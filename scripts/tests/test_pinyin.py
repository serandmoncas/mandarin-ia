import pytest

from mandarin_pipeline.cedict import parse_cedict
from mandarin_pipeline.pinyin import (
    apply_word_neutral_tones,
    char_readings,
    numbered_to_marked,
    sentence_pinyin,
    syllables_for,
    validate_numbered,
    word_readings,
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


def test_sentence_pinyin_keeps_neutral_yi_bu():
    readings = {**R, "对": {"dui4"}, "起": {"qi3"}, "看": {"kan4"}}
    for zh, proposed, expected in [
        ("对不起", "dui4 bu5 qi3", "duì bu qǐ"),
        ("看一看", "kan4 yi5 kan4", "kàn yi kàn"),
    ]:
        text, _, fell_back = sentence_pinyin(zh, proposed, readings)
        assert (text, fell_back) == (expected, False)


def test_validate_rejects_proposal_without_tone_digits():
    assert validate_numbered("我好", "wo hao", R) is None
    assert validate_numbered("我", "wo", R) is None


def test_sentence_pinyin_joins_erhua_in_text_only():
    text, syllables, fell_back = sentence_pinyin("那儿", "na4 r5", {**R, "那": {"na4"}})
    assert text == "nàr"
    assert len(syllables) == 2
    assert not fell_back


_NEUTRAL_CEDICT = parse_cedict(
    [
        "對不起 对不起 [dui4 bu5 qi3] /sorry/",
        "找不到 找不到 [zhao3 bu5 dao4] /cannot find/",
        "喜歡 喜欢 [xi3 huan5] /to like/",
        "東西 东西 [dong1 xi1] /east and west/",
        "東西 东西 [dong1 xi5] /thing/",
    ]
)
W = word_readings(_NEUTRAL_CEDICT)


def test_word_readings_normalizes_and_keeps_all_readings():
    assert W["对不起"] == [[("dui", 4), ("bu", 5), ("qi", 3)]]
    assert W["东西"] == [[("dong", 1), ("xi", 1)], [("dong", 1), ("xi", 5)]]


def test_word_readings_skips_single_chars_and_mismatched_counts():
    cedict = parse_cedict(["好 好 [hao3] /good/", "二百五 二百五 [er4 bai3] /x/"])
    assert word_readings(cedict) == {}


def test_neutral_tone_pypinyin_path():
    text, _, _ = sentence_pinyin("对不起，我来晚了。", words=W)
    assert text.startswith("duì bu qǐ")
    assert "zhǎo bu dào" in sentence_pinyin("我找不到。", words=W)[0]
    assert "xǐ huan" in sentence_pinyin("我喜欢你", words=W)[0]


def test_neutral_tone_proposal_path():
    readings = char_readings(_NEUTRAL_CEDICT)
    text, _, fell_back = sentence_pinyin("对不起", "dui4 bu4 qi3", readings, words=W)
    assert text == "duì bu qǐ" and not fell_back


def test_neutral_tone_without_words_is_unchanged():
    assert sentence_pinyin("对不起")[0] == "duì bù qǐ"


def test_neutral_tone_disagreeing_readings_leave_tone_alone():
    syl = sentence_pinyin("东西")[1]
    out = apply_word_neutral_tones(syl, W)
    assert [(s.pinyin, s.tone) for s in out] == [(s.pinyin, s.tone) for s in syl]


def test_neutral_tone_only_changes_neutral_positions_and_does_not_mutate():
    syl = sentence_pinyin("对不起")[1]
    before = [(s.pinyin, s.tone) for s in syl]
    out = apply_word_neutral_tones(syl, W)
    assert [s.pinyin for s in out] == ["duì", "bu", "qǐ"]
    assert [(s.pinyin, s.tone) for s in syl] == before


def test_neutral_tone_requires_matching_base():
    # proposal reads 喜欢 with a different base for 欢: CEDICT neutral must not overwrite it
    syl = syllables_for("喜欢", "xi3 hun2")
    out = apply_word_neutral_tones(syl, W)
    assert [s.pinyin for s in out] == ["xǐ", "hún"]


def test_sandhi_still_applies_with_words():
    assert sentence_pinyin("一样", words=W)[0] == "yí yàng"
    assert sentence_pinyin("不是", words=W)[0] == "bú shì"


_BOUNDARY_CEDICT = parse_cedict(
    [
        "做作 做作 [zuo4 zuo5] /affected/",
        "作業 作业 [zuo4 ye4] /homework/",
        "這不 这不 [zhe4 bu5] /(coll.) as a matter of fact/",
        "不是 不是 [bu4 shi4] /is not/",
        "不是 不是 [bu4 shi5] /fault/",
        "晚上 晚上 [wan3 shang5] /evening/",
        "可不 可不 [ke3 bu5] /see 可不是/",
    ]
)
WB = word_readings(_BOUNDARY_CEDICT)


def test_neutral_tone_does_not_match_across_word_boundaries():
    assert "zuò zuò yè" in sentence_pinyin("我们一起做作业吧。", words=WB)[0]
    assert sentence_pinyin("这不是我的。", words=WB)[0].startswith("zhè bú shì")
    assert "kě bù xiǎo" in sentence_pinyin("这个问题可不小。", words=WB)[0]


def test_neutral_tone_matches_word_inside_longer_token():
    # jieba keeps 每天晚上 as one token; 晚上 inside it still gets its neutral tone
    assert "wǎn shang" in sentence_pinyin("我爸爸每天晚上都看电视。", words=WB)[0]


def test_word_readings_skips_unreliable_neutral_sources():
    cedict = parse_cedict(["大人 大人 [da4 ren5] /adult/", "那是 那是 [na4 shi5] /(coll.) of course/"])
    assert word_readings(cedict) == {}
