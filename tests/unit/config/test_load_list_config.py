"""Tests for loading awesome.toml."""

from __future__ import annotations

from pathlib import Path

import pytest

from awesome_list.config.load_list_config import ListConfigError, load_list_config

MINIMAL = """\
name = "Awesome Minimal"
repo_slug = "awesome-minimal"
sections = ["Tools"]
"""


def write(tmp_path: Path, body: str) -> Path:
    path = tmp_path / "awesome.toml"
    path.write_text(body, encoding="utf-8")
    return path


def test_loads_minimal_config_with_defaults(tmp_path: Path) -> None:
    config = load_list_config(write(tmp_path, MINIMAL))

    assert config.name == "Awesome Minimal"
    assert config.repo_slug == "awesome-minimal"
    assert config.sections == ("Tools",)
    assert config.readme == "readme.md"
    assert config.site.enabled is False
    assert config.links.archive == "off"
    assert config.links.per_file_bytes == 2_000_000
    assert config.source_path.name == "awesome.toml"


def test_reads_site_links_and_limits(tmp_path: Path) -> None:
    body = (
        MINIMAL
        + """
[site]
enabled = true

[links]
archive = "local"
exclude = ["example.com"]
allowlist = ["slow.example.com"]

[links.archive_limits]
per_file_bytes = 1000
total_bytes = 2000
"""
    )
    config = load_list_config(write(tmp_path, body))

    assert config.site.enabled is True
    assert config.links.archive == "local"
    assert config.links.exclude == ("example.com",)
    assert config.links.allowlist == ("slow.example.com",)
    assert config.links.per_file_bytes == 1000
    assert config.links.total_bytes == 2000


def test_reads_tag_vocabulary(tmp_path: Path) -> None:
    body = (
        MINIMAL
        + """
[tags.type]
API = "\u21c4"

[tags.access]
Open = "\u25cb"

[tags.status]
Legacy = "\u27f3"
"""
    )
    config = load_list_config(write(tmp_path, body))

    assert config.tags.type == (("API", "\u21c4"),)
    assert config.tags.access == (("Open", "\u25cb"),)
    assert config.tags.status == (("Legacy", "\u27f3"),)


def test_github_stats_default_on(tmp_path: Path) -> None:
    config = load_list_config(write(tmp_path, MINIMAL))

    assert config.github.stats is True
    assert config.github.max_age_days == 14
    assert config.github.snapshot == "github-stats.json"


def test_reads_github_section(tmp_path: Path) -> None:
    body = (
        MINIMAL
        + """
[github]
stats = false
max_age_days = 30
snapshot = "s.json"
"""
    )

    config = load_list_config(write(tmp_path, body))

    assert config.github.stats is False
    assert config.github.max_age_days == 30
    assert config.github.snapshot == "s.json"


def test_sources_default_to_nothing(tmp_path: Path) -> None:
    config = load_list_config(write(tmp_path, MINIMAL))

    assert config.sources.lists == ()
    assert config.sources.keywords == ()
    assert config.sources.report == "reports/source-candidates.md"


def test_reads_sources_section(tmp_path: Path) -> None:
    body = (
        MINIMAL
        + """
[sources]
lists = ["https://upstream.test/list.md"]
keywords = ["new zealand"]
report = "reports/mine.md"
"""
    )

    config = load_list_config(write(tmp_path, body))

    assert config.sources.lists == ("https://upstream.test/list.md",)
    assert config.sources.keywords == ("new zealand",)
    assert config.sources.report == "reports/mine.md"


def test_rejects_unknown_sources_key(tmp_path: Path) -> None:
    body = MINIMAL + '[sources]\nmode = "mine"\n'

    with pytest.raises(ListConfigError, match=r"unknown key: sources\.mode"):
        load_list_config(write(tmp_path, body))


def test_rejects_unknown_github_key(tmp_path: Path) -> None:
    body = MINIMAL + "[github]\nstars = true\n"

    with pytest.raises(ListConfigError, match=r"unknown key: github\.stars"):
        load_list_config(write(tmp_path, body))


def test_rejects_non_boolean_github_stats(tmp_path: Path) -> None:
    body = MINIMAL + '[github]\nstats = "yes"\n'

    with pytest.raises(ListConfigError, match=r"github\.stats must be true or false"):
        load_list_config(write(tmp_path, body))


def test_rejects_unknown_top_level_key(tmp_path: Path) -> None:
    body = MINIMAL + "extra_section = 1\n"

    with pytest.raises(ListConfigError, match="unknown key: extra_section"):
        load_list_config(write(tmp_path, body))


def test_rejects_unknown_links_key(tmp_path: Path) -> None:
    body = MINIMAL + '[links]\nmode = "local"\n'

    with pytest.raises(ListConfigError, match=r"unknown key: links\.mode"):
        load_list_config(write(tmp_path, body))


def test_rejects_missing_required_keys(tmp_path: Path) -> None:
    with pytest.raises(ListConfigError, match="missing required key: name"):
        load_list_config(write(tmp_path, 'repo_slug = "x"\nsections = ["A"]\n'))

    with pytest.raises(ListConfigError, match="missing required key: repo_slug"):
        load_list_config(write(tmp_path, 'name = "X"\nsections = ["A"]\n'))

    with pytest.raises(ListConfigError, match="missing required key: sections"):
        load_list_config(write(tmp_path, 'name = "X"\nrepo_slug = "y"\n'))


def test_rejects_empty_sections(tmp_path: Path) -> None:
    body = 'name = "X"\nrepo_slug = "y"\nsections = []\n'

    with pytest.raises(ListConfigError, match="sections must not be empty"):
        load_list_config(write(tmp_path, body))


def test_rejects_unknown_archive_mode(tmp_path: Path) -> None:
    body = MINIMAL + '[links]\narchive = "tape"\n'

    with pytest.raises(ListConfigError, match="archive must be one of"):
        load_list_config(write(tmp_path, body))


def test_missing_file_raises(tmp_path: Path) -> None:
    with pytest.raises(ListConfigError, match="cannot read"):
        load_list_config(tmp_path / "nope.toml")


def test_repository_config_loads(repo_root: Path) -> None:
    config = load_list_config(repo_root / "awesome.toml")

    assert config.site.enabled is False
    assert config.links.archive == "off"
    assert config.github.stats is True
    assert config.sections


def test_accepts_wayback_archive_mode(tmp_path: Path) -> None:
    body = MINIMAL + '[links]\narchive = "wayback"\n'

    assert load_list_config(write(tmp_path, body)).links.archive == "wayback"


def test_rejects_unknown_site_key(tmp_path: Path) -> None:
    body = MINIMAL + "[site]\nport = 8000\n"

    with pytest.raises(ListConfigError, match=r"unknown key: site\.port"):
        load_list_config(write(tmp_path, body))


def test_rejects_unknown_tag_axis(tmp_path: Path) -> None:
    body = MINIMAL + '[tags.mood]\nCalm = "c"\n'

    with pytest.raises(ListConfigError, match=r"unknown key: tags\.mood"):
        load_list_config(write(tmp_path, body))


def test_rejects_bad_section_type(tmp_path: Path) -> None:
    body = 'name = "X"\nrepo_slug = "y"\nsections = "Tools"\n'

    with pytest.raises(ListConfigError, match="sections must be a list"):
        load_list_config(write(tmp_path, body))


def test_rejects_empty_name(tmp_path: Path) -> None:
    body = 'name = ""\nrepo_slug = "y"\nsections = ["A"]\n'

    with pytest.raises(ListConfigError, match="name must be a non-empty string"):
        load_list_config(write(tmp_path, body))
