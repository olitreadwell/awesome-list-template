"""Read awesome.toml into a typed config, rejecting anything unexpected."""

from __future__ import annotations

import tomllib
from pathlib import Path
from typing import Any

from awesome_list.config.list_config import (
    ARCHIVE_MODES,
    GithubConfig,
    LinksConfig,
    ListConfig,
    SiteConfig,
    SourcesConfig,
    StructureConfig,
)
from awesome_list.tags import DEFAULT_TAG_VOCABULARY, TagVocabulary

TOP_LEVEL_KEYS = {
    "name",
    "repo_slug",
    "badge",
    "readme",
    "sections",
    "site",
    "links",
    "github",
    "sources",
    "structure",
    "tags",
}
LINKS_KEYS = {"archive", "exclude", "allowlist", "archive_limits"}
GITHUB_KEYS = {"stats", "max_age_days", "snapshot"}
SOURCES_KEYS = {"lists", "keywords", "report"}
STRUCTURE_KEYS = {"nested_details"}
LIMIT_KEYS = {"per_file_bytes", "total_bytes"}
TAG_AXES = ("type", "access", "status")


class ListConfigError(ValueError):
    """Raised when awesome.toml is missing something or says something odd."""


def load_list_config(path: Path) -> ListConfig:
    """Load and validate a config file."""
    if not path.exists():
        raise ListConfigError(f"cannot read config: {path} does not exist")
    try:
        raw = tomllib.loads(path.read_text(encoding="utf-8"))
    except tomllib.TOMLDecodeError as error:
        raise ListConfigError(f"cannot read config: {path}: {error}") from error

    unknown = sorted(set(raw) - TOP_LEVEL_KEYS)
    if unknown:
        raise ListConfigError(f"unknown key: {unknown[0]}")

    for key in ("name", "repo_slug", "sections"):
        if key not in raw:
            raise ListConfigError(f"missing required key: {key}")

    sections = _string_tuple(raw["sections"], "sections")
    if not sections:
        raise ListConfigError("sections must not be empty")

    return ListConfig(
        name=_as_str(raw["name"], "name"),
        repo_slug=_as_str(raw["repo_slug"], "repo_slug"),
        sections=sections,
        readme=_as_str(raw.get("readme", "readme.md"), "readme"),
        badge=_as_str(raw.get("badge", "default"), "badge"),
        site=_load_site(raw.get("site", {})),
        links=_load_links(raw.get("links", {})),
        github=_load_github(raw.get("github", {})),
        sources=_load_sources(raw.get("sources", {})),
        structure=_load_structure(raw.get("structure", {})),
        tags=_load_tags(raw.get("tags", {}), present="tags" in raw),
        source_path=path,
    )


def _load_site(raw: Any) -> SiteConfig:
    if not isinstance(raw, dict):
        raise ListConfigError("site must be a table")
    unknown = sorted(set(raw) - {"enabled"})
    if unknown:
        raise ListConfigError(f"unknown key: site.{unknown[0]}")
    enabled = raw.get("enabled", False)
    if not isinstance(enabled, bool):
        raise ListConfigError("site.enabled must be true or false")
    return SiteConfig(enabled=enabled)


def _load_links(raw: Any) -> LinksConfig:
    if not isinstance(raw, dict):
        raise ListConfigError("links must be a table")
    unknown = sorted(set(raw) - LINKS_KEYS)
    if unknown:
        raise ListConfigError(f"unknown key: links.{unknown[0]}")

    archive = _as_str(raw.get("archive", "off"), "links.archive")
    if archive not in ARCHIVE_MODES:
        allowed = ", ".join(f'"{mode}"' for mode in ARCHIVE_MODES)
        raise ListConfigError(
            f"links.archive must be one of {allowed}, got {archive!r}"
        )

    limits = raw.get("archive_limits", {})
    if not isinstance(limits, dict):
        raise ListConfigError("links.archive_limits must be a table")
    unknown_limits = sorted(set(limits) - LIMIT_KEYS)
    if unknown_limits:
        raise ListConfigError(f"unknown key: links.archive_limits.{unknown_limits[0]}")

    return LinksConfig(
        archive=archive,
        exclude=_string_tuple(raw.get("exclude", []), "links.exclude"),
        allowlist=_string_tuple(raw.get("allowlist", []), "links.allowlist"),
        per_file_bytes=_as_int(
            limits.get("per_file_bytes", 2_000_000),
            "links.archive_limits.per_file_bytes",
        ),
        total_bytes=_as_int(
            limits.get("total_bytes", 50_000_000), "links.archive_limits.total_bytes"
        ),
    )


def _load_github(raw: Any) -> GithubConfig:
    if not isinstance(raw, dict):
        raise ListConfigError("github must be a table")
    unknown = sorted(set(raw) - GITHUB_KEYS)
    if unknown:
        raise ListConfigError(f"unknown key: github.{unknown[0]}")

    stats = raw.get("stats", True)
    if not isinstance(stats, bool):
        raise ListConfigError("github.stats must be true or false")

    return GithubConfig(
        stats=stats,
        max_age_days=_as_int(raw.get("max_age_days", 14), "github.max_age_days"),
        snapshot=_as_str(raw.get("snapshot", "github-stats.json"), "github.snapshot"),
    )


def _load_sources(raw: Any) -> SourcesConfig:
    if not isinstance(raw, dict):
        raise ListConfigError("sources must be a table")
    unknown = sorted(set(raw) - SOURCES_KEYS)
    if unknown:
        raise ListConfigError(f"unknown key: sources.{unknown[0]}")

    return SourcesConfig(
        lists=_string_tuple(raw.get("lists", []), "sources.lists"),
        keywords=_string_tuple(raw.get("keywords", []), "sources.keywords"),
        report=_as_str(
            raw.get("report", "reports/source-candidates.md"), "sources.report"
        ),
    )


def _load_structure(raw: Any) -> StructureConfig:
    if not isinstance(raw, dict):
        raise ListConfigError("structure must be a table")
    unknown = sorted(set(raw) - STRUCTURE_KEYS)
    if unknown:
        raise ListConfigError(f"unknown key: structure.{unknown[0]}")

    nested_details = raw.get("nested_details", False)
    if not isinstance(nested_details, bool):
        raise ListConfigError("structure.nested_details must be true or false")

    return StructureConfig(nested_details=nested_details)


def _load_tags(raw: Any, *, present: bool = False) -> TagVocabulary:
    if not isinstance(raw, dict):
        raise ListConfigError("tags must be a table")
    unknown = sorted(set(raw) - set(TAG_AXES))
    if unknown:
        raise ListConfigError(f"unknown key: tags.{unknown[0]}")
    pairs: dict[str, tuple[tuple[str, str], ...]] = {}
    for axis in TAG_AXES:
        table = raw.get(axis, {})
        if not isinstance(table, dict):
            raise ListConfigError(f"tags.{axis} must be a table")
        entries: list[tuple[str, str]] = []
        for label, glyph in table.items():
            entries.append(
                (
                    _as_str(label, f"tags.{axis} label"),
                    _as_str(glyph, f"tags.{axis}.{label}"),
                )
            )
        pairs[axis] = tuple(entries)
    if not any(pairs.values()):
        # An explicit [tags] table with no axes is how a list says it does not
        # use tags at all. Leaving the section out keeps the example vocabulary.
        if present:
            return TagVocabulary()
        return DEFAULT_TAG_VOCABULARY
    return TagVocabulary(
        type=pairs["type"], access=pairs["access"], status=pairs["status"]
    )


def _as_str(value: Any, key: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ListConfigError(f"{key} must be a non-empty string")
    return value


def _as_int(value: Any, key: str) -> int:
    if not isinstance(value, int) or isinstance(value, bool) or value < 0:
        raise ListConfigError(f"{key} must be a positive whole number")
    return value


def _string_tuple(value: Any, key: str) -> tuple[str, ...]:
    if not isinstance(value, list):
        raise ListConfigError(f"{key} must be a list of strings")
    return tuple(_as_str(item, key) for item in value)
