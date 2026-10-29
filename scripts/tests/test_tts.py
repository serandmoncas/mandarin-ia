import json

import httpx
import pytest

from mandarin_pipeline.audio_keys import SENTENCE_VOICE, WORD_VOICES
from mandarin_pipeline.tts import (
    EmptyAudio,
    MissingConfig,
    QuotaExhausted,
    Throttled,
    audio_key,
    build_ssml,
    jobs_from_dictionary,
    load_config,
    synthesize,
)

V = "zh-CN-XiaoxiaoNeural"


def _jobs(n):
    return [(f"t{i}", V) for i in range(n)]


class FakeClock:
    """Monotonic clock whose sleep() just advances time and records the delay."""

    def __init__(self):
        self.t = 0.0
        self.sleeps: list[float] = []

    def now(self) -> float:
        return self.t

    def sleep(self, s: float) -> None:
        self.sleeps.append(s)
        self.t += s


def run_audio(jobs, mp, synth, upload, clock=None, **kw):
    """run_audio with a fake clock so tests never really sleep."""
    from mandarin_pipeline.tts import run_audio as real

    clock = clock or FakeClock()
    return real(jobs, mp, synth, upload, clock=clock.now, sleep=clock.sleep, **kw)


def test_audio_key_stable():
    assert audio_key("你好", V) == audio_key("你好", V)
    assert audio_key("你好", V) != audio_key("你好", "zh-CN-YunxiNeural")
    assert audio_key("你好", V).endswith(".mp3")


def test_skips_jobs_in_manifest(tmp_path):
    mp = tmp_path / "m.json"
    k0 = audio_key("t0", V)
    mp.write_text(json.dumps({k0: k0}), encoding="utf-8")
    calls = []
    report = run_audio(_jobs(2), mp, lambda t, v: calls.append(t) or b"x", lambda p, d: None)
    assert calls == ["t1"]
    assert (report.done, report.skipped, report.quota_exhausted) == (1, 1, False)


def test_quota_429_stops_and_saves_manifest(tmp_path):
    mp = tmp_path / "m.json"

    def synth(t, v):
        if t == "t2":
            raise QuotaExhausted()
        return b"x"

    report = run_audio(_jobs(5), mp, synth, lambda p, d: None)
    assert report.quota_exhausted is True
    assert set(json.loads(mp.read_text(encoding="utf-8"))) == {audio_key("t0", V), audio_key("t1", V)}
    calls = []
    run_audio(_jobs(2), mp, lambda t, v: calls.append(t) or b"x", lambda p, d: None)
    assert calls == []


def test_manifest_saved_every_job(tmp_path):
    mp = tmp_path / "m.json"
    sizes = []

    def upload(path, data):
        sizes.append(len(json.loads(mp.read_text(encoding="utf-8"))) if mp.exists() else 0)

    run_audio(_jobs(3), mp, lambda t, v: b"x", upload)
    assert sizes == [0, 1, 2]
    assert len(json.loads(mp.read_text(encoding="utf-8"))) == 3


def test_limit_caps_new_jobs(tmp_path):
    report = run_audio(_jobs(5), tmp_path / "m.json", lambda t, v: b"x", lambda p, d: None, limit=2)
    assert report.done == 2


def test_jobs_only_visible_and_deduped():
    def w(sid, order, status, exs):
        return {"simplified": sid, "order": order, "status": status,
                "examples": [{"zh": e} for e in exs]}

    d = {
        "words": [
            w("B", 2, "auto_checked", ["句子", "句子"]),
            w("A", 1, "human_reviewed", ["句子"]),
            w("C", 3, "generated", ["隐藏"]),
        ],
        "phrases": [
            {"zh": "你好吗", "status": "auto_checked"},
            {"zh": "不见", "status": "generated"},
            {"zh": "句子", "status": "auto_checked"},
        ],
    }
    jobs = jobs_from_dictionary(d)
    expected = [("A", v) for v in WORD_VOICES] + [("句子", SENTENCE_VOICE)]
    expected += [("B", v) for v in WORD_VOICES] + [("你好吗", SENTENCE_VOICE)]
    assert jobs == expected


def test_missing_env_errors_before_network(tmp_path):
    with pytest.raises(MissingConfig) as e:
        load_config({"AZURE_SPEECH_KEY": "k"}, dotenv_path=tmp_path / ".env")
    assert "SUPABASE_URL" in str(e.value) and "docs/setup.md" in str(e.value)


def test_load_config_ok(tmp_path):
    env = {k: "v" for k in ("AZURE_SPEECH_KEY", "AZURE_SPEECH_REGION", "SUPABASE_URL", "SUPABASE_SERVICE_ROLE_KEY")}
    assert load_config(env, dotenv_path=tmp_path / ".env")["SUPABASE_URL"] == "v"


def test_ssml_escapes():
    s = build_ssml("a<b&c>", V)
    assert "a&lt;b&amp;c&gt;" in s and f'<voice name="{V}">' in s and 'xml:lang="zh-CN"' in s


def test_transient_429_backs_off_and_continues(tmp_path):
    clock = FakeClock()
    calls = []

    def synth(t, v):
        calls.append(t)
        if t == "t1" and calls.count("t1") == 1:
            raise Throttled(retry_after=7)
        return b"x"

    report = run_audio(_jobs(3), tmp_path / "m.json", synth, lambda p, d: None, clock=clock)
    assert (report.done, report.quota_exhausted) == (3, False)
    assert calls == ["t0", "t1", "t1", "t2"]
    assert 7 in clock.sleeps


def test_429_without_retry_after_waits_60s(tmp_path):
    clock = FakeClock()
    seen = []

    def synth(t, v):
        seen.append(t)
        if len(seen) == 1:
            raise Throttled()
        return b"x"

    run_audio(_jobs(1), tmp_path / "m.json", synth, lambda p, d: None, clock=clock)
    assert 60 in clock.sleeps


def test_persistent_429_reports_quota_after_retries(tmp_path):
    mp = tmp_path / "m.json"
    calls = []

    def synth(t, v):
        calls.append(t)
        if t == "t1":
            raise Throttled(retry_after=1)
        return b"x"

    report = run_audio(_jobs(3), mp, synth, lambda p, d: None)
    assert report.quota_exhausted is True and report.done == 1
    assert calls.count("t1") == 4  # first try + 3 retries after backoff
    assert "t2" not in calls
    assert set(json.loads(mp.read_text(encoding="utf-8"))) == {audio_key("t0", V)}


def test_pacing_at_most_18_requests_per_minute(tmp_path):
    clock = FakeClock()
    times = []

    def synth(t, v):
        times.append(clock.now())
        return b"x"

    run_audio(_jobs(40), tmp_path / "m.json", synth, lambda p, d: None, clock=clock)
    assert len(times) == 40
    for i in range(len(times) - 18):
        assert times[i + 18] - times[i] >= 60 - 1e-9


def test_synthesize_429_carries_retry_after():
    c = httpx.Client(transport=httpx.MockTransport(lambda r: httpx.Response(429, headers={"Retry-After": "7"})))
    with pytest.raises(Throttled) as e:
        synthesize("x", V, "KEY", "eastus", c)
    assert e.value.retry_after == 7
    c = httpx.Client(transport=httpx.MockTransport(lambda r: httpx.Response(429)))
    with pytest.raises(Throttled) as e:
        synthesize("x", V, "KEY", "eastus", c)
    assert e.value.retry_after is None


def test_synthesize_rejects_empty_audio():
    c = httpx.Client(transport=httpx.MockTransport(lambda r: httpx.Response(200, content=b"")))
    with pytest.raises(EmptyAudio):
        synthesize("x", V, "KEY", "eastus", c)


def test_synthesize_ok_and_429():
    seen = {}

    def handler(req: httpx.Request):
        seen["url"] = str(req.url)
        seen["h"] = req.headers
        return httpx.Response(429 if req.content.find(b"quota") >= 0 else 200, content=b"MP3")

    c = httpx.Client(transport=httpx.MockTransport(handler))
    assert synthesize("你好", V, "KEY", "eastus", c) == b"MP3"
    assert seen["url"] == "https://eastus.tts.speech.microsoft.com/cognitiveservices/v1"
    assert seen["h"]["Ocp-Apim-Subscription-Key"] == "KEY"
    assert seen["h"]["X-Microsoft-OutputFormat"] == "audio-24khz-48kbitrate-mono-mp3"
    with pytest.raises(Throttled):
        synthesize("quota", V, "KEY", "eastus", c)


def test_synthesize_other_error_raises():
    c = httpx.Client(transport=httpx.MockTransport(lambda r: httpx.Response(500)))
    with pytest.raises(httpx.HTTPStatusError):
        synthesize("x", V, "KEY", "eastus", c)
