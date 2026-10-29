import json

import httpx
import pytest

from mandarin_pipeline.audio_keys import SENTENCE_VOICE, WORD_VOICES
from mandarin_pipeline.tts import (
    MissingConfig,
    QuotaExhausted,
    audio_key,
    build_ssml,
    jobs_from_dictionary,
    load_config,
    run_audio,
    synthesize,
)

V = "zh-CN-XiaoxiaoNeural"


def _jobs(n):
    return [(f"t{i}", V) for i in range(n)]


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
    with pytest.raises(QuotaExhausted):
        synthesize("quota", V, "KEY", "eastus", c)


def test_synthesize_other_error_raises():
    c = httpx.Client(transport=httpx.MockTransport(lambda r: httpx.Response(500)))
    with pytest.raises(httpx.HTTPStatusError):
        synthesize("x", V, "KEY", "eastus", c)
