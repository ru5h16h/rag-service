from __future__ import annotations

from src.utils.cleaning import normalize_unicode, normalize_whitespace, strip_boilerplate


def test_normalize_whitespace_is_idempotent() -> None:
    text = "  First   line \n\n\n Second\t\tline  \n\n Third   line "

    once = normalize_whitespace(text)
    twice = normalize_whitespace(once)

    assert once == "First line\n\nSecond line\n\nThird line"
    assert twice == once


def test_strip_boilerplate_removes_default_patterns() -> None:
    text = "\n".join(
        [
            "Useful content",
            "Page 3 of 42",
            "Copyright",
            "© 2024 Example Corp",
            "All rights reserved",
            "---",
            "Still useful",
        ]
    )

    cleaned = strip_boilerplate(text)

    assert "Page 3 of 42" not in cleaned
    assert "© 2024 Example Corp" not in cleaned
    assert "All rights reserved" not in cleaned
    assert "---" not in cleaned
    assert "Useful content" in cleaned
    assert "Still useful" in cleaned


def test_normalize_unicode_replaces_typographic_characters() -> None:
    text = "\u2018hello\u2019 \u201cworld\u201d\u2014test\u00a0value"

    normalized = normalize_unicode(text)

    assert normalized == "'hello' \"world\"-test value"
