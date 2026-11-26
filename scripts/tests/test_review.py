"""Review results are bound to the exact content that was reviewed (id + content hash)."""
import hashlib
import json

from mandarin_pipeline.build import build_dictionary
from mandarin_pipeline.cedict import CedictEntry
from mandarin_pipeline.checks import check_word, review_items_from
from mandarin_pipeline.generate import load_reviews, run_review
from mandarin_pipeline.models import (
    CharContent,
    Component,
    GeneratedExample,
    PhraseContent,
    ReviewResult,
    WordContent,
)
from mandarin_pipeline.order import Candidate

ENTRY = [CedictEntry("好", "好", "hao3", ["good"])]
CANDS = [Candidate("好", 0.01, 1, 1, 1)]


def _word(meaning="bien"):
    wc = WordContent(
        word="好",
        cedict_reading_index=0,
        meanings_es=[meaning],
        examples=[GeneratedExample(zh=z, es="bien") for z in ("我很好", "你好吗", "好的", "他很好")],
    )
    return {"好": check_word(wc, ENTRY, set())}


CHARS = [CharContent(char="好", components=[Component(char="女", meaning_es="mujer")], mnemonic_es="Mujer.")]


def _phrases(zh="你好。"):
    return [PhraseContent(mission="hotel", zh=zh, es="Hola.")]


def _items(meaning="bien", zh="你好。"):
    return review_items_from(_word(meaning), CHARS, _phrases(zh))


def _ok_runner(calls):
    def runner(prompt: str) -> str:
        calls.append(prompt)
        ids = [line[1:-1] for line in prompt.splitlines() if line.startswith("[") and line.endswith("]")]
        return json.dumps([{"id": i, "ok": True, "issues": [], "contentHash": "bogus"} for i in ids])

    return runner


def _render(batch):
    return "\n".join(f"[{i['id']}]\n{i['text']}" for i in batch)


def test_items_carry_hash_of_exact_text():
    items = _items()
    assert [i["id"] for i in items] == ["word:好", "char:好", "phrase:hotel:000"]
    for i in items:
        assert i["content_hash"] == hashlib.sha1(i["text"].encode("utf-8")).hexdigest()


def test_pipeline_attaches_hash_not_the_model(tmp_path):
    items = _items()
    run_review(items, _render, _ok_runner([]), tmp_path)
    stored = load_reviews(tmp_path)
    assert {(r.id, r.content_hash) for r in stored} == {(i["id"], i["content_hash"]) for i in items}


def test_unchanged_items_are_not_resent_and_changed_go_to_new_batch(tmp_path):
    run_review(_items(), _render, _ok_runner([]), tmp_path)
    first = (tmp_path / "batch_000.json").read_text(encoding="utf-8")

    calls: list[str] = []
    report = run_review(_items(), _render, _ok_runner(calls), tmp_path)
    assert calls == [] and report.done == 0 and report.failed == []

    report = run_review(_items(zh="再见。"), _render, _ok_runner(calls), tmp_path)
    assert len(calls) == 1 and "[phrase:hotel:000]" in calls[0] and "[word:好]" not in calls[0]
    assert report.done == 1
    assert (tmp_path / "batch_000.json").read_text(encoding="utf-8") == first  # append-only
    assert [r["id"] for r in json.loads((tmp_path / "batch_001.json").read_text(encoding="utf-8"))] == [
        "phrase:hotel:000"
    ]


def test_review_limit_applies_to_pending_items(tmp_path):
    calls: list[str] = []
    report = run_review(_items(), _render, _ok_runner(calls), tmp_path, limit=1)
    assert report.done == 1 and "[word:好]" in calls[0] and "[char:好]" not in calls[0]


def _build(words, phrases, reviews):
    return build_dictionary(CANDS, words, reviews, CHARS, phrases, {}, "v", "t")


def test_regenerated_phrase_with_same_id_is_not_reviewed():
    old = _items()
    reviews = [ReviewResult(id=i["id"], ok=True, content_hash=i["content_hash"]) for i in old]
    d = _build(_word(), _phrases("再见。"), reviews)
    assert d.phrases[0].id == "phrase:hotel:000"
    assert d.phrases[0].status == "generated" and "not_reviewed" in d.phrases[0].flags
    # unchanged items keep their review
    assert d.words[0].status == "auto_checked"
    assert d.characters["好"].status == "auto_checked"


def test_regenerated_word_meaning_is_not_reviewed():
    reviews = [ReviewResult(id=i["id"], ok=True, content_hash=i["content_hash"]) for i in _items()]
    d = _build(_word("bueno"), _phrases(), reviews)
    assert d.words[0].status == "generated" and "not_reviewed" in d.words[0].flags
    assert d.phrases[0].status == "auto_checked"


def test_review_without_hash_is_ignored():
    d = _build(_word(), _phrases(), [ReviewResult(id="word:好", ok=True)])
    assert d.words[0].status == "generated" and d.words[0].flags == ["not_reviewed"]


def test_latest_matching_review_wins():
    item = _items()[0]
    reviews = [
        ReviewResult(id=item["id"], ok=True, content_hash=item["content_hash"]),
        ReviewResult(id=item["id"], ok=False, issues=["raro"], content_hash=item["content_hash"]),
    ]
    d = _build(_word(), _phrases(), reviews)
    assert d.words[0].status == "generated" and d.words[0].flags == ["review:raro"]
