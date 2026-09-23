# Tasks

Ordered by dependency. Each task fits one session, touches five files or fewer,
and names the test that proves it. Tasks marked RED start with a failing test or
a failing fixture. Nothing on this list needs GitHub Actions.

## Phase 1: skeleton and gate

- [x] T01 Repo skeleton
  - Acceptance: `pyproject.toml` pins deps and declares `requires-python =
">=3.12"`; `uv.lock` committed; `tools/package.json` pins awesome-lint,
    prettier, and pagefind with a committed lockfile; `license` (CC0-1.0),
    `code-of-conduct.md` (Contributor Covenant 2.1), `contributing.md`,
    `security.md`, `AGENTS.md`, `.editorconfig`, `.gitattributes`, `.gitignore`,
    and `awesome.toml` exist; `make install` succeeds on 3.12, 3.13, and 3.14.
  - Verify: `make install` then `uv run python -c "import awesome_list"`.
  - Files: `pyproject.toml`, `uv.lock`, `tools/package.json`, `Makefile`,
    `awesome.toml`, `license`, `code-of-conduct.md`.

- [x] T02 Config loading (RED)
  - Acceptance: `load_list_config` reads `awesome.toml` through `tomllib`, fills
    defaults, rejects unknown keys and a missing `name`, `repo_slug`, or
    `sections`, and returns a frozen dataclass. `site.enabled` defaults to false
    and `links.archive` defaults to `"off"`.
  - Verify: `make test -- tests/unit/config/`.
  - Files: `src/awesome_list/config/load_list_config.py`,
    `src/awesome_list/config/list_config.py`, `tests/unit/config/`.

- [x] T03 Gate and hooks
  - Acceptance: `ci/check.sh` runs `make check`; `.githooks/pre-commit` runs
    `make check-fast`; `.githooks/pre-push` runs `make check`;
    `.githooks/commit-msg` runs commitlint; `make hooks-install` sets
    `core.hooksPath`. No check exists only in a hosted workflow.
  - Verify: `make hooks-install`, then a seeded failure refuses the push; the
    `prepush_runs_full_check` guardrail passes.
  - Files: `ci/check.sh`, `.githooks/pre-commit`, `.githooks/pre-push`,
    `.githooks/commit-msg`, `src/awesome_list/cli/run_hooks_install.py`.

- [x] T04 GitHub slug (RED)
  - Acceptance: `github_slug` matches `github-slugger` on a table of headings
    including punctuation, emoji, duplicates, and variation selectors, so TOC
    anchors resolve on GitHub.
  - Verify: `make test -- tests/unit/slug/` plus the parity fixture.
  - Files: `src/awesome_list/slug/github_slug.py`, `tests/unit/slug/`.

## Phase 2: parse

- [x] T05 Parser model and token walk (RED)
  - Acceptance: `parse_readme` walks the markdown-it token stream into
    `ListDocument`, `ListSection`, `ListGroup`, `ListEntry`, `ListTag` with line
    numbers, skipping the Contents section and `Footnotes`.
  - Verify: `make test -- tests/unit/parse/`.
  - Files: `src/awesome_list/parse/parse_readme.py`,
    `src/awesome_list/parse/readme_model.py`, `tests/fixtures/readme/clean.md`.

- [x] T06 Parser edges (RED)
  - Acceptance: nested groups, indented bullets, inline code, emphasis, emoji in
    names, HTML comments inside the TOC, and multi-link description lines all
    parse to the expected model.
  - Verify: `make test -- tests/unit/parse/test_parse_readme_edges.py`.
  - Files: `tests/fixtures/readme/edges.md`, `tests/unit/parse/`.

## Phase 3: rules

- [x] T07 Violations and renderers (RED)
  - Acceptance: `RuleViolation` carries `rule`, `file`, `line`, `message`, `fix`;
    a terminal renderer and a Markdown renderer both consume it, one for the
    contributor and one for `jobs/annotate.sh`.
  - Verify: `make test -- tests/unit/rules/test_render_violations.py`.
  - Files: `src/awesome_list/rules/rule_violation.py`,
    `src/awesome_list/rules/render_violations.py`.

- [x] T08 `check_entry_grammar` (RED)
  - Acceptance: flags a missing dash separator, lowercase description start,
    missing trailing period, and trailing whitespace; the clean fixture is zero
    violations.
  - Verify: `make test -- tests/unit/rules/test_check_entry_grammar.py`.
  - Files: `src/awesome_list/rules/check_entry_grammar.py`,
    `tests/fixtures/readme/dirty-grammar.md`.

- [x] T09 `check_duplicate_urls` (RED)
  - Acceptance: catches exact and normalized duplicates (trailing slash, `www.`,
    fragment), reports both lines, and blames the later entry.
  - Verify: `make test -- tests/unit/rules/test_check_duplicate_urls.py`.
  - Files: `src/awesome_list/rules/check_duplicate_urls.py`,
    `src/awesome_list/rules/normalize_url.py`.

- [x] T10 `check_url_shape` (RED)
  - Acceptance: flags relative URLs, fragment-only URLs, `javascript:` URLs,
    `utm_*` parameters, and plain `http` where https answers.
  - Verify: `make test -- tests/unit/rules/test_check_url_shape.py`.
  - Files: `src/awesome_list/rules/check_url_shape.py`.

- [x] T11 `check_tag_vocabulary` and `check_grouping` (RED)
  - Acceptance: flags tags outside the `awesome.toml` vocabulary, entries missing
    a type or access tag, group headings with no entries, sections with no
    entries, and bullets nested more than one level under a group.
  - Verify: `make test -- tests/unit/rules/`.
  - Files: `src/awesome_list/rules/check_tag_vocabulary.py`,
    `src/awesome_list/rules/check_grouping.py`.

- [x] T12 `check_toc_freshness` (RED)
  - Acceptance: flags a missing Contents section, a section missing from the
    TOC, an extra TOC line, wrong order, a stale anchor, more than one nesting
    level, and any `Contributing` or `Footnotes` line.
  - Verify: `make test -- tests/unit/rules/test_check_toc_freshness.py`.
  - Files: `src/awesome_list/rules/check_toc_freshness.py`,
    `tests/fixtures/readme/dirty-toc.md`.

- [ ] T13 `check_entry_status` (RED)
  - Acceptance: flags an entry whose target is archived, deprecated, or
    superseded while it sits in the main list; passes the same shape inside
    `legacy.md`.
  - Verify: `make test -- tests/unit/rules/test_check_entry_status.py`.
  - Files: `src/awesome_list/rules/check_entry_status.py`,
    `tests/fixtures/readme/dirty-legacy-entries.md`.

- [ ] T14 `check_description_not_self_referential` (RED)
  - Acceptance: flags a top description that describes the list rather than the
    topic, including the phrasing upstream rejects, and passes a topic
    description.
  - Verify: `make test -- tests/unit/rules/test_check_description.py`.
  - Files: `src/awesome_list/rules/check_description_not_self_referential.py`.

- [ ] T15 `check_header_image` and `check_badge` (RED)
  - Acceptance: flags a header image that does not link out, a heading that
    repeats the image wording, a badge away from the heading, a modified badge
    SVG, and a badge link that does not resolve.
  - Verify: `make test -- tests/unit/rules/test_check_header_image.py`.
  - Files: `src/awesome_list/rules/check_header_image.py`,
    `src/awesome_list/rules/check_badge.py`.

## Phase 4: TOC and CLI

- [x] T16 `sync_contents` (RED)
  - Acceptance: renders the Contents list from headings, rewrites it in place
    while leaving the rest of the file byte-identical, and is idempotent.
  - Verify: `make test -- tests/unit/toc/`.
  - Files: `src/awesome_list/toc/render_contents.py`,
    `src/awesome_list/toc/sync_contents.py`.

- [x] T17 `list-check` and `toc` CLI
  - Acceptance: `make list-check` takes `--readme`, `--config`, and
    `--report-only`, exits non-zero on violations unless report-only, and prints
    rule, file, line, and fix. `make toc-check` reports drift without writing.
  - Verify: `make list-check`, `make toc-check`, and
    `make test -- tests/unit/cli/`.
  - Files: `src/awesome_list/cli/run_list_check.py`,
    `src/awesome_list/cli/run_toc.py`.

- [x] T17b GitHub stats on every GitHub link (RED)
  - Acceptance: `github_repo_slug` reads `owner/repo` from a repo URL and returns
    nothing for a profile, an issue, a pull request, a gist, or a non-GitHub
    host; `format_stats` prints `★ 1,234 stars, last push 2026-09-20.` and
    `★ 87 stars, archived 2024-05-01.`; `apply_github_stats` adds or replaces one
    trailing segment, is idempotent, and leaves every other line byte-identical;
    `check_github_stats` fails a GitHub entry with no stats segment, warns once when
    the snapshot is older than `max_age_days`, and returns nothing when
    `github.stats = false`; `make stats` writes `github-stats.json` and the readme
    and fails soft when `gh` is unreachable; `make stats-check` verifies both with
    no network at all.
  - Verify: `make test -- tests/unit/github/ tests/unit/cli/test_stats_cli.py`,
    then `make stats-check`.
  - Files: `src/awesome_list/github/github_stats.py`,
    `src/awesome_list/github/fetch_repo_stats.py`,
    `src/awesome_list/github/stats_snapshot.py`,
    `src/awesome_list/rules/check_github_stats.py`,
    `src/awesome_list/cli/run_stats.py`.

- [x] T17c Mine upstream lists for candidates (RED)
  - Acceptance: `parse_table_entries` reads `| [Name](url) | Description |` rows with
    their heading, skips header, separator, and linkless rows, and drops markdown
    noise from text; `propose_source_entries` proposes only entries that match a
    keyword and are not already in the readme; `render_source_report` says in the
    report that nothing has been written; `make sources` writes
    `reports/source-candidates.md`, never the readme, and is soft when every
    upstream list is unreachable.
  - Verify: `make test -- tests/unit/sources/ tests/unit/cli/test_sources_cli.py`.
  - Files: `src/awesome_list/sources/parse_table_entries.py`,
    `src/awesome_list/sources/propose_source_entries.py`,
    `src/awesome_list/sources/fetch_source_readme.py`,
    `src/awesome_list/cli/run_sources.py`.

## Phase 5: exports

- [ ] T18 `data.json` and schema (RED)
  - Acceptance: writes entries, sections, tags, counts, and generation metadata;
    validates against `schemas/data.schema.json`; entry count equals the readme
    bullet count.
  - Verify: `make test -- tests/unit/export/test_export_data_json.py`.
  - Files: `src/awesome_list/export/export_data_json.py`,
    `schemas/data.schema.json`, `schemas/entry.schema.json`.

- [ ] T19 CSV and NDJSON
  - Acceptance: stable column order, RFC 4180 quoting, one entry per NDJSON line,
    header names matching the schema fields.
  - Verify: `make test -- tests/unit/export/test_export_data_csv.py`.
  - Files: `src/awesome_list/export/export_data_csv.py`.

- [ ] T20 Atom feed and sitemap
  - Acceptance: `feed.xml` is Atom 1.0 valid with absolute URLs and stable ids;
    `sitemap.xml` matches the XSD with a `lastmod` tied to the publish commit.
  - Verify: `make test -- tests/unit/export/`.
  - Files: `src/awesome_list/export/export_atom_feed.py`,
    `src/awesome_list/export/export_sitemap.py`.

## Phase 6: site, opt-in

- [ ] T21 Static site (RED, opt-in)
  - Acceptance: with `site.enabled = true`, `make site` writes a self-contained
    `index.html` with escaped entry text, tag chips that do not rely on colour
    alone, and a full no-JS list. With `site.enabled = false`, nothing is written
    and `make check` is unchanged.
  - Verify: `make test -- tests/golden/`, and the `site_off_writes_nothing`
    test.
  - Files: `src/awesome_list/site/build_static_site.py`,
    `src/awesome_list/site/render_index_html.py`, `tests/golden/`.

- [ ] T22 Search index and E2E (opt-in)
  - Acceptance: Pagefind indexes the built HTML; E2E specs cover entry count
    against `data.json`, search for a known term, tag filtering, keyboard-only
    navigation, and an axe scan with zero serious or critical violations.
  - Verify: `make site && pytest -m e2e`.
  - Files: `src/awesome_list/site/build_search_index.py`, `e2e/`.

- [ ] T23 Publish job
  - Acceptance: `jobs/publish.sh` builds `site/`, commits it to the `gh-pages`
    branch through a git worktree, pushes it, and leaves `main` untouched. It is
    a no-op with a clear message when the site is off.
  - Verify: publish from a scratch repo with Pages set to serve `gh-pages`, then
    load the URL with no hosted runner involved.
  - Files: `jobs/publish.sh`.

- [ ] T24 Lighthouse budget (opt-in)
  - Acceptance: accessibility 100, performance and best practices 95+, thresholds
    in `lighthouserc.json`, and `make check-full` runs it outside pre-push.
  - Verify: `make check-full` on the built site.
  - Files: `lighthouserc.json`, `Makefile`.

## Phase 7: submission

- [ ] T25 `check_awesome_re_readiness` (RED)
  - Acceptance: one check function per row of the compliance table in `SPEC.md`,
    each returning pass, fail, manual, or skipped-with-reason; GitHub API checks
    use a token from `gh auth` and degrade to `manual` on rate limit.
  - Verify: `make test -- tests/unit/submission/`, then `make submission-check`
    on a scratch repo.
  - Files: `src/awesome_list/submission/check_awesome_re_readiness.py`,
    `src/awesome_list/submission/check_repo_metadata.py`.

- [ ] T26 Readiness report
  - Acceptance: a Markdown checklist the maintainer pastes into the submission
    PR, failing items showing the exact fix, manual reminders printed last.
  - Verify: golden test plus one real paste into a PR body.
  - Files: `src/awesome_list/submission/render_readiness_report.py`,
    `tests/golden/`.

## Phase 8: links

- [ ] T27 `extract_added_urls` (RED)
  - Acceptance: given a git range, returns added URLs only, deduped, ignoring
    removed lines, with `--base` for branches.
  - Verify: `make test -- tests/unit/links/test_extract_added_urls.py`.
  - Files: `src/awesome_list/links/extract_added_urls.py`,
    `tests/fixtures/diffs/`.

- [ ] T28 Link diff at pre-push
  - Acceptance: `make links-diff` checks only added URLs, finishes under 60
    seconds for a 20-URL branch, and passes on 429 or bot-wall responses after
    retries and allowlisting.
  - Verify: a branch with a dead link fails pre-push, a live one passes.
  - Files: `lychee.toml`, `.githooks/pre-push`, `ci/check.sh`.

- [ ] T29 Weekly link job
  - Acceptance: `jobs/links.sh` opens one issue titled
    `Link check: <n> broken links`, updates it on later runs, closes it when
    clean, and fails only on 404 and 410. `make jobs-due` runs it when overdue.
  - Verify: seed a dead link, run `make jobs-links` twice, fix, run again.
  - Files: `jobs/links.sh`, `schedule/launchd/links.plist`.

- [ ] T30 Dead entry handling and local archive (opt-in)
  - Acceptance: with `links.archive = "off"` the job reports and writes nothing.
    With `"local"`, `archive_page_locally` saves a single-file copy through
    monolith, records source URL, capture date, tool, and hash in
    `archive/index.json`, and `plan_dead_entry_fix` opens a PR moving the entry
    to `legacy.md` with a link to the copy. Size caps enforced.
  - Verify: unit tests over recorded responses, one scratch-repo run, and
    `local_archive_stays_opt_in` plus `no_archived_url_in_main_list`.
  - Files: `src/awesome_list/links/archive_page_locally.py`,
    `src/awesome_list/links/plan_dead_entry_fix.py`.

## Phase 9: contributors and hygiene

- [ ] T31 Issue form and triage job
  - Acceptance: `add-link.yml` collects name, URL, section, description, tags;
    `jobs/triage.sh` validates the URL, checks duplicates, and posts a verdict
    comment. The description is copied verbatim, asserted by `no_generated_prose`.
  - Verify: open a real issue in a scratch repo, run `make jobs-triage`, read the
    comment.
  - Files: `.github/ISSUE_TEMPLATE/add-link.yml`, `jobs/triage.sh`.

- [ ] T32 PR comment, labels, contributors
  - Acceptance: `jobs/annotate.sh` keeps one PR comment through
    `gh pr comment --edit-last`, labels from `awesome.toml`, and
    `CONTRIBUTORS.md` regenerates from git history.
  - Verify: two runs on one PR produce one comment.
  - Files: `jobs/annotate.sh`, `src/awesome_list/cli/run_contributors.py`.

- [ ] T33 Tooling, hooks, and repo settings
  - Acceptance: gitleaks in pre-commit and nightly, osv-scanner nightly over
    both lockfiles, `codespell` in pre-commit, Renovate as a weekly local job,
    `make repo-setup` setting description, topics, and default branch through
    `gh api` with dry-run first.
  - Verify: a fake secret is refused; `make jobs-due` runs the audit;
    `make repo-setup --dry-run` prints the calls.
  - Files: `.githooks/`, `jobs/audit.sh`, `renovate.json`,
    `src/awesome_list/cli/run_repo_setup.py`.

## Phase 10: guideline enforcement

- [ ] T34 Guideline registry with citations
  - Acceptance: `awesome_re_rules.py` holds one entry per requirement with
    upstream file, line, content hash, and the awesome-lint rule name when one
    exists; `guideline_pin_currency` fails on a missing citation or hash.
  - Verify: `make test -- tests/unit/submission/test_awesome_re_rules.py`.
  - Files: `src/awesome_list/submission/awesome_re_rules.py`.

- [ ] T35 Upstream drift job
  - Acceptance: `jobs/drift.sh` fetches `awesome.md`,
    `pull_request_template.md`, and `create-list.md`, compares hashes with the
    registry, and opens or updates one issue naming the affected rules. It never
    auto-edits a rule.
  - Verify: run against a pinned copy, then against a deliberate hash change.
  - Files: `jobs/drift.sh`, `src/awesome_list/submission/diff_guideline_sources.py`.

- [ ] T36 Guardrail suite
  - Acceptance: `tests/guardrails/` holds one test per guardrail in `SPEC.md`,
    including `checks_are_not_actions_only`, `prepush_runs_full_check`,
    `no_archived_url_in_main_list`, and `local_archive_stays_opt_in`.
  - Verify: `make test -- tests/guardrails/`, with one deliberate violation per
    test to confirm it fails.
  - Files: `tests/guardrails/`, `tests/guardrails/helpers.py`.

- [ ] T37 `compliance-audit` and trailer audit
  - Acceptance: runs the registry check, awesome-lint on the fixture readme, the
    guardrail suite, and a bot trailer audit over commits since the last tag;
    exits non-zero on failure; wired into `make check`.
  - Verify: clean run, then a failing commit without a trailer.
  - Files: `src/awesome_list/cli/run_compliance_audit.py`,
    `src/awesome_list/submission/audit_bot_trailers.py`.

- [x] T38 Rule parity with awesome-lint
  - Acceptance: awesome-lint runs over every fixture readme; a fixture our rules
    accept but the linter rejects fails the gate; deliberate strictness is
    recorded with its reason.
  - Verify: add a fixture that breaks an awesome-lint rule we miss, watch it
    fail.
  - Files: `tests/parity/test_awesome_lint_parity.py`.

## Phase 11: scheduling and adapters

- [ ] T39 Scheduler and catch-up
  - Acceptance: launchd plists for links, drift, triage, publish, and audit;
    systemd timers and a `crontab.example`; `jobs/run-due.sh` reads `.state/`,
    runs overdue jobs once in order, and does nothing when nothing is due. Jobs
    are idempotent under a double run.
  - Verify: fake a two week gap, run `make jobs-due`, run again, assert the
    second run is a no-op.
  - Files: `jobs/run-due.sh`, `schedule/launchd/`, `schedule/systemd/`,
    `schedule/crontab.example`.

- [ ] T40 Optional runner adapters
  - Acceptance: `ci/adapters/` holds a GitHub Actions file (not installed), a
    GitLab CI file, a Woodpecker file, and a Buildkite script, each running
    `ci/check.sh` and nothing else. `checks_are_not_actions_only` passes with all
    of them deleted.
  - Verify: delete `ci/adapters/`, run `make check`, confirm no change.
  - Files: `ci/adapters/`.

- [ ] T41 Pre-push gate proof
  - Acceptance: a seeded duplicate URL, a failing unit test, and a failing E2E
    spec each refuse `git push`; the fixes green them. Runtime within budget, or
    the E2E split into `check-full` is applied.
  - Verify: three seeded failures, three refused pushes, one green push.
  - Files: `.githooks/pre-push`.

## Phase 12: migration and docs

- [ ] T42 Migrate `awesome-kiwi-data`
  - Acceptance: engine matches its existing README output for entries, tags, and
    glyphs; the old `scripts/build_site.py` and `validate_readme.py` are replaced
    by `make export` and `make list-check`; report-only first, then enforcing;
    site output compared before the old builder is deleted.
  - Verify: diff old site output against new, then `make check` on that repo.
  - Files: `code/awesome-kiwi-data` (config, Makefile, scripts removal),
    `docs/migration.md`.

- [ ] T43 Migrate `awesome-olitreadwell`
  - Acceptance: `make list-check --report-only` clean on its two markdown files,
    then enforcing; `readme.md` untouched except recorded violations.
  - Verify: `make check` in that repo, and `docs/migration.md` updated.
  - Files: `code/awesome-olitreadwell`, `docs/migration.md`.

- [ ] T44 ADRs, usage, and self-test
  - Acceptance: ADRs record the Python choice, the no-hosted-runner choice, the
    rejected tools, the no-CI-badge rule, and the site opt-in; `docs/template-usage.md`
    lists the two files to edit and the first five commands; the self-test
    reproduces S1, S2, and S17 on a scratch repo.
  - Verify: scratch repo run, CI-less, linked in the PR description.
  - Files: `docs/adr/`, `docs/template-usage.md`, `docs/self-test.md`.
