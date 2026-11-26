"""CC-CEDICT parser."""
import re
from collections import defaultdict
from dataclasses import dataclass
from typing import Iterable

_LINE = re.compile(r"^(\S+)\s+(\S+)\s+\[([^\]]*)\]\s+/(.*)/\s*$")


@dataclass
class CedictEntry:
    traditional: str
    simplified: str
    pinyin_numbered: str
    glosses_en: list[str]


def parse_cedict(lines: Iterable[str]) -> dict[str, list[CedictEntry]]:
    """Parse CC-CEDICT lines into entries keyed by simplified form."""
    entries: dict[str, list[CedictEntry]] = defaultdict(list)
    for raw in lines:
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        m = _LINE.match(line)
        if not m:
            continue
        trad, simp, pinyin, glosses = m.groups()
        pinyin = pinyin.replace("u:", "v").replace("U:", "V").lower()
        entries[simp].append(
            CedictEntry(trad, simp, pinyin, [g for g in glosses.split("/") if g])
        )
    return dict(entries)
