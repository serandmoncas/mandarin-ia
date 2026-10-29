"""Azure TTS synthesis + Supabase Storage upload, resumable and quota-safe."""
import json
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Callable, Mapping
from xml.sax.saxutils import escape

import httpx
from dotenv import dotenv_values

from mandarin_pipeline.audio_keys import SENTENCE_VOICE, WORD_VOICES, audio_key
from mandarin_pipeline.build import load_manifest

__all__ = ["audio_key", "QuotaExhausted", "MissingConfig", "AudioReport"]

REQUIRED_ENV = ("AZURE_SPEECH_KEY", "AZURE_SPEECH_REGION", "SUPABASE_URL", "SUPABASE_SERVICE_ROLE_KEY")
VISIBLE = ("auto_checked", "human_reviewed")


class QuotaExhausted(Exception):
    """Azure answered HTTP 429: the free-tier quota is used up."""


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
        raise QuotaExhausted()
    resp.raise_for_status()
    return resp.content


def upload(path: str, data: bytes, supabase_url: str, service_key: str, client: httpx.Client) -> None:
    resp = client.post(
        f"{supabase_url.rstrip('/')}/storage/v1/object/audio/{path}",
        content=data,
        headers={
            "Authorization": f"Bearer {service_key}",
            "apikey": service_key,
            "Content-Type": "audio/mpeg",
            "x-upsert": "true",
        },
    )
    resp.raise_for_status()


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
) -> AudioReport:
    """Synthesize and upload missing jobs; the manifest is saved after each one.

    Stops cleanly on QuotaExhausted. Any other error propagates, but everything
    done so far is already on disk.
    """
    manifest = load_manifest(manifest_path)
    report = AudioReport()
    for text, voice in jobs:
        key = audio_key(text, voice)
        if key in manifest:
            report.skipped += 1
            continue
        if limit is not None and report.done >= limit:
            break
        try:
            data = synth(text, voice)
        except QuotaExhausted:
            report.quota_exhausted = True
            break
        upload(key, data)
        manifest[key] = key
        _save_manifest(manifest, manifest_path)
        report.done += 1
    return report
