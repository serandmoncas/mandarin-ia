import pytest

from mandarin_pipeline.cedict import parse_cedict
from mandarin_pipeline.pinyin import (
    char_readings,
    numbered_to_marked,
    sentence_pinyin,
    syllables_for,
    validate_numbered,
)


@pytest.mark.parametrize(
    "numbered,marked",
    [
        ("ni3 hao3", "nǐ hǎo"),
        ("xue2", "xué"),
        ("gou3", "gǒu"),
        ("lv4", "lǜ"),
        ("liu2", "liú"),
        ("ma5", "ma"),
    ],
)
def test_numbered_to_marked(numbered, marked):
    assert numbered_to_marked(numbered) == marked


def test_syllables_for_matches_characters():
    syl = syllables_for("你好", "ni3 hao3")
    assert [(s.hanzi, s.pinyin, s.tone) for s in syl] == [("你", "nǐ", 3), ("好", "hǎo", 3)]


def test_syllables_for_mismatch_returns_none():
    assert syllables_for("你好吗", "ni3 hao3") is None


def test_sentence_pinyin_leaves_punctuation_without_syllable():
    text, syl, _ = sentence_pinyin("你好，我是Sergio。")
    assert [s.hanzi for s in syl[:2]] == ["你", "好"]
    assert text.startswith("nǐ hǎo")
    assert all(s.hanzi not in "，。" for s in syl)
    assert syl[0].tone == 3


R = {"妈": {"ma"}, "我": {"wo"}, "吃": {"chi"}, "得": {"de", "dei"}, "快": {"kuai"},
     "活": {"huo"}, "儿": {"er"}, "女": {"nv"}, "有": {"you"}, "个": {"ge"}}


def test_validate_accepts_neutral_tone():
    s = validate_numbered("妈妈", "ma1 ma5", R)
    assert [(x.pinyin, x.tone) for x in s] == [("mā", 1), ("ma", 5)]


def test_validate_accepts_contextual_reading():
    assert [x.pinyin for x in validate_numbered("吃得快", "chi1 de5 kuai4", R)] == ["chī", "de", "kuài"]


def test_validate_rejects_unknown_base():
    assert validate_numbered("我", "ni3", R) is None


def test_validate_rejects_count_mismatch():
    assert validate_numbered("妈妈", "ma1", R) is None


def test_validate_ignores_digits_and_latin():
    assert [x.hanzi for x in validate_numbered("我有2个", "wo3 you3 ge4", R)] == ["我", "有", "个"]


def test_validate_normalizes_umlaut_and_case():
    for p in ("nü3", "nu:3", "NV3"):
        assert validate_numbered("女", p, R)[0].pinyin == "nǚ"


def test_validate_erhua():
    assert [x.pinyin for x in validate_numbered("活儿", "huo2 r5", R)] == ["huó", "r"]
    assert validate_numbered("儿", "r5", R) is None


def test_char_readings_includes_multichar_entries():
    cedict = parse_cedict(["媽媽 妈妈 [ma1 ma5] /mom/", "得 得 [de2] /to obtain/"])
    r = char_readings(cedict)
    assert "ma" in r["妈"] and {"de", "dei"} <= r["得"]
