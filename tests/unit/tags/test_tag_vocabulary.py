"""Tag matching: glyphs, bare labels, backticks, and unknown labels."""

from __future__ import annotations

from awesome_list.parse.readme_model import ListTag
from awesome_list.tags import DEFAULT_TAG_VOCABULARY

VOCABULARY = DEFAULT_TAG_VOCABULARY


def test_matches_glyph_and_label() -> None:
    match = VOCABULARY.match_leading("▦ Data - what it holds.")

    assert match.tag == ListTag(axis="type", label="Data")
    assert match.remainder == "what it holds."


def test_matches_bare_label() -> None:
    match = VOCABULARY.match_leading("Open - no glyph needed.")

    assert match.tag == ListTag(axis="access", label="Open")
    assert match.remainder == "no glyph needed."


def test_matches_backticked_tag() -> None:
    match = VOCABULARY.match_leading("`⇄ API` - a backticked tag.")

    assert match.tag == ListTag(axis="type", label="API")
    assert match.remainder == "a backticked tag."


def test_unknown_label_on_a_known_glyph_is_reported() -> None:
    match = VOCABULARY.match_leading("▦ Database - an unknown label.")

    assert match.tag is None
    assert (match.axis, match.label) == ("type", "Database")
    assert match.remainder == "an unknown label."


def test_plain_description_matches_nothing() -> None:
    match = VOCABULARY.match_leading("just a description.")

    assert match.tag is None
    assert match.axis is None
    assert match.remainder == "just a description."


def test_empty_text_matches_nothing() -> None:
    match = VOCABULARY.match_leading("   ")

    assert match.tag is None
    assert match.remainder == ""


def test_labels_for_axis() -> None:
    assert VOCABULARY.labels_for("access") == ("Open", "Key", "Login", "Paid")


def test_default_vocabulary_axes_are_complete() -> None:
    axes = dict(VOCABULARY.axes())

    assert set(axes) == {"type", "access", "status"}
    assert axes["type"][0] == ("API", "⇄")


def test_unclosed_backtick_is_not_unwrapped() -> None:
    match = VOCABULARY.match_leading("`Data - an unclosed backtick.")

    assert match.tag is None
    assert match.remainder == "`Data - an unclosed backtick."


def test_label_must_be_followed_by_a_separator() -> None:
    match = VOCABULARY.match_leading("Database stuff - not a tag.")

    assert match.tag is None
    assert match.axis is None
