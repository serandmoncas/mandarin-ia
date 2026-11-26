"""Spoken-tone sandhi for 一 and 不 (third-tone sandhi is deliberately not marked).

Input syllables carry dictionary tones (一 = yi1, 不 = bu4), as produced by pypinyin or
by a validated proposal. The output shows what a speaker actually says, and the tone
number drives the syllable colour in the app.
"""
from mandarin_pipeline.models import Syllable
from mandarin_pipeline.pinyin import _mark

_BASES = {"一": "yi", "不": "bu"}

# Han numerals that mark "counting" context: 一 keeps yī next to them (一二三, 十一, 一百一).
NUMERALS = set("零一二三四五六七八九十百千万亿两")


def retone(s: Syllable, tone: int) -> Syllable:
    """Copy of an 一/不 syllable with a new tone and its tone-marked pinyin."""
    return s.model_copy(update={"tone": tone, "pinyin": _mark(_BASES[s.hanzi], tone)})


def apply_yi_bu_sandhi(syllables: list[Syllable]) -> list[Syllable]:
    """Return a new list where 一 and 不 show their spoken tone.

    Rules (see tests/test_sandhi.py):
    - 不 (bu4) before a 4th tone -> bú (2).
    - 一 (yi1) before a 4th tone -> yí (2); before a 1st, 2nd or 3rd tone -> yì (4).
    - 一 keeps yī (1): at the end, after 第 (ordinals), next to another numeral
      (counting: 一二三, 十一) and before 月 (dates: 一月).
    - A neutral tone (5) after 一 usually hides a 4th tone (一个 yí ge): treat it as 4.

    Only change 一 with tone 1 and 不 with tone 4; never mutate the input.
    Use `retone(s, tone)` to build the changed syllable and `NUMERALS` for counting.
    """
    out = list(syllables)
    for i, s in enumerate(syllables):
        nxt = syllables[i + 1] if i + 1 < len(syllables) else None
        if nxt is None:
            continue
        if s.hanzi == "不" and s.tone == 4 and nxt.tone == 4:
            out[i] = retone(s, 2)
        elif s.hanzi == "一" and s.tone == 1:
            prev = syllables[i - 1] if i > 0 else None
            counting = (prev is not None and (prev.hanzi == "第" or prev.hanzi in NUMERALS)) or (
                nxt.hanzi in NUMERALS or nxt.hanzi == "月"
            )
            if not counting:
                out[i] = retone(s, 2 if nxt.tone in (4, 5) else 4)
    return out
