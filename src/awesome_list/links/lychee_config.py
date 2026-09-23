"""Render a lychee config from awesome.toml, so link checking matches the list."""

from __future__ import annotations

from awesome_list.config.list_config import ListConfig

HEADER = "# Generated from awesome.toml by make links. Do not edit by hand."
CACHE_MAX_AGE = "6d"
MAX_RETRIES = 2
ACCEPT = ("200..=204", "429")


def render_lychee_config(config: ListConfig) -> str:
    """Return the lychee TOML for this list."""
    lines = [
        HEADER,
        "cache = true",
        f'max_cache_age = "{CACHE_MAX_AGE}"',
        f"max_retries = {MAX_RETRIES}",
        f"accept = [{', '.join(f'"{code}"' for code in ACCEPT)}]",
        'include_fragments = "none"',
    ]
    excluded = tuple(dict.fromkeys((*config.links.exclude, *config.links.allowlist)))
    if excluded:
        lines.append("")
        lines.append(
            "# links.exclude and links.allowlist: skipped, not reported as dead."
        )
        lines.append(f"exclude = [{', '.join(f'"{url}"' for url in excluded)}]")
    lines.append("")
    return "\n".join(lines)
