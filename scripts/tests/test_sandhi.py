import pytest

from mandarin_pipeline.pinyin import syllables_for
from mandarin_pipeline.sandhi import apply_yi_bu_sandhi


def spoken(hanzi: str, numbered: str) -> str:
    return " ".join(s.pinyin for s in apply_yi_bu_sandhi(syllables_for(hanzi, numbered)))


@pytest.mark.parametrize(
    "hanzi,numbered,expected",
    [
        # 不
        ("不是", "bu4 shi4", "bú shì"),
        ("不好", "bu4 hao3", "bù hǎo"),
        ("不来", "bu4 lai2", "bù lái"),
        ("对不起", "dui4 bu5 qi3", "duì bu qǐ"),  # already neutral: untouched
        # 一 before tones
        ("一样", "yi1 yang4", "yí yàng"),
        ("一个", "yi1 ge4", "yí gè"),
        ("一个", "yi1 ge5", "yí ge"),  # neutral hides a 4th tone
        ("一天", "yi1 tian1", "yì tiān"),
        ("一年", "yi1 nian2", "yì nián"),
        ("一起", "yi1 qi3", "yì qǐ"),
        # 一 keeps yī
        ("统一", "tong3 yi1", "tǒng yī"),  # end
        ("第一次", "di4 yi1 ci4", "dì yī cì"),  # ordinal
        ("一二三", "yi1 er4 san1", "yī èr sān"),  # counting
        ("十一", "shi2 yi1", "shí yī"),
        ("一月", "yi1 yue4", "yī yuè"),  # date
    ],
)
def test_yi_bu_sandhi(hanzi, numbered, expected):
    assert spoken(hanzi, numbered) == expected


def test_tone_number_follows_spoken_tone():
    out = apply_yi_bu_sandhi(syllables_for("不是", "bu4 shi4"))
    assert [s.tone for s in out] == [2, 4]


def test_input_is_not_mutated():
    syl = syllables_for("一样", "yi1 yang4")
    apply_yi_bu_sandhi(syl)
    assert syl[0].pinyin == "yī" and syl[0].tone == 1


def test_other_syllables_untouched():
    assert spoken("你好", "ni3 hao3") == "nǐ hǎo"
