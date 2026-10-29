"""Resumable batch generation of AI content through the local `claude -p` CLI."""
import json
import os
import re
import subprocess
from dataclasses import dataclass, field
from pathlib import Path
from string import Template
from typing import Callable, Literal

from pydantic import BaseModel, ValidationError

from mandarin_pipeline.models import MISSIONS, ReviewResult

Runner = Callable[[str], str]
Kind = Literal["words", "chars", "phrases", "review"]

PROMPTS_DIR = Path(__file__).parent / "prompts"
_FENCE = re.compile(r"^```[a-zA-Z]*\s*\n(.*?)\n?```\s*$", re.DOTALL)
_KEY = {"words": "word", "chars": "char", "review": "id"}


@dataclass
class BatchReport:
    done: int = 0
    skipped: int = 0
    failed: list[int] = field(default_factory=list)


def strip_code_fences(text: str) -> str:
    """Remove a surrounding ```json ... ``` fence, if any."""
    text = text.strip()
    m = _FENCE.match(text)
    return m.group(1).strip() if m else text


def claude_runner(prompt: str) -> str:
    proc = subprocess.run(
        ["claude", "-p", prompt, "--output-format", "json"],
        capture_output=True,
        text=True,
        timeout=600,
        check=True,
    )
    payload = json.loads(proc.stdout)
    if not isinstance(payload, dict) or payload.get("is_error"):
        raise ValueError(f"claude reported an error: {proc.stdout[:500]}")
    result = payload.get("result")
    if not isinstance(result, str):
        raise ValueError(f"claude result is not a string: {proc.stdout[:500]}")
    return strip_code_fences(result)


def _validate(kind: Kind, batch: list[dict], raw: str, model: type[BaseModel]) -> list[dict]:
    """Parse and validate a model response; raise ValueError/ValidationError when invalid."""
    data = json.loads(strip_code_fences(raw))
    if not isinstance(data, list):
        raise ValueError("response is not a JSON array")
    objs = [model.model_validate(o) for o in data]
    key = _KEY.get(kind)
    if key:
        got = [getattr(o, key) for o in objs]
        want = [item[key] for item in batch]
        if len(got) != len(want) or set(got) != set(want):
            raise ValueError(f"{key} mismatch: expected {want}, got {got}")
    else:  # phrases: one item per mission
        if not objs:
            raise ValueError("empty phrase list")
        expected = {item["mission"] for item in batch}
        wrong = {o.mission for o in objs} - expected
        if wrong:
            raise ValueError(f"unexpected missions: {sorted(wrong)}")
    if kind == "review":
        # Bind each verdict to the exact text the pipeline sent, ignoring any model echo.
        hashes = {item["id"]: item["content_hash"] for item in batch}
        objs = [o.model_copy(update={"content_hash": hashes[o.id]}) for o in objs]
    return [o.model_dump(by_alias=False) for o in objs]


def _expected_keys(kind: Kind, batch: list[dict]) -> set[str]:
    return {item[_KEY.get(kind, "mission")] for item in batch}


def _is_done(kind: Kind, batch: list[dict], path: Path) -> bool:
    """A batch file is done only if it parses and covers exactly this batch's items."""
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        key = _KEY.get(kind, "mission")
        got = [o[key] for o in data]
    except (OSError, ValueError, KeyError, TypeError):
        return False
    if kind != "phrases" and len(got) != len(batch):
        return False
    return set(got) == _expected_keys(kind, batch)


def run_batches(
    kind: Kind,
    items: list[dict],
    render_prompt: Callable[[list[dict]], str],
    model: type[BaseModel],
    runner: Runner,
    out_dir: Path,
    batch_size: int = 20,
    first_index: int = 0,
) -> BatchReport:
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    report = BatchReport()
    for idx, start in enumerate(range(0, len(items), batch_size), start=first_index):
        batch = items[start : start + batch_size]
        out = out_dir / f"batch_{idx:03d}.json"
        err = out_dir / f"batch_{idx:03d}.error.txt"
        if out.exists() and _is_done(kind, batch, out):
            report.skipped += 1
            continue
        prompt = render_prompt(batch)
        log: list[str] = []
        result = None
        for attempt in (1, 2):
            raw = ""
            try:
                raw = runner(prompt)
                result = _validate(kind, batch, raw, model)
                break
            except (ValueError, ValidationError, subprocess.SubprocessError, OSError, KeyError) as e:
                diag = ""
                if isinstance(e, subprocess.CalledProcessError):
                    diag = f"STDERR:\n{e.stderr}\nSTDOUT:\n{e.stdout}\n"
                log.append(f"--- attempt {attempt} ---\nERROR: {e}\n{diag}RAW:\n{raw}\n")
        if result is None:
            err.write_text("\n".join(log), encoding="utf-8")
            report.failed.append(idx)
            continue
        tmp = out.with_suffix(".json.tmp")
        tmp.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        os.replace(tmp, out)
        err.unlink(missing_ok=True)
        report.done += 1
    return report


# ---- AI review: append-only batches keyed by (id, content_hash) ----


def load_reviews(review_dir: Path) -> list[ReviewResult]:
    """Every stored review, in batch order (later batches override earlier ones)."""
    out: list[ReviewResult] = []
    for f in sorted(Path(review_dir).glob("batch_*.json")):
        out.extend(ReviewResult.model_validate(x) for x in json.loads(f.read_text(encoding="utf-8")))
    return out


def _next_batch_index(out_dir: Path) -> int:
    indices = [
        int(m.group(1))
        for f in Path(out_dir).glob("batch_*.json")
        if (m := re.fullmatch(r"batch_(\d+)\.json", f.name))
    ]
    return max(indices) + 1 if indices else 0


def run_review(
    items: list[dict],
    render_prompt: Callable[[list[dict]], str],
    runner: Runner,
    out_dir: Path,
    batch_size: int = 25,
    limit: int | None = None,
) -> BatchReport:
    """Review only items with no stored (id, content_hash) verdict, into NEW batch files.

    Existing batch files are never rewritten, so upstream changes do not shift or
    regenerate earlier reviews; regenerated content simply gets reviewed again.
    """
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    done = {(r.id, r.content_hash) for r in load_reviews(out_dir)}
    pending = [i for i in items if (i["id"], i["content_hash"]) not in done][:limit]
    return run_batches(
        "review", pending, render_prompt, ReviewResult, runner, out_dir,
        batch_size=batch_size, first_index=_next_batch_index(out_dir),
    )


# ---- prompt rendering and item building (used by the CLI) ----


def _load_prompt(name: str) -> Template:
    return Template((PROMPTS_DIR / f"{name}.md").read_text(encoding="utf-8"))


def build_word_items(candidates: list[dict], cedict: dict) -> list[dict]:
    items = []
    for c in sorted(candidates, key=lambda c: c["order"]):
        readings = [
            {"index": i, "pinyin": e.pinyin_numbered, "glosses": e.glosses_en}
            for i, e in enumerate(cedict[c["word"]])
        ]
        items.append({"word": c["word"], "order": c["order"], "readings": readings})
    return items


def build_char_items(candidates: list[dict]) -> list[dict]:
    seen: dict[str, None] = {}
    for c in sorted(candidates, key=lambda c: c["order"]):
        for ch in c["word"]:
            if "一" <= ch <= "鿿":
                seen.setdefault(ch)
    return [{"char": ch} for ch in seen]


def build_phrase_items() -> list[dict]:
    return [{"mission": k, "label": v} for k, v in MISSIONS.items()]


def make_word_renderer(all_items: list[dict]) -> Callable[[list[dict]], str]:
    template = _load_prompt("words")

    def render(batch: list[dict]) -> str:
        first = min(i["order"] for i in batch)
        known = " ".join(i["word"] for i in all_items if i["order"] < first) or "(ninguna todavía)"
        lines = []
        for item in batch:
            lines.append(f"Palabra: {item['word']}")
            for r in item["readings"]:
                lines.append(f"  lectura {r['index']}: {r['pinyin']} — {'; '.join(r['glosses'])}")
        return template.substitute(known=known, words="\n".join(lines), count=len(batch))

    return render


def make_char_renderer() -> Callable[[list[dict]], str]:
    template = _load_prompt("chars")
    return lambda batch: template.substitute(
        chars=" ".join(i["char"] for i in batch), count=len(batch)
    )


def make_phrase_renderer() -> Callable[[list[dict]], str]:
    template = _load_prompt("phrases")
    return lambda batch: template.substitute(
        mission=batch[0]["mission"], label=batch[0]["label"]
    )


def make_review_renderer() -> Callable[[list[dict]], str]:
    template = _load_prompt("review")
    return lambda batch: template.substitute(
        items="\n\n".join(f"[{i['id']}]\n{i['text']}" for i in batch), count=len(batch)
    )
