"""Pinyin helpers: numbered -> tone-marked, per-character syllables, sentence pinyin."""
from pypinyin import Style, pinyin

from mandarin_pipeline.models import Syllable

_MARKS = {
    "a": "āáǎàa",
    "e": "ēéěèe",
    "i": "īíǐìi",
    "o": "ōóǒòo",
    "u": "ūúǔùu",
    "ü": "ǖǘǚǜü",
}
_VOWELS = "aeiouü"


def _is_han(ch: str) -> bool:
    return "一" <= ch <= "鿿"


def _split_tone(syl: str) -> tuple[str, int]:
    if syl and syl[-1] in "12345":
        return syl[:-1], int(syl[-1])
    return syl, 5


def _mark(base: str, tone: int) -> str:
    base = base.replace("v", "ü").replace("V", "Ü")
    if tone == 5:
        return base
    lower = base.lower()
    if "a" in lower:
        pos = lower.index("a")
    elif "e" in lower:
        pos = lower.index("e")
    elif "ou" in lower:
        pos = lower.index("o")
    else:
        pos = max((i for i, c in enumerate(lower) if c in _VOWELS), default=-1)
    if pos < 0:
        return base
    marked = _MARKS[lower[pos]][tone - 1]
    return base[:pos] + (marked.upper() if base[pos].isupper() else marked) + base[pos + 1 :]


def numbered_to_marked(s: str) -> str:
    """Convert numbered pinyin ("ni3 hao3") to tone-marked ("nǐ hǎo"). Tone 5 has no mark."""
    return " ".join(_mark(*_split_tone(syl)) for syl in s.split())


def syllables_for(hanzi: str, numbered: str) -> list[Syllable] | None:
    """Pair each character with its syllable; None when the counts differ."""
    parts = numbered.split()
    if len(hanzi) != len(parts):
        return None
    out = []
    for ch, part in zip(hanzi, parts):
        base, tone = _split_tone(part)
        out.append(Syllable(hanzi=ch, pinyin=_mark(base, tone), tone=tone))
    return out


def sentence_pinyin(zh: str) -> tuple[str, list[Syllable]]:
    """Citation-tone pinyin of a sentence via pypinyin; punctuation/latin get no syllable."""
    items = pinyin(zh, style=Style.TONE3, neutral_tone_with_five=True, errors=lambda _s: [])
    han = [ch for ch in zh if _is_han(ch)]
    syllables = []
    for ch, item in zip(han, items):
        base, tone = _split_tone(item[0])
        syllables.append(Syllable(hanzi=ch, pinyin=_mark(base, tone), tone=tone))
    return " ".join(s.pinyin for s in syllables), syllables
