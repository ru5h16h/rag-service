from __future__ import annotations

from src.retrieval.preprocess import is_empty_query, normalize_query


def test_normalize_query_is_idempotent() -> None:
    once = normalize_query("  Refund   a\tCharge\n")
    twice = normalize_query(once)
    assert once == twice


def test_normalize_query_lowercases_and_collapses_whitespace() -> None:
    assert normalize_query("  How  Do\tI\nrefund? ") == "how do i refund?"


def test_normalize_query_nfkc_normalizes() -> None:
    # Fullwidth characters (U+FF21...) collapse to ASCII under NFKC, then lowercase.
    assert normalize_query("ＡＢＣ") == "abc"


def test_is_empty_query_true_for_whitespace() -> None:
    assert is_empty_query("   \t\n ") is True


def test_is_empty_query_false_for_real_query() -> None:
    assert is_empty_query("refund a charge") is False
