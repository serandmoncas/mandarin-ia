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


R = {"妈": {"ma1", "ma5"}, "我": {"wo3"}, "吃": {"chi1"}, "得": {"de2", "de5", "dei3"},
     "快": {"kuai4"}, "活": {"huo2"}, "儿": {"er2"}, "女": {"nv3"}, "有": {"you3"},
     "个": {"ge4", "ge5"}, "一": {"yi1", "yi2", "yi4"}, "不": {"bu4", "bu2"}, "天": {"tian1"},
     "好": {"hao3", "hao4"}}


def test_validate_accepts_neutral_tone():
    s = validate_numbered("妈妈", "ma1 ma5", R)
    assert [(x.pinyin, x.tone) for x in s] == [("mā", 1), ("ma", 5)]


def test_validate_accepts_contextual_reading():
    assert [x.pinyin for x in validate_numbered("吃得快", "chi1 de5 kuai4", R)] == ["chī", "de", "kuài"]


def test_validate_rejects_wrong_tone():
    assert validate_numbered("妈妈", "ma3 ma3", R) is None
    assert validate_numbered("妈妈", "ma1 ma5", R) is not None


def test_validate_normalizes_yi_bu_to_dictionary_tone():
    assert [x.tone for x in validate_numbered("一不", "yi2 bu2", R)] == [1, 4]


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
    assert {"ma1", "ma5"} <= r["妈"] and {"de2", "de5", "dei3"} <= r["得"]


def test_sentence_pinyin_sandhi_decides_yi_bu_over_proposal():
    for zh, proposed, expected in [
        ("一天", "yi2 tian1", "yì tiān"),
        ("不好", "bu2 hao3", "bù hǎo"),
        ("一个", "yi2 ge4", "yí gè"),
    ]:
        text, _, fell_back = sentence_pinyin(zh, proposed, R)
        assert (text, fell_back) == (expected, False)


def test_sentence_pinyin_joins_erhua_in_text_only():
    text, syllables, fell_back = sentence_pinyin("那儿", "na4 r5", {**R, "那": {"na4"}})
    assert text == "nàr"
    assert len(syllables) == 2
    assert not fell_back
