import json
from pathlib import Path

from mandarin_pipeline.audio_keys import SENTENCE_VOICE, WORD_VOICES, audio_key
from mandarin_pipeline.build import (
    build_dictionary,
    compute_stats,
    dictionary_json,
    write_dictionary,
)
from mandarin_pipeline.cedict import CedictEntry
from mandarin_pipeline.checks import check_word, review_items_from
from mandarin_pipeline.models import (
    CharContent,
    Component,
    GeneratedExample,
    PhraseContent,
    ReviewResult,
    WordContent,
)
from mandarin_pipeline.order import Candidate

ROOT = Path(__file__).resolve().parents[2]
VERSION, STAMP = "202610291200", "2026-10-29T12:00:00Z"

ENTRIES = {
    "你好": [CedictEntry("你好", "你好", "ni3 hao3", ["Hello!"])],
    "谢谢": [CedictEntry("謝謝", "谢谢", "xie4 xie5", ["to thank"])],
    "你": [CedictEntry("你", "你", "ni3", ["you"])],
}


def content(word, zhs, meanings=("saludo",)):
    return WordContent(
        word=word,
        cedict_reading_index=0,
        meanings_es=list(meanings),
        examples=[GeneratedExample(zh=z, es=f"es {i}") for i, z in enumerate(zhs)],
    )


def checked(word, zhs, known=frozenset()):
    return check_word(content(word, zhs), ENTRIES[word], set(known))


CANDS = [
    Candidate("你好", 0.01, 1, 3, 1),
    Candidate("谢谢", 0.01, 1, 2, 2),
    Candidate("你", 0.01, None, 1, 3),
    Candidate("再见", 0.01, 1, 9, 4),  # no generated content
]


def make_inputs():
    words = {
        "你好": checked("你好", ["你好吗", "你好，朋友", "我说你好", "他说你好"]),
        "谢谢": checked("谢谢", ["谢谢你", "谢谢大家", "谢谢老师", "谢谢你们"], {"你"}),
        # only 1 valid example -> automatic flag too_few_examples
        "你": checked("你", ["你好", "他们", "我们", "大家"]),
    }
    chars = [
        CharContent(char="你", components=[Component(char="亻", meaning_es="persona")], mnemonic_es="Una persona."),
        CharContent(char="好", components=[Component(char="女", meaning_es="mujer"), Component(char="子", meaning_es="hijo")], mnemonic_es="Mujer con hijo."),
    ]
    phrases = [
        PhraseContent(mission="introductions", zh="你好，我叫小明。", es="Hola, me llamo Xiaoming."),
        PhraseContent(mission="restaurant", zh="请给我菜单。", es="Deme el menú, por favor."),
    ]
    reviewed = {"word:你好", "word:谢谢", "char:你", "phrase:introductions:000"}
    reviews = [
        ReviewResult(id=i["id"], ok=True, content_hash=i["content_hash"])
        for i in review_items_from(words, chars, phrases)
        if i["id"] in reviewed
    ]
    manifest = {
        audio_key("你好", WORD_VOICES[0]): audio_key("你好", WORD_VOICES[0]),
        audio_key("你好", WORD_VOICES[1]): audio_key("你好", WORD_VOICES[1]),
        audio_key("你好吗", SENTENCE_VOICE): audio_key("你好吗", SENTENCE_VOICE),
        audio_key("你好，我叫小明。", SENTENCE_VOICE): audio_key("你好，我叫小明。", SENTENCE_VOICE),
    }
    return words, reviews, chars, phrases, manifest


def build(manifest=None):
    words, reviews, chars, phrases, m = make_inputs()
    return build_dictionary(
        CANDS, words, reviews, chars, phrases, m if manifest is None else manifest, VERSION, STAMP
    )


def test_build_matches_contract():
    data = json.loads(dictionary_json(build()))
    assert set(data) == {"version", "generatedAt", "words", "characters", "phrases", "credits"}
    assert data["version"] == VERSION and data["generatedAt"] == STAMP
    w = data["words"][0]
    assert set(w) == {
        "id", "simplified", "traditional", "pinyin", "pinyinNumbered", "syllables", "meaningsEs",
        "hskLevel", "freqRank", "order", "audio", "examples", "status", "flags",
    }
    assert w["id"] == w["simplified"] == "你好"
    assert w["pinyin"] == "nǐ hǎo" and w["pinyinNumbered"] == "ni3 hao3"
    assert set(w["examples"][0]) == {"zh", "pinyin", "syllables", "es", "knownBeforeRatio", "audio"}
    assert set(w["syllables"][0]) == {"hanzi", "pinyin", "tone"}
    assert set(data["characters"]["你"]) == {"char", "components", "mnemonicEs", "status", "flags"}
    assert set(data["characters"]["你"]["components"][0]) == {"char", "meaningEs"}
    assert set(data["phrases"][0]) == {"id", "mission", "zh", "pinyin", "syllables", "es", "audio", "status", "flags"}
    assert data["phrases"][0]["id"] == "phrase:introductions:000"
    assert set(data["credits"][0]) == {"name", "license", "url"}
    assert [x["name"] for x in data["credits"]][0] == "CC-CEDICT"
    assert [x["id"] for x in data["words"]] == ["你好", "谢谢", "你"]  # sorted by order
    assert data["words"][1]["traditional"] == "謝謝"


def test_status_and_not_reviewed_flag():
    d = build()
    by_id = {w.id: w for w in d.words}
    assert by_id["你好"].status == "auto_checked" and by_id["你好"].flags == []
    assert by_id["你"].status == "generated"
    assert "too_few_examples" in by_id["你"].flags and "not_reviewed" in by_id["你"].flags
    assert d.characters["好"].status == "generated" and "not_reviewed" in d.characters["好"].flags
    assert d.phrases[1].status == "generated" and "not_reviewed" in d.phrases[1].flags


def test_missing_generation_is_absent():
    d = build()
    assert "再见" not in {w.id for w in d.words}
    stats = compute_stats(CANDS, d)
    assert stats["words"]["missing"] == 1
    assert stats["words"]["auto_checked"] == 2 and stats["words"]["generated"] == 1
    assert stats["flags"]["too_few_examples"] == 1
    assert stats["hsk"] == {"1": 2, "none": 1}


def test_audio_paths_from_manifest():
    d = build({audio_key("你好", WORD_VOICES[0]): "custom/path.mp3"})
    nihao = d.words[0]
    assert [(a.voice, a.path) for a in nihao.audio] == [(WORD_VOICES[0], "custom/path.mp3")]
    assert all(e.audio is None for e in nihao.examples)
    assert d.phrases[0].audio is None
    assert build({}).words[0].audio == []


def test_audio_refs_for_examples_and_phrases():
    d = build()
    assert [a.voice for a in d.words[0].audio] == list(WORD_VOICES[:2])
    assert d.words[0].examples[0].audio.voice == SENTENCE_VOICE
    assert d.words[0].examples[1].audio is None
    assert d.phrases[0].audio.voice == SENTENCE_VOICE and d.phrases[1].audio is None


def test_writes_sample_fixture():
    out = ROOT / "data" / "fixtures" / "dictionary.sample.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    d = build()
    write_dictionary(d, out)
    data = json.loads(out.read_text(encoding="utf-8"))
    assert len(data["words"]) == 3 and len(data["characters"]) == 2 and len(data["phrases"]) == 2
    assert any(w["status"] == "generated" and w["flags"] for w in data["words"])
