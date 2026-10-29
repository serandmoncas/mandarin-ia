"""CLI entry point: python -m mandarin_pipeline <command>."""
import argparse
from pathlib import Path

from mandarin_pipeline.sources import download_sources

ROOT = Path(__file__).resolve().parents[2]
SOURCES_DIR = ROOT / "data" / "sources"


def _download(args: argparse.Namespace) -> None:
    download_sources(SOURCES_DIR)
    print(f"Sources ready in {SOURCES_DIR}")


# Register subcommands here: name -> (help, handler)
COMMANDS = {
    "download": ("Download CC-CEDICT and the HSK list", _download),
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
