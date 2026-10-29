"""Download raw data sources into data/sources/ (idempotent)."""
import gzip
import shutil
from pathlib import Path

import httpx

CEDICT_URL = "https://www.mdbg.net/chinese/export/cedict/cedict_1_0_ts_utf-8_mdbg.txt.gz"
HSK_URL = "https://raw.githubusercontent.com/drkameleon/complete-hsk-vocabulary/main/complete.json"
CEDICT_FILE = "cedict_ts.txt"
HSK_FILE = "complete.json"


def _fetch(url: str, target: Path) -> None:
    with httpx.stream("GET", url, follow_redirects=True, timeout=120) as r:
        r.raise_for_status()
        with target.open("wb") as f:
            for chunk in r.iter_bytes():
                f.write(chunk)


def download_sources(dest: Path) -> None:
    dest.mkdir(parents=True, exist_ok=True)
    cedict = dest / CEDICT_FILE
    if not cedict.exists():
        gz = dest / (CEDICT_FILE + ".gz")
        _fetch(CEDICT_URL, gz)
        with gzip.open(gz, "rb") as src, cedict.open("wb") as out:
            shutil.copyfileobj(src, out)
        gz.unlink()
    hsk = dest / HSK_FILE
    if not hsk.exists():
        _fetch(HSK_URL, hsk)
