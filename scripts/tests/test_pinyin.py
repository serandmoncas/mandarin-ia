import pytest

from mandarin_pipeline.pinyin import numbered_to_marked, sentence_pinyin, syllables_for


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
    text, syl = sentence_pinyin("你好，我是Sergio。")
    assert [s.hanzi for s in syl[:2]] == ["你", "好"]
    assert text.startswith("nǐ hǎo")
    assert all(s.hanzi not in "，。" for s in syl)
    assert syl[0].tone == 3
