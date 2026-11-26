"""Candidate selection and learning order."""
import json
from dataclasses import dataclass, replace
from pathlib import Path
from typing import Callable

HSK_PULL = 1.25  # weight applied to the HSK rank when mixing with frequency rank


@dataclass
class Candidate:
    word: str
    frequency: float
    hsk_level: int | None
    freq_rank: int = 0
    order: int = 0


def select_candidates(
    hsk: dict[str, int],
    cedict: dict,
    freq_words: list[str],
    freq: Callable[[str], float],
    max_level: int = 3,
    total: int = 2500,
) -> tuple[list[Candidate], list[str]]:
    """All HSK words up to max_level present in CEDICT, filled with frequent words up to total."""
    cands: list[Candidate] = []
    warnings: list[str] = []
    seen: set[str] = set()
    for word, level in hsk.items():
        if level > max_level:
            continue
        if word not in cedict:
            warnings.append(word)
            continue
        cands.append(Candidate(word, freq(word), level))
        seen.add(word)
    for word in freq_words:
        if len(cands) >= total:
            break
        if word in seen or word not in cedict:
            continue
        cands.append(Candidate(word, freq(word), hsk.get(word)))  # HSK 4+ keeps its level
        seen.add(word)
    return cands, warnings


def learning_order(cands: list[Candidate]) -> list[Candidate]:
    """Assign freq_rank and order; HSK words are pulled forward by their HSK rank."""
    by_freq = sorted(cands, key=lambda c: -c.frequency)
    ranked = [replace(c, freq_rank=i) for i, c in enumerate(by_freq, 1)]
    hsk_sorted = sorted(
        (c for c in ranked if c.hsk_level is not None),
        key=lambda c: (c.hsk_level, c.freq_rank),
    )
    hsk_rank = {c.word: i for i, c in enumerate(hsk_sorted, 1)}

    def key(c: Candidate) -> tuple[float, int]:
        k = float(c.freq_rank)
        if c.word in hsk_rank:
            k = min(k, HSK_PULL * hsk_rank[c.word])
        return (k, c.freq_rank)

    result = sorted(ranked, key=key)
    return [replace(c, order=i) for i, c in enumerate(result, 1)]


def write_candidates(cands: list[Candidate], path: Path) -> None:
    rows = [
        {
            "word": c.word,
            "frequency": c.frequency,
            "hskLevel": c.hsk_level,
            "freqRank": c.freq_rank,
            "order": c.order,
        }
        for c in cands
    ]
    Path(path).write_text(
        json.dumps(rows, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
