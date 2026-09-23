# Plan: awesome-list-template

Technical plan for building the spec in `SPEC.md`. Order is by dependency, not
by importance. Each phase ends at a checkpoint a human can read and approve
before the next phase starts.

## Components and dependency graph

```
config (load_list_config)
  └── parse (parse_readme) ──┬── rules (check_*) ──┬── cli/list-check
                             │                     │
                             ├── toc (sync_contents) ── cli/toc
                             │
                             └── export (data.json, csv, atom, sitemap)
                                   └── site (build_static_site) ──┬── pagefind
                                                                  ├── e2e
                                                                  └── lighthouse
slug (github_slug) is used by toc and by the site anchors
submission (check_awesome_re_readiness) depends on parse plus gh
links (extract_added_urls, archive_page_locally, plan_dead_entry_fix) depends on
  parse plus git plus, for archiving, monolith
cli wraps everything; jobs/ shells out to cli and gh; nothing depends on cli
```

Rules, exports, and slug are pure functions over the parsed model, so they can
be built in parallel once `parse` lands. The site is opt-in and last among the
build steps.

## Phase order

1. Repo skeleton. `pyproject.toml` with `requires-python = ">=3.12"` and pinned
   deps, `uv.lock`, `tools/package.json` with awesome-lint, prettier, and
   pagefind pinned, `awesome.toml`, `license` (CC0-1.0), `code-of-conduct.md`
   (Contributor Covenant 2.1), `contributing.md`, `security.md`, `AGENTS.md`,
   `Makefile` with `check` and `check-fast`, `.githooks/`, and `ci/check.sh`.
   No engine code yet.
2. `load_list_config` plus typed dataclasses. Config in, frozen config out,
   defaults filled, unknown keys rejected.
3. `github_slug`. Small, and every TOC anchor and site link depends on it, so it
   comes before the parser work that consumes it.
4. `parse_readme`. Highest-risk component: markdown-it token stream to
   `ListDocument`, `ListSection`, `ListGroup`, `ListEntry`, `ListTag`, with line
   numbers. Everything downstream reuses its fixtures.
5. `rules/*`. One module per rule, each with a clean fixture, a dirty fixture,
   and a unit test. Parallel once `parse` is stable.
6. `toc/sync_contents`. Render and rewrite in place, idempotent.
7. `cli/list-check` and `cli/toc`, including `--report-only`, which is what the
   migrations need. First usable slice: an existing list can be checked.
8. `export/*`. `data.json` first, then csv, atom, sitemap. Contract tests per
   format.
9. `site/*`, opt-in. Golden tests on a fixture list, Pagefind index, E2E and
   Lighthouse behind `check-full`.
10. `jobs/publish.sh` plus Pages deploy-from-branch. Second usable slice: a list
    publishes with no hosted runner.
11. `submission/check_awesome_re_readiness` with the pinned rule registry.
    Third usable slice: a list can be submitted.
12. `links/*`: diff extraction, then the weekly job, then local archiving and
    dead entry planning behind `links.archive`.
13. Contributor surface: issue form, `jobs/triage.sh`, `jobs/annotate.sh`,
    contributors file, `make fix`.
14. Hygiene: gitleaks, codespell, osv-scanner, Renovate self-hosted,
    `make repo-setup`, `jobs/audit.sh`.
15. Scheduling: `jobs/run-due.sh`, launchd plists, systemd timers, crontab
    example, so no job depends on a hosted clock.
16. Migration of the two existing lists, report-only first, enforcing second,
    then the old scripts deleted.
17. Docs: ADRs, `docs/template-usage.md`, `docs/migration.md`, `docs/maintaining.md`,
    and a self-test on a scratch repo.

## Parallel work

- Phases 5, 8, and 10 can start once phase 4 lands and touch disjoint
  directories (`rules/`, `export/`, `site/`).
- Phases 13, 14, and 15 touch `jobs/`, `schedule/`, and `.githooks/` only, so
  they can be written while 12 is being debugged.
- Phase 16 depends on a green phase 7 and a green phase 8, and starts with the
  smaller list if the maintainer prefers a fast first migration.

## Risks and mitigations

| Risk                                                   | Mitigation                                                                                                                                              |
| ------------------------------------------------------ | ------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Parser model churn breaks rules and exports repeatedly | Freeze the model after phase 4 with tests, and route later changes through `schemas/`                                                                   |
| Our slug logic drifts from GitHub's anchors            | Parity test against `github-slugger` output on a table of headings, plus the awesome-lint TOC rule                                                      |
| Link checks flaky on 429, bot walls, or slow hosts     | Diff mode at pre-push, full check weekly, cache with `max_cache_age`, retries, an allowlist in `awesome.toml`, and hard failures limited to 404 and 410 |
| awesome-lint version bumps change rules under us       | Pin exactly in `tools/package.json`, review the Renovate PR, and keep the parity fixture test so a rule change shows up as a failing fixture            |
| Rate limits in the readiness checker                   | Token from `gh auth`, cached responses per run, `manual` verdict instead of a hard error                                                                |
| Pre-push runtime grows until people skip it            | Site off by default, E2E and Lighthouse in `check-full` and the nightly audit, and a recorded split once a list outgrows the budget                     |
| A contributor pushes with `--no-verify`                | `jobs/audit.sh` re-runs the full check against `main` nightly and reports the commit hash                                                               |
| A sleeping laptop never fires a scheduled job          | `jobs/run-due.sh` on an hourly tick reads `.state/` and runs overdue jobs on wake; every job is idempotent                                              |
| Local archiving bloats the repo                        | Per-file and total caps in `awesome.toml`, `archive/` gitignored by default, and a documented example kept instead                                      |
| Migration changes an existing list's output silently   | Report-only mode first, old site output diffed against new output, and `docs/migration.md` recording the state per list                                 |
| Template repo mistaken for a list                      | No badge, no `awesome` topics on the template, and `no_ci_badge_or_list_topics` as a guardrail test                                                     |

## Verification checkpoints

- After phase 7: `awesome-kiwi-data` runs `make list-check --report-only` with no
  crashes, and the violations are the ones a human would name.
- After phase 10: `jobs/publish.sh` pushes `gh-pages` from a scratch repo, the
  site is reachable, and Pagefind returns a known entry, with no hosted runner.
- After phase 11: `make submission-check` on a fixture repo reports the same
  verdicts a human would, including the manual reminders.
- After phase 12: `jobs/links.sh` opens one issue on a seeded dead link, updates
  it on a second run, closes it when fixed, and with `links.archive = "local"`
  writes a copy under `archive/` and moves the entry to `legacy.md`.
- After phase 15: `make jobs-due` runs every overdue job once after a simulated
  two week gap, and a second run does nothing.
- After phase 17: `make check` passes on a fresh clone plus a scratch list repo,
  which is S1, S2, and S17 measured end to end.
