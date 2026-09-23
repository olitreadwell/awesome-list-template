"""GitHub anchor slugs, matching github-slugger, which awesome-lint depends on."""

from __future__ import annotations

import unicodedata

_EMOJI_RANGES = (
    (0x1F000, 0x1FAFF),
    (0x1F1E6, 0x1F1FF),
    (0x2600, 0x27BF),
    (0x2B00, 0x2BFF),
)
_KEPT_PUNCTUATION = "-_"
_STRIPPED = {0x200D}
_VARIATION_SELECTORS = range(0xFE00, 0xFE10)


def github_slug(text: str) -> str:
    """Return the anchor GitHub gives a heading, without deduplication."""
    normalised = "".join(" " if char.isspace() else char for char in text.lower())
    kept = "".join(char for char in normalised if _keep_char(char))
    return kept.replace(" ", "-")


def _keep_char(char: str) -> bool:
    """Keep what GitHub keeps: letters, numbers, emoji, hyphens, underscores, spaces."""
    if char in _KEPT_PUNCTUATION or char.isspace():
        return True
    if ord(char) in _STRIPPED or ord(char) in _VARIATION_SELECTORS:
        return False
    codepoint = ord(char)
    if any(start <= codepoint <= end for start, end in _EMOJI_RANGES):
        return True
    return unicodedata.category(char)[0] in {"L", "N"}


class GithubSlugger:
    """Stateful slugger: repeated headings get -1, -2 suffixes, like GitHub."""

    def __init__(self) -> None:
        self._occurrences: dict[str, int] = {}

    def reset(self) -> None:
        """Forget every slug produced so far."""
        self._occurrences = {}

    def slug(self, text: str) -> str:
        """Return a unique slug for this heading text."""
        result = github_slug(text)
        original = result
        while result in self._occurrences:
            self._occurrences[original] += 1
            result = f"{original}-{self._occurrences[original]}"
        self._occurrences[result] = 0
        return result
