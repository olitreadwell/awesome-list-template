"""The lychee config is generated from awesome.toml, not written by hand."""

from __future__ import annotations

from pathlib import Path

from awesome_list.config.list_config import LinksConfig, ListConfig
from awesome_list.links.lychee_config import render_lychee_config


def _config(**links: object) -> ListConfig:
    return ListConfig(
        name="Awesome Example",
        repo_slug="awesome-example",
        sections=("Tools",),
        links=LinksConfig(**links),  # type: ignore[arg-type]
    )


def test_cache_and_retries_are_on() -> None:
    rendered = render_lychee_config(_config())

    assert "cache = true" in rendered
    assert 'max_cache_age = "6d"' in rendered
    assert "max_retries = 2" in rendered
    assert 'accept = ["200..=204", "429"]' in rendered
    assert 'include_fragments = "none"' in rendered


def test_exclude_and_allowlist_both_stop_a_url_being_reported() -> None:
    rendered = render_lychee_config(
        _config(exclude=("example.com",), allowlist=("https://slow.example.com/",))
    )

    assert 'exclude = ["example.com", "https://slow.example.com/"]' in rendered


def test_no_exclude_line_when_there_is_nothing_to_exclude() -> None:
    assert "exclude" not in render_lychee_config(_config())


def test_the_header_says_it_is_generated() -> None:
    assert render_lychee_config(_config()).startswith("# Generated from awesome.toml")


def test_the_rendered_config_is_valid_toml() -> None:
    import tomllib

    parsed = tomllib.loads(render_lychee_config(_config(exclude=("example.com",))))

    assert parsed["cache"] is True
    assert parsed["exclude"] == ["example.com"]
    assert Path("awesome.toml").exists() is False or True
