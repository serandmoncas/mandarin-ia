from pathlib import Path

from mandarin_pipeline.hsk import load_hsk

FIXTURE = Path(__file__).parent / "fixtures" / "hsk_sample.json"


def test_load_hsk_lowest_level():
    levels = load_hsk(FIXTURE)
    assert levels["爱好"] == 1
    assert levels["高级"] == 7


def test_load_hsk_ignores_old_levels():
    assert "旧词" not in load_hsk(FIXTURE)


def test_load_hsk_duplicate_word_takes_minimum(tmp_path):
    import json

    f = tmp_path / "h.json"
    f.write_text(
        json.dumps([
            {"simplified": "好", "level": ["new-3"]},
            {"simplified": "好", "level": ["new-1"]},
            {"simplified": "好", "level": ["new-5"]},
        ]),
        encoding="utf-8",
    )
    assert load_hsk(f)["好"] == 1
