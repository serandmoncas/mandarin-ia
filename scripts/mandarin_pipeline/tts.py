"""Azure TTS synthesis + Supabase Storage upload, resumable, paced and quota-safe."""
import json
import os
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Callable, Mapping
from xml.sax.saxutils import escape

import httpx
from dotenv import dotenv_values

from mandarin_pipeline.audio_keys import SENTENCE_VOICE, WORD_VOICES, audio_key
from mandarin_pipeline.build import load_manifest

__all__ = ["audio_key", "QuotaExhausted", "Throttled", "EmptyAudio", "MissingConfig", "AudioReport"]

# Supabase Storage is reached over its S3 protocol with storage-only access keys, so the
# pipeline never holds a key that can touch the database (see docs/setup.md).
REQUIRED_ENV = (
    "AZURE_SPEECH_KEY",
    "AZURE_SPEECH_REGION",
    "SUPABASE_S3_ENDPOINT",
    "SUPABASE_S3_REGION",
    "SUPABASE_S3_ACCESS_KEY_ID",
    "SUPABASE_S3_SECRET_ACCESS_KEY",
)
AUDIO_BUCKET = "audio"
VISIBLE = ("auto_checked", "human_reviewed")

# Azure F0 throttles at ~20 transactions per 60 s; stay below it.
MAX_REQUESTS_PER_MINUTE = 18
# Retries of one job after a 429 (each after backing off) before giving up the run.
THROTTLE_RETRIES = 3
DEFAULT_BACKOFF_S = 60.0


class QuotaExhausted(Exception):
    """Azure keeps answering 429: monthly F0 quota used up or sustained throttling."""


class Throttled(Exception):
    """One HTTP 429 from Azure; retry_after is the Retry-After delay in seconds, if given."""

    def __init__(self, retry_after: float | None = None):
        super().__init__(f"HTTP 429 (Retry-After: {retry_after})")
        self.retry_after = retry_after


class EmptyAudio(Exception):
    """Azure answered 200 with an empty body."""


class MissingConfig(Exception):
    pass


@dataclass
class AudioReport:
    done: int = 0
    skipped: int = 0
    quota_exhausted: bool = False


def load_config(environ: Mapping[str, str] | None = None, dotenv_path: Path | None = None) -> dict[str, str]:
    """Merge the .env file (if any) under the environment; fail before any network call."""
    values: dict[str, str] = {}
    if dotenv_path is not None and Path(dotenv_path).exists():
        values.update({k: v for k, v in dotenv_values(dotenv_path).items() if v})
    values.update({k: v for k, v in (os.environ if environ is None else environ).items() if v})
    missing = [k for k in REQUIRED_ENV if not values.get(k)]
    if missing:
        raise MissingConfig(
            f"Faltan variables de entorno: {', '.join(missing)}. "
            "Revisa docs/setup.md y completa el archivo .env."
        )
    return values


def build_ssml(text: str, voice: str) -> str:
    return (
        f'<speak version="1.0" xml:lang="zh-CN"><voice name="{voice}">'
        f"{escape(text)}</voice></speak>"
    )


def synthesize(text: str, voice: str, key: str, region: str, client: httpx.Client) -> bytes:
    resp = client.post(
        f"https://{region}.tts.speech.microsoft.com/cognitiveservices/v1",
        content=build_ssml(text, voice).encode("utf-8"),
        headers={
            "Ocp-Apim-Subscription-Key": key,
            "Content-Type": "application/ssml+xml",
            "X-Microsoft-OutputFormat": "audio-24khz-48kbitrate-mono-mp3",
            "User-Agent": "mandarin-ia",
        },
    )
    if resp.status_code == 429:
        raise Throttled(_retry_after(resp.headers.get("Retry-After")))
    resp.raise_for_status()
    if not resp.content:
        raise EmptyAudio(f"Azure devolvió audio vacío para {voice}: {text!r}")
    return resp.content


def _retry_after(value: str | None) -> float | None:
    """Retry-After in seconds; None when absent or not numeric (e.g. an HTTP date)."""
    try:
        return max(0.0, float(value)) if value is not None else None
    except ValueError:
        return None


def make_s3_client(cfg: Mapping[str, str]):
    """boto3 client for Supabase Storage's S3 endpoint (path-style, as Supabase documents)."""
    import boto3
    from botocore.config import Config

    return boto3.client(
        "s3",
        endpoint_url=cfg["SUPABASE_S3_ENDPOINT"],
        region_name=cfg["SUPABASE_S3_REGION"],
        aws_access_key_id=cfg["SUPABASE_S3_ACCESS_KEY_ID"],
        aws_secret_access_key=cfg["SUPABASE_S3_SECRET_ACCESS_KEY"],
        config=Config(s3={"addressing_style": "path"}),
    )


def upload(path: str, data: bytes, s3) -> None:
    """Puts one MP3 in the audio bucket; boto3 raises on any non-2xx answer."""
    s3.put_object(Bucket=AUDIO_BUCKET, Key=path, Body=data, ContentType="audio/mpeg")


def jobs_from_dictionary(d: dict) -> list[tuple[str, str]]:
    """(text, voice) jobs for visible entries only: words by order, their examples, then phrases."""
    jobs: list[tuple[str, str]] = []
    seen: set[tuple[str, str]] = set()

    def add(text: str, voices: tuple[str, ...]) -> None:
        for voice in voices:
            if (text, voice) not in seen:
                seen.add((text, voice))
                jobs.append((text, voice))

    for w in sorted(d["words"], key=lambda w: w["order"]):
        if w["status"] not in VISIBLE:
            continue
        add(w["simplified"], WORD_VOICES)
        for ex in w.get("examples", []):
            add(ex["zh"], (SENTENCE_VOICE,))
    for p in d.get("phrases", []):
        if p["status"] in VISIBLE:
            add(p["zh"], (SENTENCE_VOICE,))
    return jobs


def _save_manifest(manifest: dict[str, str], path: Path) -> None:
    path = Path(path)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(
        json.dumps(manifest, ensure_ascii=False, sort_keys=True, indent=2) + "\n", encoding="utf-8"
    )
    os.replace(tmp, path)


def run_audio(
    jobs: list[tuple[str, str]],
    manifest_path: Path,
    synth: Callable[[str, str], bytes],
    upload: Callable[[str, bytes], None],
    limit: int | None = None,
    clock: Callable[[], float] = time.monotonic,
    sleep: Callable[[float], None] = time.sleep,
    max_per_minute: int = MAX_REQUESTS_PER_MINUTE,
    throttle_retries: int = THROTTLE_RETRIES,
) -> AudioReport:
    """Synthesize and upload missing jobs; the manifest is saved after each one.

    Requests are spaced to at most max_per_minute. A 429 backs off (Retry-After or
    60 s) and retries the same job; after throttle_retries consecutive 429s the run
    stops cleanly with quota_exhausted. Any other error propagates, but everything
    done so far is already on disk.
    """
    manifest = load_manifest(manifest_path)
    report = AudioReport()
    interval = 60.0 / max_per_minute
    next_slot = clock()

    def paced_synth(text: str, voice: str) -> bytes:
        nonlocal next_slot
        throttles = 0
        while True:
            wait = next_slot - clock()
            if wait > 0:
                sleep(wait)
            next_slot = clock() + interval
            try:
                return synth(text, voice)
            except Throttled as e:
                throttles += 1
                if throttles > throttle_retries:
                    raise QuotaExhausted() from e
                sleep(DEFAULT_BACKOFF_S if e.retry_after is None else e.retry_after)

    for text, voice in jobs:
        key = audio_key(text, voice)
        if key in manifest:
            report.skipped += 1
            continue
        if limit is not None and report.done >= limit:
            break
        try:
            data = paced_synth(text, voice)
        except QuotaExhausted:
            report.quota_exhausted = True
            break
        upload(key, data)
        manifest[key] = key
        _save_manifest(manifest, manifest_path)
        report.done += 1
    return report
