from mandarin_pipeline import frequency
from mandarin_pipeline.cedict import CedictEntry
from mandarin_pipeline.frequency import is_han_word, top_frequency_words


def test_is_han_word():
    assert is_han_word("你好")
    assert not is_han_word("ok")
    assert not is_han_word("")
    assert not is_han_word("，")


def test_top_frequency_filters_junk(monkeypatch):
    monkeypatch.setattr(
        frequency, "_top_n_list", lambda n: ["的", "ok", "123", "，", "张三", "我"]
    )
    cedict = {
        "的": [CedictEntry("的", "的", "de5", ["of"])],
        "我": [CedictEntry("我", "我", "wo3", ["I"])],
    }
    assert top_frequency_words(6, cedict) == ["的", "我"]
