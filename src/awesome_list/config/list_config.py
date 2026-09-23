"""Typed configuration, loaded from awesome.toml."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from awesome_list.tags import DEFAULT_TAG_VOCABULARY, TagVocabulary

ARCHIVE_MODES = ("off", "local", "wayback")


@dataclass(frozen=True, slots=True)
class SiteConfig:
    """Whether the optional site and its gate extensions are on."""

    enabled: bool = False


@dataclass(frozen=True, slots=True)
class SourcesConfig:
    """Upstream lists to mine for candidates. Mining never writes an entry."""

    lists: tuple[str, ...] = ()
    keywords: tuple[str, ...] = ()
    report: str = "reports/source-candidates.md"


@dataclass(frozen=True, slots=True)
class GithubConfig:
    """Whether GitHub links carry stars and activity, and how fresh that is."""

    stats: bool = True
    max_age_days: int = 14
    snapshot: str = "github-stats.json"


@dataclass(frozen=True, slots=True)
class LinksConfig:
    """How dead entries are handled."""

    archive: str = "off"
    exclude: tuple[str, ...] = ()
    allowlist: tuple[str, ...] = ()
    per_file_bytes: int = 2_000_000
    total_bytes: int = 50_000_000


@dataclass(frozen=True, slots=True)
class ListConfig:
    """Everything the engine needs beyond the readme."""

    name: str
    repo_slug: str
    sections: tuple[str, ...]
    readme: str = "readme.md"
    badge: str = "default"
    site: SiteConfig = SiteConfig()
    links: LinksConfig = LinksConfig()
    github: GithubConfig = GithubConfig()
    sources: SourcesConfig = SourcesConfig()
    tags: TagVocabulary = DEFAULT_TAG_VOCABULARY
    source_path: Path = Path("awesome.toml")
