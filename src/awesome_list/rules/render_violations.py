"""One renderer per audience: a terminal and a pull request comment."""

from __future__ import annotations

from awesome_list.rules.rule_violation import RuleViolation


def render_violations(
    violations: tuple[RuleViolation, ...], *, style: str = "text"
) -> str:
    """Render violations as plain text or as Markdown."""
    if not violations:
        return ""
    if style == "markdown":
        return "\n".join(f"- `{violation.render()}`" for violation in violations)
    return "\n".join(violation.render() for violation in violations)


def summarise_violations(violations: tuple[RuleViolation, ...]) -> str:
    """Return a one-line count by rule, for job summaries."""
    if not violations:
        return "no violations"
    counts: dict[str, int] = {}
    for violation in violations:
        counts[violation.rule] = counts.get(violation.rule, 0) + 1
    parts = [f"{rule} {count}" for rule, count in sorted(counts.items())]
    return f"{len(violations)} violations: " + ", ".join(parts)
