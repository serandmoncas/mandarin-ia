"""CLI entry point: python -m mandarin_pipeline <command>."""
import argparse
import json
import sys
from pathlib import Path

import httpx

from mandarin_pipeline.cedict import parse_cedict
from mandarin_pipeline.generate import (
    build_char_items,
    build_phrase_items,
    build_word_items,
    claude_runner,
    load_reviews,
    make_char_renderer,
    make_phrase_renderer,
    make_review_renderer,
    make_word_renderer,
    run_batches,
    run_review,
)
from mandarin_pipeline.build import (
    Dictionary,
    build_dictionary,
    compute_stats,
    load_manifest,
    now_stamps,
    write_dictionary,
)
from mandarin_pipeline.checks import _load_dir, build_review_items, load_checked_words
from mandarin_pipeline.frequency import top_frequency_words, word_frequency
from mandarin_pipeline.hsk import load_hsk
from mandarin_pipeline.models import CharContent, PhraseContent, WordContent
from mandarin_pipeline.order import Candidate, learning_order, select_candidates, write_candidates
from mandarin_pipeline.sources import download_sources
from mandarin_pipeline.tts import (
    MissingConfig,
    jobs_from_dictionary,
    load_config,
    run_audio,
    synthesize,
    upload,
)

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


def _generate(args: argparse.Namespace) -> None:
    candidates = json.loads((ROOT / "data" / "candidates.json").read_text(encoding="utf-8"))
    out_dir = ROOT / "data" / "generated" / args.kind
    if args.kind == "words":
        with open(SOURCES_DIR / "cedict_ts.txt", encoding="utf-8") as f:
            cedict = parse_cedict(f)
        all_items = build_word_items(candidates, cedict)
        items = all_items[: args.limit]
        render, model, size = make_word_renderer(all_items), WordContent, 20
    elif args.kind == "chars":
        items = build_char_items(candidates)[: args.limit]
        render, model, size = make_char_renderer(), CharContent, 30
    else:
        items = build_phrase_items()[: args.limit]
        render, model, size = make_phrase_renderer(), PhraseContent, 1
    report = run_batches(args.kind, items, render, model, claude_runner, out_dir, batch_size=size)
    print(f"{args.kind}: {len(items)} items; done={report.done} skipped={report.skipped} failed={report.failed}")
    if report.failed:
        print(f"See *.error.txt in {out_dir}")


def _review(args: argparse.Namespace) -> None:
    candidates = json.loads((ROOT / "data" / "candidates.json").read_text(encoding="utf-8"))
    with open(SOURCES_DIR / "cedict_ts.txt", encoding="utf-8") as f:
        cedict = parse_cedict(f)
    items = build_review_items(ROOT / "data" / "generated", cedict, candidates)
    out_dir = ROOT / "data" / "generated" / "review"
    report = run_review(
        items, make_review_renderer(), claude_runner, out_dir, batch_size=25, limit=args.limit
    )
    print(f"review: {len(items)} reviewable items; done={report.done} failed={report.failed}")
    if report.failed:
        print(f"See *.error.txt in {out_dir}")


def _assemble() -> tuple[list[Candidate], Dictionary]:
    data = ROOT / "data"
    rows = json.loads((data / "candidates.json").read_text(encoding="utf-8"))
    candidates = [
        Candidate(r["word"], r["frequency"], r["hskLevel"], r["freqRank"], r["order"]) for r in rows
    ]
    with open(SOURCES_DIR / "cedict_ts.txt", encoding="utf-8") as f:
        cedict = parse_cedict(f)
    gen = data / "generated"
    words = load_checked_words(gen, cedict, {c.word: c.order for c in candidates})
    reviews = load_reviews(gen / "review")
    chars = [CharContent.model_validate(x) for x in _load_dir(gen / "chars")]
    phrases = [PhraseContent.model_validate(x) for x in _load_dir(gen / "phrases")]
    manifest = load_manifest(data / "audio-manifest.json")
    version, stamp = now_stamps()
    return candidates, build_dictionary(
        candidates, words, reviews, chars, phrases, manifest, version, stamp
    )


def _build(args: argparse.Namespace) -> None:
    _, d = _assemble()
    out = ROOT / "data" / "dictionary.json"
    write_dictionary(d, out)
    print(f"Written {out}: {len(d.words)} words, {len(d.characters)} characters, {len(d.phrases)} phrases")


def _stats(args: argparse.Namespace) -> None:
    candidates, d = _assemble()
    for section, counts in compute_stats(candidates, d).items():
        print(f"{section}:")
        for key, n in sorted(counts.items()):
            print(f"  {key}: {n}")


def _audio(args: argparse.Namespace) -> None:
    try:
        cfg = load_config(dotenv_path=ROOT / ".env")
    except MissingConfig as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)
    d = json.loads((ROOT / "data" / "dictionary.json").read_text(encoding="utf-8"))
    jobs = jobs_from_dictionary(d)
    with httpx.Client(timeout=60) as client:
        report = run_audio(
            jobs,
            ROOT / "data" / "audio-manifest.json",
            lambda text, voice: synthesize(
                text, voice, cfg["AZURE_SPEECH_KEY"], cfg["AZURE_SPEECH_REGION"], client
            ),
            lambda path, data: upload(
                path, data, cfg["SUPABASE_URL"], cfg["SUPABASE_SERVICE_ROLE_KEY"], client
            ),
            limit=args.limit,
        )
    print(f"audio: {len(jobs)} jobs; done={report.done} skipped={report.skipped}")
    if report.quota_exhausted:
        print("Cuota de Azure agotada; vuelve a ejecutar `audio` más tarde (se retoma donde quedó).")
    print("Ejecuta `build` para adjuntar los audios al diccionario.")


# Register subcommands here: name -> (help, handler)
COMMANDS = {
    "download": ("Download CC-CEDICT and the HSK list", _download),
    "candidates": ("Compute candidates and learning order", _candidates),
    "generate": ("Generate AI content in resumable batches with claude -p", _generate),
    "build": ("Assemble data/dictionary.json", _build),
    "stats": ("Counts by status, flag and HSK level", _stats),
    "audio": ("Synthesize audio with Azure TTS and upload it to Supabase Storage", _audio),
    "review": ("Second AI review pass over content that passed the automatic checks", _review),
}


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(prog="mandarin_pipeline")
    sub = parser.add_subparsers(dest="command", required=True)
    for name, (help_text, handler) in COMMANDS.items():
        p = sub.add_parser(name, help=help_text)
        p.set_defaults(handler=handler)
        if name == "generate":
            p.add_argument("kind", choices=["words", "chars", "phrases"])
        if name in ("generate", "review", "audio"):
            p.add_argument("--limit", type=int, default=None, help="Process at most N items (audio: new jobs only)")
    args = parser.parse_args(argv)
    args.handler(args)


if __name__ == "__main__":
    main()
