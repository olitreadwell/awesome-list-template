"""Tag vocabulary: the labels and glyphs a list may use."""

from __future__ import annotations

from dataclasses import dataclass

from awesome_list.parse.readme_model import ListTag

DEFAULT_TAG_VOCABULARY: TagVocabulary


@dataclass(frozen=True, slots=True)
class TagMatch:
    """The result of looking for one tag at the start of a string."""

    remainder: str
    tag: ListTag | None = None
    axis: str | None = None
    label: str | None = None


@dataclass(frozen=True, slots=True)
class TagVocabulary:
    """The configured tags, grouped by axis, in file order."""

    type: tuple[tuple[str, str], ...] = ()
    access: tuple[tuple[str, str], ...] = ()
    status: tuple[tuple[str, str], ...] = ()

    def axes(self) -> tuple[tuple[str, tuple[tuple[str, str], ...]], ...]:
        """Return (axis, labels) pairs in a stable order."""
        return (("type", self.type), ("access", self.access), ("status", self.status))

    def labels_for(self, axis: str) -> tuple[str, ...]:
        """Return the labels configured for one axis."""
        return tuple(label for label, _glyph in dict(self.axes())[axis])

    def match_leading(self, text: str) -> TagMatch:
        """Match one tag at the start of a description tail.

        Recognises "glyph label", a bare label, and both of those wrapped in
        backticks. A known glyph with an unknown label comes back as axis plus
        label with tag=None, so the vocabulary rule can report it.
        """
        stripped = text.strip()
        if not stripped:
            return TagMatch(remainder="")

        inner, wrapped = _unwrap_backticks(stripped)
        for axis, pairs in self.axes():
            for label, glyph in pairs:
                for candidate in (f"{glyph} {label}", label):
                    if inner.lower().startswith(candidate.lower()):
                        after = inner[len(candidate) :]
                        if after and after[0] not in " -\u2013\u2014:":
                            continue
                        return TagMatch(
                            remainder=_strip_separator(after),
                            tag=ListTag(axis=axis, label=label),
                        )
            for _label, glyph in pairs:
                if inner.startswith(f"{glyph} "):
                    word = inner[len(glyph) + 1 :].split(" ", 1)[0]
                    after = inner[len(glyph) + 1 + len(word) :]
                    return TagMatch(
                        remainder=_strip_separator(after),
                        axis=axis,
                        label=word.strip(".,;:"),
                    )
        del wrapped
        return TagMatch(remainder=stripped)


def _unwrap_backticks(text: str) -> tuple[str, bool]:
    if text.startswith("`"):
        end = text.find("`", 1)
        if end != -1:
            inner = text[1:end]
            return inner + text[end + 1 :], True
    return text, False


def _strip_separator(text: str) -> str:
    remainder = text.lstrip()
    while remainder[:1] in {"-", "\u2013", "\u2014", ":"}:
        remainder = remainder[1:].lstrip()
    return remainder


DEFAULT_TAG_VOCABULARY = TagVocabulary(
    type=(
        ("API", "⇄"),
        ("Data", "▦"),
        ("Portal", "☰"),
        ("Register", "☑"),
        ("Docs", "¶"),
    ),
    access=(("Open", "○"), ("Key", "◑"), ("Login", "◕"), ("Paid", "●")),
    status=(("Legacy", "⟳"), ("Archived", "▣")),
)
