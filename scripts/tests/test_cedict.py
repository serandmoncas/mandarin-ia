from pathlib import Path

from mandarin_pipeline.cedict import parse_cedict

FIXTURE = Path(__file__).parent / "fixtures" / "cedict_sample.txt"


def test_parse_cedict_multiple_readings():
    result = parse_cedict(FIXTURE.read_text(encoding="utf-8").splitlines())
    assert len(result["行"]) == 2
    assert {e.pinyin_numbered for e in result["行"]} == {"xing2", "hang2"}


def test_parse_cedict_umlaut():
    result = parse_cedict(FIXTURE.read_text(encoding="utf-8").splitlines())
    assert result["女"][0].pinyin_numbered == "nv3"
    assert result["女"][0].glosses_en == ["woman"]


def test_parse_cedict_ignores_comments_and_lowercases():
    result = parse_cedict(["# c", "北京 北京 [Bei3 jing1] /Beijing/"])
    assert result["北京"][0].pinyin_numbered == "bei3 jing1"
