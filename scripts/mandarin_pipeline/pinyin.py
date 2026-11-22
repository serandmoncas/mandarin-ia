"""Pinyin helpers: numbered -> tone-marked, per-character syllables, sentence pinyin."""
from pypinyin import Style, pinyin

from mandarin_pipeline.cedict import CedictEntry
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


def _pypinyin_syllables(zh: str) -> list[Syllable]:
    """Citation-tone syllables via pypinyin; punctuation/latin get no syllable."""
    items = pinyin(zh, style=Style.TONE3, neutral_tone_with_five=True, errors=lambda _s: [])
    han = [ch for ch in zh if _is_han(ch)]
    syllables = []
    for ch, item in zip(han, items):
        base, tone = _split_tone(item[0])
        syllables.append(Syllable(hanzi=ch, pinyin=_mark(base, tone), tone=tone))
    return syllables


def sentence_pinyin(
    zh: str, proposed: str | None = None, readings: dict[str, set[str]] | None = None
) -> tuple[str, list[Syllable], bool]:
    """Pinyin of a sentence with 一/不 sandhi applied.

    Uses the proposed numbered pinyin when it validates against `readings`; otherwise pypinyin.
    The bool is True when a proposal existed but failed validation.
    """
    from mandarin_pipeline.sandhi import apply_yi_bu_sandhi  # sandhi imports _mark from here

    syllables = validate_numbered(zh, proposed, readings or {}) if proposed else None
    fell_back = bool(proposed) and syllables is None
    if syllables is None:
        syllables = _pypinyin_syllables(zh)
    syllables = apply_yi_bu_sandhi(syllables)
    return " ".join(s.pinyin for s in syllables), syllables, fell_back


def _normalize(syl: str) -> str:
    return syl.lower().replace("u:", "v").replace("ü", "v")


def char_readings(cedict: dict[str, list[CedictEntry]]) -> dict[str, set[str]]:
    """Toneless bases (ü as v) of every known reading of each han character."""
    readings: dict[str, set[str]] = {}
    for entries in cedict.values():
        for entry in entries:
            syls = entry.pinyin_numbered.split()
            if len(syls) != len(entry.simplified):
                continue
            for ch, syl in zip(entry.simplified, syls):
                if _is_han(ch):
                    readings.setdefault(ch, set()).add(_split_tone(_normalize(syl))[0])
    for ch in set(readings) | {c for c in cedict if len(c) == 1 and _is_han(c)}:
        for item in pinyin(ch, style=Style.NORMAL, heteronym=True):
            readings.setdefault(ch, set()).update(_normalize(r) for r in item)
    return readings


def validate_numbered(
    zh: str, numbered: str, readings: dict[str, set[str]]
) -> list[Syllable] | None:
    """Accept proposed numbered pinyin only if each syllable is a real reading of its character."""
    han = [ch for ch in zh if _is_han(ch)]
    parts = numbered.split()
    if len(han) != len(parts):
        return None
    out = []
    for i, (ch, part) in enumerate(zip(han, parts)):
        base, tone = _split_tone(_normalize(part))
        if ch == "儿" and base == "r" and i > 0:
            out.append(Syllable(hanzi=ch, pinyin="r", tone=5))
            continue
        if base not in readings.get(ch, set()):
            return None
        out.append(Syllable(hanzi=ch, pinyin=_mark(base, tone), tone=tone))
    return out
