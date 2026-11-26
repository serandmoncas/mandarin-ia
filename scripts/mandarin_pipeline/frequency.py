"""Word frequency helpers backed by wordfreq (SUBTLEX-CH among others)."""
from mandarin_pipeline.cedict import CedictEntry


def is_han_word(s: str) -> bool:
    return bool(s) and all("㐀" <= c <= "鿿" for c in s)


def word_frequency(word: str) -> float:
    from wordfreq import word_frequency as _wf

    return _wf(word, "zh")


def _top_n_list(n: int) -> list[str]:
    from wordfreq import top_n_list

    return top_n_list("zh", n)


def top_frequency_words(n: int, cedict: dict[str, list[CedictEntry]]) -> list[str]:
    """Top-n wordfreq zh tokens that are pure Han and present in CC-CEDICT."""
    return [w for w in _top_n_list(n) if is_han_word(w) and w in cedict]
