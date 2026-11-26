"""Assemble the final dictionary.json from candidates, generated content and reviews."""
import json
import os
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

from mandarin_pipeline.audio_keys import SENTENCE_VOICE, WORD_VOICES, audio_key
from mandarin_pipeline.checks import (
    CheckedWord,
    apply_review,
    check_char,
    check_phrase,
    phrase_id,
    review_items_from,
)
from mandarin_pipeline.models import (
    AudioRef,
    CamelModel,
    CharContent,
    Example,
    MissionId,
    PhraseContent,
    ReviewResult,
    Status,
    Syllable,
)
from mandarin_pipeline.order import Candidate
from mandarin_pipeline.pinyin import WordReadings, numbered_to_marked

# Mirrors data/SOURCES.md; keep both in sync.
CREDITS: list[dict[str, str]] = [
    {
        "name": "CC-CEDICT",
        "license": "CC BY-SA 4.0",
        "url": "https://www.mdbg.net/chinese/dictionary?page=cc-cedict",
    },
    {
        "name": "SUBTLEX-CH (vía wordfreq)",
        "license": "Uso libre con crédito a los autores de SUBTLEX (Cai y Brysbaert, 2010)",
        "url": "https://github.com/rspeer/wordfreq",
    },
    {
        "name": "Lista HSK 3.0 (drkameleon/complete-hsk-vocabulary)",
        "license": "MIT",
        "url": "https://github.com/drkameleon/complete-hsk-vocabulary",
    },
    {
        "name": "Voces de Microsoft Azure (Azure AI Speech)",
        "license": "Servicio de Microsoft Azure",
        "url": "https://azure.microsoft.com/products/ai-services/text-to-speech",
    },
]


class Credit(CamelModel):
    name: str
    license: str
    url: str


class WordEntry(CamelModel):
    id: str
    simplified: str
    traditional: str
    pinyin: str
    pinyin_numbered: str
    syllables: list[Syllable]
    meanings_es: list[str]
    hsk_level: int | None
    freq_rank: int
    order: int
    audio: list[AudioRef]
    examples: list[Example]
    status: Status
    flags: list[str]


class CharComponent(CamelModel):
    char: str
    meaning_es: str


class CharacterInfo(CamelModel):
    char: str
    components: list[CharComponent]
    mnemonic_es: str
    status: Status
    flags: list[str]


class PhraseEntry(CamelModel):
    id: str
    mission: MissionId
    zh: str
    pinyin: str
    syllables: list[Syllable]
    es: str
    audio: AudioRef | None
    status: Status
    flags: list[str]


class Dictionary(CamelModel):
    version: str
    generated_at: str
    words: list[WordEntry]
    characters: dict[str, CharacterInfo]
    phrases: list[PhraseEntry]
    credits: list[Credit]


def _resolve(review: ReviewResult | None, flags: list[str]) -> tuple[Status, list[str]]:
    if review is None:
        return "generated", [*flags, "not_reviewed"]
    return apply_review(flags, review.ok, review.issues)


def _sentence_audio(text: str, manifest: dict[str, str]) -> AudioRef | None:
    key = audio_key(text, SENTENCE_VOICE)
    return AudioRef(voice=SENTENCE_VOICE, path=manifest[key]) if key in manifest else None


def matching_reviews(
    words: dict[str, CheckedWord],
    chars: list[CharContent],
    phrases: list[PhraseContent],
    reviews: list[ReviewResult],
    neutral_words: WordReadings | None = None,
) -> dict[str, ReviewResult]:
    """Reviews (by id) whose content hash matches the item's current review text.

    A verdict for older content (same id, different text) is ignored, so regenerated
    content is never shown as checked until it is reviewed again. Later reviews win.
    """
    by_key = {(r.id, r.content_hash): r for r in reviews if r.content_hash}
    out: dict[str, ReviewResult] = {}
    for item in review_items_from(words, chars, phrases, neutral_words):
        review = by_key.get((item["id"], item["content_hash"]))
        if review is not None:
            out[item["id"]] = review
    return out


def build_dictionary(
    candidates: list[Candidate],
    words: dict[str, CheckedWord],
    reviews: list[ReviewResult],
    chars: list[CharContent],
    phrases: list[PhraseContent],
    manifest: dict[str, str],
    version: str,
    generated_at: str,
    neutral_words: WordReadings | None = None,
) -> Dictionary:
    reviews_by_id = matching_reviews(words, chars, phrases, reviews, neutral_words)
    word_entries: list[WordEntry] = []
    for cand in sorted(candidates, key=lambda c: c.order):
        checked = words.get(cand.word)
        if checked is None:
            continue  # no generated content: counted as "missing" by stats
        status, flags = _resolve(reviews_by_id.get(f"word:{cand.word}"), checked.flags)
        numbered = checked.reading.pinyin_numbered if checked.reading else ""
        audio = [
            AudioRef(voice=v, path=manifest[audio_key(cand.word, v)])
            for v in WORD_VOICES
            if audio_key(cand.word, v) in manifest
        ]
        examples = [
            e.model_copy(update={"audio": _sentence_audio(e.zh, manifest)}) for e in checked.examples
        ]
        word_entries.append(
            WordEntry(
                id=cand.word,
                simplified=cand.word,
                traditional=checked.reading.traditional if checked.reading else cand.word,
                pinyin=numbered_to_marked(numbered),
                pinyin_numbered=numbered,
                syllables=checked.syllables or [],
                meanings_es=checked.content.meanings_es,
                hsk_level=cand.hsk_level,
                freq_rank=cand.freq_rank,
                order=cand.order,
                audio=audio,
                examples=examples,
                status=status,
                flags=flags,
            )
        )

    characters: dict[str, CharacterInfo] = {}
    for c in chars:
        status, flags = _resolve(reviews_by_id.get(f"char:{c.char}"), check_char(c))
        characters[c.char] = CharacterInfo(
            char=c.char,
            components=[CharComponent(char=x.char, meaning_es=x.meaning_es) for x in c.components],
            mnemonic_es=c.mnemonic_es,
            status=status,
            flags=flags,
        )

    phrase_entries: list[PhraseEntry] = []
    counters: Counter[str] = Counter()
    for p in phrases:
        pid = phrase_id(p.mission, counters[p.mission])
        counters[p.mission] += 1
        pinyin_text, syllables, auto_flags = check_phrase(p, neutral_words)
        status, flags = _resolve(reviews_by_id.get(pid), auto_flags)
        phrase_entries.append(
            PhraseEntry(
                id=pid,
                mission=p.mission,
                zh=p.zh,
                pinyin=pinyin_text,
                syllables=syllables,
                es=p.es,
                audio=_sentence_audio(p.zh, manifest),
                status=status,
                flags=flags,
            )
        )

    return Dictionary(
        version=version,
        generated_at=generated_at,
        words=word_entries,
        characters=characters,
        phrases=phrase_entries,
        credits=[Credit(**c) for c in CREDITS],
    )


def now_stamps() -> tuple[str, str]:
    """(version YYYYMMDDHHMM, ISO-8601 UTC) for the current instant."""
    now = datetime.now(timezone.utc).replace(microsecond=0)
    return now.strftime("%Y%m%d%H%M"), now.isoformat().replace("+00:00", "Z")


def load_manifest(path: Path) -> dict[str, str]:
    path = Path(path)
    return json.loads(path.read_text(encoding="utf-8")) if path.exists() else {}


def dictionary_json(d: Dictionary) -> str:
    return json.dumps(d.model_dump(by_alias=True), ensure_ascii=False, indent=2) + "\n"


def write_dictionary(d: Dictionary, path: Path) -> None:
    """Atomic write: a crash never leaves a truncated dictionary.json."""
    path = Path(path)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(dictionary_json(d), encoding="utf-8")
    try:
        os.replace(tmp, path)
    except OSError:
        tmp.unlink(missing_ok=True)
        raise


VISIBLE: tuple[Status, ...] = ("auto_checked", "human_reviewed")


def visibility_warning(d: Dictionary) -> str | None:
    """A warning when the app would show no word at all (and its build would need one)."""
    if any(w.status in VISIBLE for w in d.words):
        return None
    return (
        f"0 palabras visibles (auto_checked/human_reviewed) de {len(d.words)}. La app no "
        "mostrará ninguna palabra. Ejecuta `review` y luego `build`, o revisa las marcas con `stats`."
    )


def compute_stats(candidates: list[Candidate], d: Dictionary) -> dict[str, dict[str, int]]:
    """Counts by status (words, with 'missing' for candidates lacking content), flag and HSK level."""
    present = {w.id for w in d.words}
    words_status = Counter(w.status for w in d.words)
    words_status["missing"] = sum(c.word not in present for c in candidates)
    by_flag = Counter(f.split(":", 1)[0] for w in d.words for f in w.flags)
    by_hsk = Counter(str(w.hsk_level) if w.hsk_level else "none" for w in d.words)
    return {
        "words": dict(words_status),
        "characters": dict(Counter(c.status for c in d.characters.values())),
        "phrases": dict(Counter(p.status for p in d.phrases)),
        "flags": dict(by_flag),
        "hsk": dict(by_hsk),
    }
