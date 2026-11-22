"""Automatic checks over generated content and the final status decision."""
import hashlib
import json
from dataclasses import dataclass, field
from pathlib import Path

import jieba

from mandarin_pipeline.cedict import CedictEntry
from mandarin_pipeline.models import (
    CharContent,
    Example,
    PhraseContent,
    Status,
    Syllable,
    WordContent,
    WordPinyin,
)
from mandarin_pipeline.pinyin import (
    WordReadings,
    _is_han,
    char_readings,
    sentence_pinyin,
    syllables_for,
    word_readings,
)

MAX_HAN = 20
MIN_EXAMPLES = 2


@dataclass
class CheckedWord:
    content: WordContent
    reading: CedictEntry | None
    examples: list[Example]
    flags: list[str] = field(default_factory=list)
    syllables: list[Syllable] | None = None


def _han_count(text: str) -> int:
    return sum(_is_han(c) for c in text)


def _is_han_token(token: str) -> bool:
    return any(_is_han(c) for c in token)


def known_before_ratio(zh: str, target: str, known: set[str]) -> float:
    """Share of han tokens that are the target word or already known."""
    total = hits = 0
    for i, piece in enumerate(zh.split(target)):
        if i > 0:  # each split point is one occurrence of the target
            total += 1
            hits += 1
        for token in jieba.lcut(piece):
            if _is_han_token(token):
                total += 1
                hits += token in known
    return hits / total if total else 0.0


def check_word(
    content: WordContent,
    entries: list[CedictEntry],
    known: set[str],
    proposals: dict[str, str] | None = None,
    readings: dict[str, set[str]] | None = None,
    words: WordReadings | None = None,
) -> CheckedWord:
    """`proposals` maps an example's zh to proposed numbered pinyin, validated with `readings`."""
    flags: list[str] = []
    idx = content.cedict_reading_index
    reading = entries[idx] if idx < len(entries) else None
    if reading is None:
        flags.append("reading_index_out_of_range")

    # Dedupe meanings (whitespace-insensitive) so the app never renders duplicates.
    meanings: list[str] = []
    for m in content.meanings_es:
        if m.strip() not in {x.strip() for x in meanings}:
            meanings.append(m)
    if meanings != content.meanings_es:
        content = content.model_copy(update={"meanings_es": meanings})

    examples: list[Example] = []
    seen_zh: set[str] = set()
    for ex in content.examples:
        if content.word not in ex.zh or _han_count(ex.zh) > MAX_HAN or not ex.es.strip():
            continue
        if ex.zh in seen_zh:
            continue
        seen_zh.add(ex.zh)
        pinyin_text, syllables, fell_back = sentence_pinyin(
            ex.zh, (proposals or {}).get(ex.zh), readings, words
        )
        if fell_back and "pinyin_fallback" not in flags:
            flags.append("pinyin_fallback")
        examples.append(
            Example(
                zh=ex.zh,
                pinyin=pinyin_text,
                syllables=syllables,
                es=ex.es,
                known_before_ratio=known_before_ratio(ex.zh, content.word, known),
            )
        )
    if len(examples) < MIN_EXAMPLES:
        flags.append("too_few_examples")

    syllables = None
    if reading is not None:
        syllables = syllables_for(content.word, reading.pinyin_numbered)
        if syllables is None:
            flags.append("syllable_mismatch")

    if any(not m.strip() for m in content.meanings_es):
        flags.append("empty_meaning")
    return CheckedWord(content, reading, examples, flags, syllables)


def check_char(content: CharContent) -> list[str]:
    flags = []
    if not content.mnemonic_es.strip():
        flags.append("empty_mnemonic")
    if any(not c.meaning_es.strip() for c in content.components):
        flags.append("empty_component_meaning")
    return flags


def check_phrase(
    content: PhraseContent, words: WordReadings | None = None
) -> tuple[str, list[Syllable], list[str]]:
    flags = []
    if not content.es.strip():
        flags.append("empty_translation")
    if _han_count(content.zh) > MAX_HAN:
        flags.append("too_long")
    pinyin_text, syllables, _ = sentence_pinyin(content.zh, words=words)
    return pinyin_text, syllables, flags


def apply_review(flags: list[str], review_ok: bool, issues: list[str]) -> tuple[Status, list[str]]:
    """auto_checked only with no automatic flags and an ok review; otherwise generated."""
    if not flags and review_ok and not issues:
        return "auto_checked", []
    review_flags = [f"review:{i}" for i in issues]
    if not review_ok and not issues:
        review_flags.append("review:not_ok")
    return "generated", [*flags, *review_flags]


# ---- review item building (items with no automatic flags only) ----


def _load_dir(path: Path) -> list[dict]:
    """Concatenate the records of every batch_NNN.json in a directory, in order."""
    out: list[dict] = []
    for f in sorted(Path(path).glob("batch_*.json")):
        out.extend(json.loads(f.read_text(encoding="utf-8")))
    return out


def phrase_id(mission: str, index: int) -> str:
    return f"phrase:{mission}:{index:03d}"


def content_hash(text: str) -> str:
    """sha1 of exactly the text sent to the reviewer for one item."""
    return hashlib.sha1(text.encode("utf-8")).hexdigest()


def _item(item_id: str, text: str) -> dict:
    return {"id": item_id, "text": text, "content_hash": content_hash(text)}


def review_items_from(
    words: dict[str, CheckedWord],
    chars: list[CharContent],
    phrases: list[PhraseContent],
    neutral_words: WordReadings | None = None,
) -> list[dict]:
    """Review items ({id, text, content_hash}) for content with no automatic flags.

    Shared by the review step (what to send) and the build (which review still matches).
    """
    items: list[dict] = []
    for checked in words.values():
        if checked.flags:
            continue
        content = checked.content
        lines = [
            f"Palabra: {content.word} ({checked.reading.pinyin_numbered})",
            f"Glosas CEDICT: {'; '.join(checked.reading.glosses_en)}",
            f"Significados: {'; '.join(content.meanings_es)}",
        ]
        lines += [f"Ejemplo: {e.zh} | {e.pinyin} | {e.es}" for e in checked.examples]
        items.append(_item(f"word:{content.word}", "\n".join(lines)))

    for char in chars:
        if check_char(char):
            continue
        comps = "; ".join(f"{c.char} = {c.meaning_es}" for c in char.components)
        items.append(
            _item(
                f"char:{char.char}",
                f"Carácter: {char.char}\nComponentes: {comps}\nMnemotecnia: {char.mnemonic_es}",
            )
        )

    counters: dict[str, int] = {}
    for phrase in phrases:
        idx = counters.get(phrase.mission, 0)
        counters[phrase.mission] = idx + 1
        pinyin_text, _, flags = check_phrase(phrase, neutral_words)
        if flags:
            continue
        items.append(
            _item(
                phrase_id(phrase.mission, idx),
                f"Situación: {phrase.mission}\nFrase: {phrase.zh} | {pinyin_text} | {phrase.es}",
            )
        )
    return items


def _load_pinyin_proposals(path: Path) -> dict[str, dict[str, str]]:
    """word -> {zh: numbered pinyin} from the pinyin batches; later batches win per word."""
    if not path.is_dir():
        return {}
    proposals: dict[str, dict[str, str]] = {}
    for raw in _load_dir(path):
        wp = WordPinyin.model_validate(raw)
        proposals[wp.word] = {e.zh: e.pinyin for e in wp.examples}
    return proposals


def load_checked_words(
    gen_dir: Path,
    cedict: dict[str, list[CedictEntry]],
    order: dict[str, int],
    neutral_words: WordReadings | None = None,
) -> dict[str, CheckedWord]:
    """Run check_word over every generated word, with the words learned before it as known.

    `neutral_words` None means no CEDICT neutral tones (callers pass `word_readings(cedict)`).
    """
    by_order = sorted(order.items(), key=lambda kv: kv[1])
    readings = char_readings(cedict)
    proposals = _load_pinyin_proposals(Path(gen_dir) / "pinyin")
    words: dict[str, CheckedWord] = {}
    for raw in _load_dir(Path(gen_dir) / "words"):
        content = WordContent.model_validate(raw)
        before = order.get(content.word, 0)
        known = {w for w, o in by_order if o < before}
        words[content.word] = check_word(
            content, cedict.get(content.word, []), known, proposals.get(content.word), readings,
            neutral_words,
        )
    return words


def build_review_items(
    gen_dir: Path, cedict: dict[str, list[CedictEntry]], candidates: list[dict]
) -> list[dict]:
    """Items that passed the automatic checks, read from the generated batch files."""
    gen_dir = Path(gen_dir)
    neutral_words = word_readings(cedict)
    words = load_checked_words(
        gen_dir, cedict, {c["word"]: c["order"] for c in candidates}, neutral_words
    )
    chars = [CharContent.model_validate(x) for x in _load_dir(gen_dir / "chars")]
    phrases = [PhraseContent.model_validate(x) for x in _load_dir(gen_dir / "phrases")]
    return review_items_from(words, chars, phrases, neutral_words)
