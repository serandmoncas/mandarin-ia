"""HSK 3.0 word list loader (complete-hsk-vocabulary complete.json)."""
import json
from pathlib import Path


def load_hsk(path: Path) -> dict[str, int]:
    """Map simplified word -> lowest HSK 3.0 level (`new-N` tags only)."""
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    levels: dict[str, int] = {}
    for item in data:
        new = [int(t[4:]) for t in item.get("level", []) if t.startswith("new-")]
        if new:
            word = item["simplified"]
            levels[word] = min(levels.get(word, 99), min(new))
    return levels
