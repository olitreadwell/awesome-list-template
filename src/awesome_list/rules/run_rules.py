"""Run every rule over a parsed document."""

from __future__ import annotations

from dataclasses import replace

from awesome_list.github.github_stats import StatsSnapshot
from awesome_list.parse.readme_model import ListDocument
from awesome_list.rules.check_bare_urls import check_bare_urls
from awesome_list.rules.check_duplicate_urls import check_duplicate_urls
from awesome_list.rules.check_entry_grammar import check_entry_grammar
from awesome_list.rules.check_github_stats import check_github_stats
from awesome_list.rules.check_grouping import check_grouping
from awesome_list.rules.check_tag_vocabulary import check_tag_vocabulary
from awesome_list.rules.check_toc_freshness import check_toc_freshness
from awesome_list.rules.check_url_shape import check_url_shape
from awesome_list.rules.rule_violation import RuleViolation
from awesome_list.tags import TagVocabulary


def run_rules(
    document: ListDocument,
    text: str,
    vocabulary: TagVocabulary,
    *,
    file: str = "readme.md",
    entry_sections: tuple[str, ...] = (),
    github_snapshot: StatsSnapshot | None = None,
    github_stats_enabled: bool = False,
    github_stats_max_age_days: int = 14,
    allowed_urls: tuple[str, ...] = (),
    nested_details_allowed: bool = False,
) -> tuple[RuleViolation, ...]:
    """Return every violation in the document, ordered by line."""
    violations: list[RuleViolation] = []
    allowed = frozenset(allowed_urls)

    for entry in document.entries:
        # A list that keeps detail bullets under an entry declares them as
        # details, so the entry grammar does not apply to those lines.
        if not (nested_details_allowed and entry.nested_under_entry):
            violations.extend(check_entry_grammar(entry))
        violations.extend(check_url_shape(entry, allowed))
        violations.extend(check_tag_vocabulary(entry, vocabulary))

    violations.extend(
        check_duplicate_urls(document, allowed, skip_details=nested_details_allowed)
    )
    violations.extend(check_bare_urls(document))
    violations.extend(
        check_grouping(
            document,
            entry_sections,
            nested_details_allowed=nested_details_allowed,
        )
    )
    violations.extend(check_toc_freshness(document, text))
    violations.extend(
        check_github_stats(
            document,
            github_snapshot,
            github_stats_max_age_days,
            enabled=github_stats_enabled,
            allowed_urls=allowed,
        )
    )

    return tuple(
        sorted(
            (replace(v, file=file) for v in violations), key=lambda v: (v.line, v.rule)
        )
    )
