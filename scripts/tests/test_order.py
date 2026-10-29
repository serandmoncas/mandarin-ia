from mandarin_pipeline.order import Candidate, learning_order, select_candidates


def _freq(table):
    return lambda w: table.get(w, 0.0)


def test_includes_all_hsk_up_to_max_level():
    hsk = {"a": 1, "b": 3, "c": 4}
    cedict = {w: [] for w in "abcdef"}
    freq = _freq({"c": 0.9, "a": 0.1, "b": 0.1, "d": 0.5})
    cands, _ = select_candidates(hsk, cedict, ["c", "d"], freq, max_level=3, total=2)
    words = {c.word for c in cands}
    assert {"a", "b"} <= words
    assert "c" not in words


def test_fills_to_total_with_frequent_words():
    hsk = {"a": 1}
    cedict = {w: [] for w in "abcdef"}
    cands, _ = select_candidates(hsk, cedict, list("bcdef"), _freq({}), total=4)
    assert len(cands) == 4
    assert cands[0].hsk_level == 1


def test_missing_hsk_word_is_warning():
    hsk = {"a": 1, "zz": 2}
    cedict = {"a": []}
    cands, warnings = select_candidates(hsk, cedict, ["a"], _freq({}), total=5)
    assert "zz" in warnings
    assert "zz" not in {c.word for c in cands}


def test_rare_hsk1_word_pulled_forward():
    cands = [Candidate(f"w{i}", 1.0 - i / 1000, None) for i in range(100)]
    cands.append(Candidate("rare", 1e-12, 1))
    ordered = {c.word: c for c in learning_order(cands)}
    assert ordered["rare"].freq_rank == 101
    assert ordered["rare"].order <= 2


def test_frequent_non_hsk_stays_early():
    cands = [Candidate("top", 0.9, None), Candidate("x", 0.1, 1), Candidate("y", 0.05, 2)]
    ordered = {c.word: c for c in learning_order(cands)}
    assert ordered["top"].order == 1


def test_order_is_dense_1_based():
    cands = [Candidate(f"w{i}", 1.0 / (i + 1), 1 if i % 3 == 0 else None) for i in range(50)]
    result = learning_order(cands)
    assert sorted(c.order for c in result) == list(range(1, 51))
    assert [c.order for c in result] == list(range(1, 51))
