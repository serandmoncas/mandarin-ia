from mandarin_pipeline.cedict import CedictEntry
from mandarin_pipeline.checks import (
    apply_review,
    check_char,
    check_phrase,
    check_word,
    known_before_ratio,
)
from mandarin_pipeline.models import (
    CharContent,
    Component,
    GeneratedExample,
    PhraseContent,
    WordContent,
)


def word(w, idx=0, meanings=("sentido",), examples=None):
    examples = examples if examples is not None else [
        GeneratedExample(zh=f"{p}{w}你", es="x") for p in ("我", "他", "她", "们")
    ]
    return WordContent(
        word=w, cedict_reading_index=idx, meanings_es=list(meanings), examples=examples
    )


ENTRIES_XING = [
    CedictEntry("行", "行", "xing2", ["to walk"]),
    CedictEntry("行", "行", "hang2", ["row"]),
]


def test_polyphonic_reading_selected():
    r = check_word(word("行", 1), ENTRIES_XING, set())
    assert r.reading.pinyin_numbered == "hang2"
    assert r.flags == []


def test_reading_index_out_of_range_flags():
    r = check_word(word("行", 7), ENTRIES_XING, set())
    assert r.reading is None
    assert "reading_index_out_of_range" in r.flags


def test_citation_tone_for_bu():
    ex = [GeneratedExample(zh="我不是", es="x")] * 4
    entries = [CedictEntry("不", "不", "bu4", ["not"])]
    r = check_word(word("不", examples=ex), entries, set())
    assert r.reading.pinyin_numbered == "bu4"
    assert r.syllables[0].tone == 4


def test_drops_examples_without_target():
    ex = [GeneratedExample(zh="我喜欢你", es="x"), GeneratedExample(zh="他喜欢你", es="x")]
    ex += [GeneratedExample(zh="他走了", es="y")] * 2
    r = check_word(word("喜欢", examples=ex), [CedictEntry("喜歡", "喜欢", "xi3 huan5", ["like"])], set())
    assert len(r.examples) == 2
    assert all("喜欢" in e.zh for e in r.examples)


def test_drops_long_examples():
    long_zh = "我" * 21 + "好"
    ex = [GeneratedExample(zh=long_zh, es="x")] * 2
    ex += [GeneratedExample(zh="我好", es="y"), GeneratedExample(zh="他好", es="y")]
    r = check_word(word("好", examples=ex), [CedictEntry("好", "好", "hao3", ["good"])], set())
    assert [e.zh for e in r.examples] == ["我好", "他好"]


def test_too_few_examples_flag():
    ex = [GeneratedExample(zh="我好", es="y")] + [GeneratedExample(zh="他走", es="z")] * 3
    r = check_word(word("好", examples=ex), [CedictEntry("好", "好", "hao3", ["good"])], set())
    assert "too_few_examples" in r.flags


def test_syllable_mismatch_flag():
    entries = [CedictEntry("你好", "你好", "ni3", ["hello"])]
    ex = [GeneratedExample(zh="你好吗", es="x")] * 4
    r = check_word(word("你好", examples=ex), entries, set())
    assert "syllable_mismatch" in r.flags


def test_empty_meaning_flag():
    r = check_word(word("好", meanings=("bien", " ")), [CedictEntry("好", "好", "hao3", ["g"])], set())
    assert "empty_meaning" in r.flags


def test_known_before_ratio():
    assert known_before_ratio("我喜欢你", "喜欢", {"我"}) == 2 / 3


def test_apply_review_statuses():
    assert apply_review([], True, []) == ("auto_checked", [])
    status, flags = apply_review([], False, ["poco natural"])
    assert status == "generated" and flags == ["review:poco natural"]
    status, flags = apply_review(["empty_meaning"], True, [])
    assert status == "generated" and flags == ["empty_meaning"]


def test_check_char():
    ok = CharContent(char="好", components=[Component(char="女", meaning_es="mujer")], mnemonic_es="x")
    assert check_char(ok) == []
    bad = CharContent(char="好", components=[Component(char="女", meaning_es=" ")], mnemonic_es="")
    assert set(check_char(bad)) == {"empty_mnemonic", "empty_component_meaning"}


def test_check_phrase():
    zh, syl, flags = check_phrase(PhraseContent(mission="hotel", zh="你好", es="hola"))
    assert zh == "nǐ hǎo" and len(syl) == 2 and flags == []
    _, _, flags = check_phrase(PhraseContent(mission="hotel", zh="我" * 21, es=""))
    assert set(flags) == {"empty_translation", "too_long"}


def test_build_review_items_only_unflagged(tmp_path):
    import json

    from mandarin_pipeline.checks import build_review_items

    good = {"word": "好", "cedict_reading_index": 0, "meanings_es": ["bien"],
            "examples": [{"zh": z, "es": "bien"} for z in ("我很好", "他很好", "好的", "你好吗")]}
    bad = {**good, "word": "坏", "examples": [{"zh": "我很好", "es": "x"}] * 4}
    (tmp_path / "words").mkdir()
    (tmp_path / "words" / "batch_000.json").write_text(json.dumps([good, bad]), encoding="utf-8")
    (tmp_path / "phrases").mkdir()
    (tmp_path / "phrases" / "batch_000.json").write_text(
        json.dumps([{"mission": "hotel", "zh": "你好", "es": "hola"},
                    {"mission": "hotel", "zh": "再见", "es": ""}]), encoding="utf-8")
    cedict = {"好": [CedictEntry("好", "好", "hao3", ["good"])], "坏": [CedictEntry("壞", "坏", "huai4", ["bad"])]}
    cands = [{"word": "好", "order": 1}, {"word": "坏", "order": 2}]
    ids = [i["id"] for i in build_review_items(tmp_path, cedict, cands)]
    assert ids == ["word:好", "phrase:hotel:000"]


def test_apply_review_not_ok_without_issues_is_flagged():
    status, flags = apply_review([], False, [])
    assert status == "generated" and flags == ["review:not_ok"]


def test_drops_examples_with_empty_translation():
    ex = [GeneratedExample(zh="我好", es=" ")] + [GeneratedExample(zh=f"他好{i}", es="y") for i in range(3)]
    r = check_word(word("好", examples=ex), [CedictEntry("好", "好", "hao3", ["good"])], set())
    assert [e.zh for e in r.examples] == ["他好0", "他好1", "他好2"]


def test_dedupes_meanings_and_examples():
    ex = [GeneratedExample(zh="我好", es="y")] * 2 + [GeneratedExample(zh="他好", es="z")] * 2
    r = check_word(
        word("好", meanings=("bien", " bien", "bueno"), examples=ex),
        [CedictEntry("好", "好", "hao3", ["good"])],
        set(),
    )
    assert r.content.meanings_es == ["bien", "bueno"]
    assert [e.zh for e in r.examples] == ["我好", "他好"]
