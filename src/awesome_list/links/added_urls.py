"""The URLs one version of a readme has that an earlier version did not."""

from __future__ import annotations

from awesome_list.parse.parse_readme import parse_readme


def added_urls(new_text: str, base_text: str) -> tuple[str, ...]:
    """Return the entry URLs added since ``base_text``, in document order."""
    known = set(_normalized_urls(base_text))
    added: list[str] = []
    for url in (entry.url for entry in parse_readme(new_text).entries):
        key = _normalize(url)
        if key in known:
            continue
        known.add(key)
        added.append(url)
    return tuple(added)


def _normalized_urls(text: str) -> frozenset[str]:
    return frozenset(_normalize(entry.url) for entry in parse_readme(text).entries)


def _normalize(url: str) -> str:
    """Ignore the differences that do not make two links different links."""
    return url.strip().rstrip("/").removeprefix("http://").removeprefix("https://")
