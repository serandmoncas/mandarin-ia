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


def _join_text(syllables: list[Syllable]) -> str:
    """Space-joined pinyin text; an erhua syllable (儿 read "r") attaches to the previous one."""
    text = ""
    for i, s in enumerate(syllables):
        erhua = s.hanzi == "儿" and s.pinyin == "r" and i > 0
        text += s.pinyin if erhua or not text else f" {s.pinyin}"
    return text


_MAX_WORD_LEN = 4
_UNMARK = {
    mark: ("v" if plain == "ü" else plain) for plain, marks in _MARKS.items() for mark in marks
}


def _base_of(marked: str) -> str:
    """Toneless base of a marked syllable, ü as v ("lǜ" -> "lv")."""
    return "".join(_UNMARK.get(c, c) for c in marked.lower())


WordReadings = dict[str, list[list[tuple[str, int]]]]

# CEDICT neutral readings that only fit a rare sense: 大人 "adult" is dàrén (neutral only
# as an honorific), 那是 is nà shì except as colloquial "of course".
_UNRELIABLE_NEUTRAL = {"大人", "那是"}


def word_readings(cedict: dict[str, list[CedictEntry]]) -> WordReadings:
    """Per multi-character word, every CEDICT reading as [(base, tone), ...] (ü as v)."""
    words: WordReadings = {}
    for word, entries in cedict.items():
        if len(word) < 2 or word in _UNRELIABLE_NEUTRAL:
            continue
        for entry in entries:
            syls = entry.pinyin_numbered.split()
            if len(syls) != len(word):
                continue
            words.setdefault(word, []).append([_split_tone(_normalize(s)) for s in syls])
    return words


def _neutralize(out: list[Syllable], idxs: list[int], readings: list[list[tuple[str, int]]]) -> None:
    for k, i in enumerate(idxs):
        if all(r[k][1] == 5 for r in readings):
            base = readings[0][k][0]
            if _base_of(out[i].pinyin) == base:
                out[i] = out[i].model_copy(update={"pinyin": _mark(base, 5), "tone": 5})


def apply_word_neutral_tones(syllables: list[Syllable], words: WordReadings) -> list[Syllable]:
    """Make neutral the syllables that every CEDICT reading of a word marks as tone 5.

    Words must respect jieba's segmentation: first a run of whole jieba tokens (longest
    first, so 找/不到 -> 找不到), otherwise words inside one token, matched from the right
    (做作业 -> 做 + 作业, never 做作). Only a syllable whose base matches CEDICT's changes.
    """
    import jieba  # local: loading jieba is slow and only this path needs it

    out = list(syllables)
    # one char per han syllable; anything else is a hard boundary
    text = "".join(s.hanzi if _is_han(s.hanzi) and len(s.hanzi) == 1 else "\n" for s in out)
    bounds = [0]
    for token in jieba.lcut(text, HMM=False):
        bounds.append(bounds[-1] + len(token))
    ti = 0
    while ti < len(bounds) - 1:
        for tj in range(len(bounds) - 1, ti + 1, -1):
            word = text[bounds[ti] : bounds[tj]]
            if len(word) <= _MAX_WORD_LEN and word in words:
                _neutralize(out, list(range(bounds[ti], bounds[tj])), words[word])
                ti = tj
                break
        else:
            lo, end = bounds[ti], bounds[ti + 1]
            while end - lo > 1:
                for size in range(min(_MAX_WORD_LEN, end - lo), 1, -1):
                    word = text[end - size : end]
                    if word in words:
                        _neutralize(out, list(range(end - size, end)), words[word])
                        end -= size
                        break
                else:
                    end -= 1
            ti += 1
    return out


def sentence_pinyin(
    zh: str,
    proposed: str | None = None,
    readings: dict[str, set[str]] | None = None,
    words: WordReadings | None = None,
) -> tuple[str, list[Syllable], bool]:
    """Pinyin of a sentence with CEDICT neutral tones (when `words`) and 一/不 sandhi applied.

    Uses the proposed numbered pinyin when it validates against `readings`; otherwise pypinyin.
    The bool is True when a proposal existed but failed validation.
    """
    from mandarin_pipeline.sandhi import apply_yi_bu_sandhi  # sandhi imports _mark from here

    syllables = validate_numbered(zh, proposed, readings or {}) if proposed else None
    fell_back = bool(proposed) and syllables is None
    if syllables is None:
        syllables = _pypinyin_syllables(zh)
    if words is not None:
        syllables = apply_word_neutral_tones(syllables, words)
    syllables = apply_yi_bu_sandhi(syllables)
    return _join_text(syllables), syllables, fell_back


def _normalize(syl: str) -> str:
    return syl.lower().replace("u:", "v").replace("ü", "v")


def char_readings(cedict: dict[str, list[CedictEntry]]) -> dict[str, set[str]]:
    """Numbered syllables (ü as v, e.g. "de2", "de5") of every known reading of each character."""
    readings: dict[str, set[str]] = {}
    for entries in cedict.values():
        for entry in entries:
            syls = entry.pinyin_numbered.split()
            if len(syls) != len(entry.simplified):
                continue
            for ch, syl in zip(entry.simplified, syls):
                if _is_han(ch):
                    base, tone = _split_tone(_normalize(syl))
                    readings.setdefault(ch, set()).add(f"{base}{tone}")
    for ch in set(readings) | {c for c in cedict if len(c) == 1 and _is_han(c)}:
        for item in pinyin(ch, style=Style.TONE3, neutral_tone_with_five=True, heteronym=True):
            for r in item:
                base, tone = _split_tone(_normalize(r))
                readings.setdefault(ch, set()).add(f"{base}{tone}")
    return readings


# 一 and 不 are validated with their dictionary tone; sandhi alone decides the spoken one.
_DICTIONARY_TONE = {"一": 1, "不": 4}


def validate_numbered(
    zh: str, numbered: str, readings: dict[str, set[str]]
) -> list[Syllable] | None:
    """Accept proposed numbered pinyin only if each syllable is a real reading of its character.

    Tones 1-4 must match a known numbered reading; tone 5 only needs a known base.
    """
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
        if part[-1] not in "12345":
            return None
        if tone != 5:  # a neutral 一/不 stays neutral; otherwise sandhi decides
            tone = _DICTIONARY_TONE.get(ch, tone)
        known = readings.get(ch, set())
        if tone == 5:
            ok = any(r[:-1] == base for r in known)
        else:
            ok = f"{base}{tone}" in known
        if not ok:
            return None
        out.append(Syllable(hanzi=ch, pinyin=_mark(base, tone), tone=tone))
    return out
