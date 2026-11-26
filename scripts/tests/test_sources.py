import gzip

import pytest

from mandarin_pipeline import sources


def _fake_fetch(calls, fail_after_partial=False):
    def fetch(url, target):
        calls.append(url)
        if url == sources.CEDICT_URL:
            target.write_bytes(gzip.compress(b"# cedict\n"))
        else:
            target.write_bytes(b"[]")
        if fail_after_partial and url == sources.HSK_URL:
            target.write_bytes(b"[")
            raise RuntimeError("interrupted")

    return fetch


def test_interrupted_download_leaves_no_final_file_and_retries(tmp_path, monkeypatch):
    calls = []
    monkeypatch.setattr(sources, "_fetch", _fake_fetch(calls, fail_after_partial=True))
    with pytest.raises(RuntimeError):
        sources.download_sources(tmp_path)
    assert not (tmp_path / sources.HSK_FILE).exists()
    assert not list(tmp_path.glob("*.part"))

    calls.clear()
    monkeypatch.setattr(sources, "_fetch", _fake_fetch(calls))
    sources.download_sources(tmp_path)
    assert calls == [sources.HSK_URL]  # cedict already complete, hsk re-fetched
    assert (tmp_path / sources.HSK_FILE).read_bytes() == b"[]"


def test_failed_gunzip_leaves_no_final_file(tmp_path, monkeypatch):
    monkeypatch.setattr(sources, "_fetch", lambda url, t: t.write_bytes(b"not gzip"))
    with pytest.raises(Exception):
        sources.download_sources(tmp_path)
    assert not (tmp_path / sources.CEDICT_FILE).exists()
    assert not list(tmp_path.iterdir())


def test_existing_files_are_not_refetched(tmp_path, monkeypatch):
    (tmp_path / sources.CEDICT_FILE).write_text("x")
    (tmp_path / sources.HSK_FILE).write_text("[]")
    calls = []
    monkeypatch.setattr(sources, "_fetch", _fake_fetch(calls))
    sources.download_sources(tmp_path)
    assert calls == []
