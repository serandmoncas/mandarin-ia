"""Build data/duolingo/palabras.json from the Duolingo extraction.

Inputs (all in data/duolingo/):
  raw.tsv        hanzi, pinyin, English meaning (may be empty), unit as S<n>U<m>
  es_manual.tsv  hanzi, Spanish meaning for words missing from dictionary.json
Cross-references data/dictionary.json to add Spanish meanings, HSK level and
frequency rank. Stdlib only:

    python3 scripts/duolingo_build.py --progress "Sección X, unidad Y"

The output is personal (git-ignored), so progress is passed in, never hardcoded.
"""

import argparse
import json
import re
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DUO = ROOT / "data" / "duolingo"


def read_tsv(path: Path) -> list[list[str]]:
    lines = path.read_text(encoding="utf-8").splitlines()
    return [line.split("\t") for line in lines if line.strip()]


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--progress", default="", help="current Duolingo position, free text")
    args = parser.parse_args()

    dictionary = json.loads((ROOT / "data" / "dictionary.json").read_text(encoding="utf-8"))
    by_hanzi = {w["simplified"]: w for w in dictionary["words"]}
    manual_es = {row[0]: row[1] for row in read_tsv(DUO / "es_manual.tsv")}

    words = []
    for hanzi, pinyin, meaning_en, unit_code in read_tsv(DUO / "raw.tsv"):
        section, unit = map(int, re.fullmatch(r"S(\d+)U(\d+)", unit_code).groups())
        entry = by_hanzi.get(hanzi)
        meanings_es = entry["meaningsEs"][:3] if entry else [manual_es[hanzi]]
        words.append({
            "hanzi": hanzi,
            "pinyin": pinyin,
            "meaningsEs": meanings_es,
            "meaningEn": meaning_en or None,
            "section": section,
            "unit": unit,
            "dictionaryId": entry["id"] if entry else None,
            "hskLevel": entry.get("hskLevel") if entry else None,
            "freqRank": entry.get("freqRank") if entry else None,
        })

    words.sort(key=lambda w: (w["section"], w["unit"], w["freqRank"] or 99999))
    characters = sorted({ch for w in words for ch in w["hanzi"]})

    out = {
        "source": "Duolingo, pestaña Caracteres (curso de chino desde inglés)",
        "extractedAt": date.today().isoformat(),
        "progress": args.progress,
        "words": words,
        "characters": characters,
    }
    (DUO / "palabras.json").write_text(
        json.dumps(out, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    in_dict = sum(1 for w in words if w["dictionaryId"])
    print(f"{len(words)} palabras ({in_dict} en dictionary.json), {len(characters)} caracteres")


if __name__ == "__main__":
    main()
