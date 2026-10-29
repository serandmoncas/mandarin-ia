"""CLI entry point: python -m mandarin_pipeline <command>."""
import argparse
from pathlib import Path

from mandarin_pipeline.cedict import parse_cedict
from mandarin_pipeline.frequency import top_frequency_words, word_frequency
from mandarin_pipeline.hsk import load_hsk
from mandarin_pipeline.order import learning_order, select_candidates, write_candidates
from mandarin_pipeline.sources import download_sources

ROOT = Path(__file__).resolve().parents[2]
SOURCES_DIR = ROOT / "data" / "sources"


def _download(args: argparse.Namespace) -> None:
    download_sources(SOURCES_DIR)
    print(f"Sources ready in {SOURCES_DIR}")


def _candidates(args: argparse.Namespace) -> None:
    total, max_level = 2500, 3
    with open(SOURCES_DIR / "cedict_ts.txt", encoding="utf-8") as f:
        cedict = parse_cedict(f)
    hsk = load_hsk(SOURCES_DIR / "complete.json")
    freq_words = top_frequency_words(total * 2, cedict)
    cands, warnings = select_candidates(
        hsk, cedict, freq_words, word_frequency, max_level=max_level, total=total
    )
    ordered = learning_order(cands)
    out = ROOT / "data" / "candidates.json"
    write_candidates(ordered, out)
    print(f"Total candidates: {len(ordered)}")
    for level in range(1, max_level + 1):
        print(f"HSK {level}: {sum(c.hsk_level == level for c in ordered)}")
    print(f"Non-HSK: {sum(c.hsk_level is None for c in ordered)}")
    print(f"Warnings (HSK words missing from CEDICT): {len(warnings)}")
    for w in warnings:
        print(f"  - {w}")
    print("First 30: " + " ".join(c.word for c in ordered[:30]))
    print(f"Written to {out}")


# Register subcommands here: name -> (help, handler)
COMMANDS = {
    "download": ("Download CC-CEDICT and the HSK list", _download),
    "candidates": ("Compute candidates and learning order", _candidates),
}


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(prog="mandarin_pipeline")
    sub = parser.add_subparsers(dest="command", required=True)
    for name, (help_text, handler) in COMMANDS.items():
        sub.add_parser(name, help=help_text).set_defaults(handler=handler)
    args = parser.parse_args(argv)
    args.handler(args)


if __name__ == "__main__":
    main()
