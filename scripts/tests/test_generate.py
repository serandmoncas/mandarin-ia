import json

import pytest

from mandarin_pipeline.generate import BatchReport, run_batches, strip_code_fences
from mandarin_pipeline.models import WordContent


def _word_obj(word: str, examples: int = 4) -> dict:
    return {
        "word": word,
        "cedict_reading_index": 0,
        "meanings_es": ["significado"],
        "examples": [{"zh": f"{word}好", "es": "bien"} for _ in range(examples)],
    }


ITEMS = [{"word": f"词{i}", "order": i} for i in range(45)]


def render(batch: list[dict]) -> str:
    return "PROMPT " + ",".join(i["word"] for i in batch)


def fake_runner(calls: list[str], examples: int = 4):
    def runner(prompt: str) -> str:
        calls.append(prompt)
        words = prompt.removeprefix("PROMPT ").split(",")
        return json.dumps([_word_obj(w, examples) for w in words], ensure_ascii=False)

    return runner


def run(tmp_path, runner, items=ITEMS):
    return run_batches("words", items, render, WordContent, runner, tmp_path, batch_size=20)


def test_writes_batch_files(tmp_path):
    report = run(tmp_path, fake_runner([]))
    for n in ("000", "001", "002"):
        assert (tmp_path / f"batch_{n}.json").exists()
    assert report == BatchReport(done=3, skipped=0, failed=[])
    data = json.loads((tmp_path / "batch_002.json").read_text(encoding="utf-8"))
    assert len(data) == 5 and data[0]["cedict_reading_index"] == 0


def test_resume_skips_existing(tmp_path):
    run(tmp_path, fake_runner([]))
    calls: list[str] = []
    report = run(tmp_path, fake_runner(calls))
    assert calls == []
    assert report.skipped == 3 and report.done == 0


def test_invalid_json_retries_once_then_records_error(tmp_path):
    calls: list[str] = []

    def runner(prompt: str) -> str:
        calls.append(prompt)
        if "词0," in prompt:  # first batch only
            return "no json"
        return fake_runner([])(prompt)

    report = run(tmp_path, runner)
    assert sum("词0," in c for c in calls) == 2
    assert (tmp_path / "batch_000.error.txt").exists()
    assert not (tmp_path / "batch_000.json").exists()
    assert report.failed == [0]
    assert (tmp_path / "batch_001.json").exists() and (tmp_path / "batch_002.json").exists()


def test_schema_violation_counts_as_invalid(tmp_path):
    calls: list[str] = []
    report = run(tmp_path, fake_runner(calls, examples=3), items=ITEMS[:5])
    assert len(calls) == 2
    assert report.failed == [0]


def test_wrong_items_counts_as_invalid(tmp_path):
    calls: list[str] = []

    def runner(prompt: str) -> str:
        calls.append(prompt)
        return json.dumps([_word_obj("别的")])

    report = run(tmp_path, runner, items=ITEMS[:5])
    assert len(calls) == 2 and report.failed == [0]


def test_retry_succeeds_on_second_attempt(tmp_path):
    calls: list[str] = []

    def runner(prompt: str) -> str:
        calls.append(prompt)
        return "oops" if len(calls) == 1 else fake_runner([])(prompt)

    report = run(tmp_path, runner, items=ITEMS[:5])
    assert report == BatchReport(done=1, skipped=0, failed=[])


def test_strips_code_fences():
    assert strip_code_fences('```json\n[{"a": 1}]\n```') == '[{"a": 1}]'
    assert strip_code_fences('  [1]  ') == "[1]"
    assert json.loads(strip_code_fences("```\n[1]\n```")) == [1]


def test_fenced_response_is_parsed(tmp_path):
    def runner(prompt: str) -> str:
        words = prompt.removeprefix("PROMPT ").split(",")
        return "```json\n" + json.dumps([_word_obj(w) for w in words]) + "\n```"

    report = run(tmp_path, runner, items=ITEMS[:3])
    assert report.done == 1
