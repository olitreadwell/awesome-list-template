# Spec: awesome-list-template

A template and engine that treat a curated list as a maintained dataset. Copy
it, edit two files, and the list passes the awesome.re submission checklist and
keeps its links alive without a human opening every one. The same engine is what
Oli's existing lists migrate onto: `code/awesome-kiwi-data` and
`code/awesome-olitreadwell`.

## Objective

### Problem

Curated lists rot. Links die quietly, the table of contents drifts from the
headings, entries lose the dash or the trailing period, and the submission PR to
[sindresorhus/awesome](https://github.com/sindresorhus/awesome) gets closed on
details a script could have checked in two seconds.

Existing templates stop at a readme skeleton plus one lint workflow.
[jthegedus/awesome-list-template](https://github.com/jthegedus/awesome-list-template)
(95 stars, last pushed July 2024) is the closest prior art: CI and conventions,
no publishing path, no exports, no submission check, no plan for link rot.

### Users

- Maintainer: owns the list. Wants merges to be decisions rather than chores.
- Contributor: adds one link through an issue form or a small branch, and needs
  to be told exactly what is wrong without reading a style guide.
- Agent: an AI coding agent working in the repo, which needs a machine-checkable
  contract so it can verify its own work instead of guessing.

### What success looks like

A list created from this template is submission-ready on day one, and stays
green for a year with roughly one maintenance action per month. An existing list
migrated onto the engine keeps its current shape, gains tests it never had, and
gains link rot handling it never had.

## Decisions

Answers to the open questions from the first pass, plus the constraints added
since. These are settled unless the maintainer says otherwise.

1. **Host is GitHub.** Repo, issues, issue forms, and Pages. That is where
   awesome.re lists live. GitLab and Forgejo are out of scope for v1, though
   nothing in the pipeline assumes a host.
2. **No GitHub Actions dependency.** Every check is a local command, aggregated
   in `ci/check.sh` and driven by git hooks. `ci/adapters/` holds optional
   adapter files and none are installed. A check that only runs on a hosted
   runner stops running the moment a workflow is disabled or an org blocks
   Actions. See `docs/adr/0003-no-hosted-runner-dependency.md`.
3. **The engine is Python**, not TypeScript. Python standard library first, with
   a small dependency set. The two existing lists already have Python scripts
   (`build_site.py`, `validate_readme.py`), and this template grows those into
   one tested engine instead of starting a second runtime. See
   `docs/adr/0001-python-engine.md`.
4. **Supported Python versions are the current LTS-style set: 3.12, 3.13,
   3.14.** Tests run on all three, on macOS and Linux. Anything older is not
   supported, and `requires-python` says so.
5. **The site is opt-in.** `site.enabled = false` by default. Exports (`data.json`,
   `data.csv`, `feed.xml`) stay on because they cost nothing. Turning the site on
   adds HTML, search, the publish job, E2E, and Lighthouse to the gate.
6. **Config is its own file**, `awesome.toml`, not a key inside `pyproject.toml`
   and not inside `package.json`. TOML allows comments, and `tomllib` reads it
   from the standard library.
7. **Code of conduct is the full Contributor Covenant 2.1.**
8. **Archived entries are kept locally, and only when opted in.**
   `links.archive = "off"` by default, `"local"` to save a single-file copy into
   `archive/`, and `"wayback"` documented as the alternate. The main list never
   gains an archived URL: the entry moves to `legacy.md` and links the local copy.
9. **Enforcement is the automated test suite plus git hooks.** The pre-push hook
   runs the full gate. Scheduled jobs catch what a bypassed hook let through; they
   are not the first line of defense.
10. **Generated output is published, not committed to `main`.**
    `jobs/publish.sh` commits `site/` to a `gh-pages` branch through a git
    worktree.
11. **Every GitHub link carries stars and last activity.** `[github] stats = true`
    is the default in `awesome.toml`, so a reader sees `★ 4,210 stars, last
push 2024-05-06.` on the entry rather than clicking to find out. `make
stats` fetches stars, last push, and archived state through `gh api`, caches
    them in `github-stats.json`, then adds or replaces one trailing segment per
    entry. `make list-check` fails an entry that links a repository with no
    stats segment, points at `make stats` as the fix, and warns once when the
    snapshot is older than `max_age_days`. Only `make stats` touches the
    network: `make stats-check` and `make list-check` read the cached snapshot,
    so a laptop with no connection still runs the whole gate.
12. **Upstream lists are mined for candidates, never for entries.** `[sources]`
    in `awesome.toml` names readmes to read (`public-apis/public-apis` is the
    first one) and keywords to match. `make sources` parses their tables, drops
    anything the list already carries, attaches repo stats where the upstream
    link is a repository, and writes `reports/source-candidates.md`. It is a
    report and nothing else: a human writes the entry, because awesome.re
    rejects list content written by automation.

## Non-goals

- No CMS, database, or server. The list is a Markdown file plus scripts.
- No analytics, comment widgets, or third-party trackers in the site.
- No auto-generation of list content. awesome.re rejects AI-generated lists and
  fully AI-generated PRs, so automation here verifies and repairs.
- No fork of `awesome-lint`. We wrap it and pin it.
- No second runtime beyond the tooling Node install needed for `awesome-lint`,
  Prettier, and Pagefind.

## Tech Stack

Pinned exactly. `uv.lock` and `tools/package-lock.json` are committed.

Engine, Python 3.12 to 3.14:

| Use                     | Tool                               | Version        |
| ----------------------- | ---------------------------------- | -------------- |
| Environment and pinning | uv                                 | 0.12.18        |
| Lint and format         | ruff                               | 0.16.8         |
| Types                   | mypy (`--strict`)                  | 2.3.1          |
| Tests                   | pytest                             | 9.1.1          |
| Coverage                | pytest-cov, branch coverage        | 7.x            |
| Markdown parsing        | markdown-it-py                     | 4.2.0          |
| Markdown extras         | mdit-py-plugins, linkify-it-py     | current pinned |
| CLI                     | argparse from the standard library | 3.12+          |
| TOML config             | tomllib from the standard library  | 3.12+          |

Tooling, Node 24.21.0 LTS, installed only for these three:

| Use                                    | Tool                                  | Version |
| -------------------------------------- | ------------------------------------- | ------- |
| Awesome gate                           | awesome-lint                          | 2.3.0   |
| Markdown, JSON, YAML formatting        | prettier with `proseWrap: "preserve"` | 3.9.8   |
| Search index, only when the site is on | pagefind                              | 1.5.2   |

Command line tools that replace the Actions shortcuts. Each runs on a laptop, a
VPS, or a runner:

| Tool                                 | Version  | Replaces                                                        |
| ------------------------------------ | -------- | --------------------------------------------------------------- |
| gh (GitHub CLI)                      | 2.101.0  | issue creation, PR creation, PR comments, labels, repo settings |
| gitleaks                             | 8.30.1   | gitleaks-action                                                 |
| osv-scanner                          | 2.6.0    | dependency-review-action                                        |
| renovate (self-hosted, weekly job)   | 44.108.2 | Dependabot version updates                                      |
| lychee                               | 0.24.2   | lychee-action                                                   |
| monolith (optional, local archiving) | 2.10.1   | Wayback dependence                                              |
| scorecard (optional)                 | v2.4.4   | scorecard-action                                                |

Rejected, with reasons in `docs/adr/`:

- TypeScript on Node for the engine. Two runtimes for one repo, and the existing
  lists are already Python. Node stays as a tooling install.
- `husky`. Plain git hooks with `core.hooksPath = .githooks` need no install
  step and no postinstall script.
- `markdownlint-cli2`. awesome-lint already bundles the remark-lint rules this
  repo needs, and a second Markdown linter produces conflicting advice.
- `dkhamsing/awesome_bot`. Last commit April 2023. lychee does the job.
- `tcort/github-action-markdown-link-check`. Slower, weaker cache and fragment
  handling than lychee. One link checker is enough.
- Every Actions-only tool: `lychee-action`, `create-issue-from-file`,
  `create-pull-request`, `sticky-pull-request-comment`, `deploy-pages`,
  `upload-pages-artifact`, `scorecard-action`, `harden-runner`, `actionlint`,
  `zizmor`, `gitleaks-action`, `dependency-review-action`, `actions/labeler`,
  `actions/stale`, `actions/github-script`. A local CLI or `gh` covers each.
- Next.js or any SPA framework for the site. With the site opt-in, it is one
  static page plus a search index.

## Commands

`make` targets wrap `uv run`, so no tool needs a global install. Every command
runs on a laptop or on a runner, and none needs a hosted pipeline.

```bash
make install             # uv sync, plus npm ci in tools/
make check               # the full gate, see below
make check-fast          # pre-commit subset, under 10 seconds
make check-full          # check plus the checks that need the network
make toc                 # rewrite the Contents section
make toc-check           # fail if the Contents section is stale
make list-check          # grammar, duplicates, tags, TOC, grouping, GitHub stats
make stats               # fetch stars and last push dates, write the snapshot
make stats-check         # fail when the snapshot or an entry is out of date
make sources             # candidates from upstream lists, written as a report
make export              # data.json, data.ndjson, data.csv
make export-check        # fail when those three files are behind
make submission-check    # awesome.re readiness report
make compliance-audit    # repository settings that drifted, read only
make links               # lychee over the readme, config generated from awesome.toml
make links-diff          # lychee over URLs added in this branch
make jobs-due            # run any scheduled job that is overdue
make jobs-links          # link check, report, optional issue
make jobs-stats          # stats refresh, commits only when the numbers moved
make jobs-drift          # upstream guideline drift
make hooks-install       # core.hooksPath = .githooks
make repo-setup          # gh api, dry-run by default
```

`make check` runs, in order: `ruff check`, `mypy`, `ruff format --check`,
`prettier --check`, `toc-check`, `list-check`, `stats-check`, `export-check`,
`awesome-lint`, and `pytest` with the coverage floor and the guardrail and
parity suites. It is the single gate, and the pre-push hook, the scheduled
audit, and a human all call it.

### Built, and not yet built

This spec describes the whole engine. What exists today is: the parse model,
the rules, the TOC, GitHub stats, upstream sources, the three exports, the
lychee wrapper and its diff mode, the submission checks, the repository
settings audit and setup, the hooks, and the job scripts listed above.

Not built yet, and written up here rather than wired:

- the site (`src/awesome_list/site/`, `site/`, Pagefind, `e2e/`, Lighthouse),
  so `make site`, `make e2e`, and `make lighthouse` do not exist
- the Atom feed, the sitemap, and JSON-LD
- the guideline registry (`awesome_re_rules.py`) and its drift job
- dead-entry remediation and local archiving (`plan_dead_entry_fix.py`,
  `archive_page_locally.py`)
- the issue triage, PR annotation, and publish job scripts

`AUTOMATIONS.md` carries a row per automation with the same distinction.

`make check-fast` is the pre-commit subset: `ruff format --check` on changed
files, `prettier --check` on changed files, and `toc-check` plus `list-check`.
It stays under 10 seconds so nobody is tempted to skip it.

`ci/check.sh` runs `make check` and nothing else.

## Project Structure

```
readme.md                     the list; only source of truth for entries
awesome.toml                  list name, repo slug, badge, sections, tag vocab,
                              site, links, structure, and github stats policy
github-stats.json             stars and last push per repo, written by make stats
contributing.md               contributor guide, linked from readme Footnotes
code-of-conduct.md            Contributor Covenant 2.1
license                       CC0-1.0 text
security.md                   reporting policy for the repo
AGENTS.md                     contract for agents working in the repo
src/awesome_list/
  cli/                        one module per make target
  config/                     load awesome.toml, typed, unknown keys rejected
  parse/                      markdown-it token stream to ListSection, ListEntry
  rules/                      one rule per module: check_entry_grammar.py, ...
  toc/                        render_contents.py, sync_contents.py
  export/                     build_exports.py, JSON, NDJSON, and CSV
  site/                       not built yet
  submission/                 check_submission.py
  repo/                       audit_repo_settings.py, github_repo_settings.py
  github/                     github_repo_slug, format_stats, apply_github_stats,
                              fetch_repo_stats.py, stats_snapshot.py
  sources/                    parse_table_entries.py, propose_source_entries.py,
                              fetch_source_readme.py
  links/                      added_urls.py, lychee_config.py, run_lychee.py
  slug/                       github_slug.py, matching github-slugger output
schemas/
  entry.schema.json           one entry
  data.schema.json            data.json
tools/
  package.json                awesome-lint, prettier, pagefind, pinned
  package-lock.json
tests/
  unit/                       mirrors src/awesome_list/ layout
  fixtures/readme/            clean.md plus one dirty fixture per rule
  fixtures/diffs/             git diffs for the link diff tests
  guardrails/                 one test per guardrail in this spec
  parity/                     our rules against awesome-lint output
e2e/                          Playwright specs, only when the site is on
archive/                      local single-file copies, opt-in, gitignored by
                              default with an example kept for docs
site/                         generated, gitignored, published to gh-pages
ci/
  check.sh                    the one command any runner calls
  adapters/                   github-actions.yml (not installed), gitlab-ci.yml,
                              woodpecker.yml, buildkite.sh
jobs/
  links.sh  stats.sh  drift.sh  run-due.sh
  triage.sh  publish.sh  annotate.sh  audit.sh       not built yet
schedule/
  launchd/  systemd/  crontab.example
.githooks/
  pre-commit  pre-push  commit-msg
.state/                       last-success timestamps per job, gitignored
.github/
  ISSUE_TEMPLATE/add-link.yml, config.yml
  PULL_REQUEST_TEMPLATE.md
  CODEOWNERS
renovate.json
docs/adr/, docs/template-usage.md, docs/migration.md, docs/maintaining.md
```

## Code Style

Domain-prefixed names, precise types, comments above the definition they explain.

```python
@dataclass(frozen=True, slots=True)
class ListEntry:
    name: str
    url: str
    description: str
    tags: tuple[ListTag, ...]
    line: int


def parse_list_entry(markdown_line: str) -> ListEntry | None:
    """Return an entry for a README bullet, or None for a group heading."""


def check_entry_grammar(entry: ListEntry) -> tuple[RuleViolation, ...]:
    """Return one violation per broken rule, each with a line and a fix hint."""
```

Conventions:

- Exports are two or three words with a domain word: `parse_list_entry`, not
  `parse` or `entry`.
- One rule per module, named for the rule: `check_duplicate_urls.py`.
- Rules are pure: entry in, violations out. No I/O, no clock, no network.
  Anything with I/O lives in `cli/`, `links/`, or `jobs/`.
- Violations are a frozen dataclass with `rule`, `file`, `line`, `message`,
  `fix`, so the CLI, the PR comment, and the triage job render the same object.
- Tests mirror the source path: `tests/unit/rules/test_check_duplicate_urls.py`.
- `mypy --strict` clean. No `Any`, no `# type: ignore` without a comment naming
  the reason.
- Ruff owns formatting and lint. No style debate beyond `ruff format`.

## Testing Strategy

Automated tests are the gate. A hosted pipeline is optional and is never the
enforcement mechanism.

### The cycle

```
RED    write the failing test, or the failing fixture pair
GREEN  smallest implementation that passes
REFACTOR  rename, extract, keep the suite green
```

### Where the gate runs

| Stage            | What runs                                                                   | Budget           |
| ---------------- | --------------------------------------------------------------------------- | ---------------- |
| pre-commit hook  | `make check-fast`: format check on changed files, `toc-check`, `list-check` | under 10s        |
| pre-push hook    | `make check`: the full suite, including guardrails and parity               | under 5 min      |
| nightly job      | `jobs/audit.sh` re-runs `make check` against `main` and reports             | minutes          |
| weekly jobs      | `jobs/links.sh` full link check, `jobs/drift.sh` guideline drift            | minutes          |
| optional adapter | `ci/check.sh`, which is `make check`                                        | runner dependent |

Consequences that shape the design:

- Every check runs offline except `awesome-lint`, lychee, `make stats`, and,
  when the site is on, Pagefind's install. Each degrades with an explicit message instead of a
  hard failure when the network is unavailable.
- The pre-push hook is the real gate, so its runtime matters. With the site off
  there is no E2E and no Lighthouse, and the suite is test-dominated and fast.
  With the site on, E2E and Lighthouse join pre-push only if they fit the budget,
  and `make check-full` exists for the slower set.
- `git push --no-verify` bypasses the gate. That is allowed for work in progress
  on a scratch branch. `jobs/audit.sh` exists to catch anything that reaches
  `main` without a green `make check`, and it reports the commit hash.
- Tests never depend on the environment: no token in unit tests, no network in
  unit tests, no clock reads outside an injected clock, no test order dependence
  (`pytest-randomly` enabled).

### What gets which test

| Concern                                  | Level                                                  | Where                                    |
| ---------------------------------------- | ------------------------------------------------------ | ---------------------------------------- |
| Parser (tokens to model)                 | unit, small                                            | `tests/unit/parse/`                      |
| One rule each                            | unit, small, table-driven                              | `tests/unit/rules/`                      |
| GitHub slug parity with `github-slugger` | unit plus parity                                       | `tests/unit/slug/`, `tests/parity/`      |
| TOC render and sync                      | unit plus idempotence                                  | `tests/unit/toc/`                        |
| Exports                                  | unit plus contract against `schemas/`                  | `tests/unit/export/`                     |
| Site HTML                                | golden file, only when the site is on                  | `tests/golden/`                          |
| CLI wiring, config loading               | unit with a temp dir                                   | `tests/unit/cli/`                        |
| GitHub stats fetch, format, apply        | unit with an injected runner, never the network        | `tests/unit/github/`, `tests/unit/cli/`  |
| Upstream list mining                     | unit over a recorded readme, never the network         | `tests/unit/sources/`, `tests/unit/cli/` |
| Readiness checker                        | unit per requirement, one end to end on a fixture repo | `tests/unit/submission/`                 |
| Link diff and archive planning           | unit over fixture diffs and recorded responses         | `tests/unit/links/`                      |
| Job scripts                              | integration, `bash -n` plus a dry run                  | `tests/integration/jobs/`                |
| Built site in a browser                  | E2E, medium, site on only                              | `e2e/`                                   |

### Test rules

- Fixtures are the contract. Every rule gets a pair: `clean.md` (zero violations
  of that rule) and `dirty-<rule>.md` (exactly one violation, expected line). A
  rule that cannot show both is not finished.
- Prove-It for bugs. A bug report starts as a failing fixture, then the fix.
- State, not interactions. Assert on violations and rendered output, never on
  call sequences or on internals.
- DAMP over DRY. Each test reads as a statement about the rule.
- Golden files are reviewed, not blessed. `pytest --update-golden` is a
  deliberate act and the diff is read.
- Contract tests run against `schemas/` for `data.json`, against OpenSearch 1.1
  for the descriptor, and against the sitemap XSD for the sitemap.
- Parity tests run `awesome-lint` over every fixture readme. A fixture our rules
  accept but awesome-lint rejects fails the gate. The linter wins ties. Where we
  are deliberately stricter, the test records why: awesome-lint 2.3.0 treats a
  missing TOC as acceptable, while awesome.re's PR template requires a `Contents`
  section, so `check_toc_freshness` fails a readme with no TOC.
- Idempotence: `make toc` twice equals once, `make export` twice is
  byte-identical, `make jobs-due` twice does the second run's worth of nothing.

### Coverage gates

- 100% statements and branches for `parse/`, `rules/`, `toc/`, `slug/`, and
  `submission/`.
- 90% floor overall, excluding `cli/` argument parsing and `site/templates/`.
- Enforced by `pytest --cov --cov-branch --cov-fail-under`, not by an optional
  job.

### Guardrails

Each row maps to a test in `tests/guardrails/`. A change that breaks a constraint
fails the gate instead of shipping.

- `readme_is_never_written_by_build`: run the build, assert `readme.md` is
  byte-identical.
- `no_generated_prose`: the issue-to-PR path asserts the entry description equals
  the issue form field character for character.
- `no_auto_merge_on_readme`: the auto-merge config never lists `readme.md`, in
  Renovate or in a local script.
- `checks_are_not_actions_only`: every check has a `make` target and a caller in
  `ci/check.sh` or `jobs/`.
- `prepush_runs_full_check`: the pre-push hook invokes `make check`, parsed from
  the hook file.
- `only_toc_and_stats_write_the_readme`: no other CLI module writes `readme.md`,
  and `make stats-check` is in the gate and never shells out to `gh`.
- `sources_report_is_never_a_readme_write`: `make sources` writes only the
  report file.
- `network_calls_live_in_one_module`: `subprocess` appears in
  `github/fetch_repo_stats.py` and `cli/run_hooks_install.py` and nowhere else.
- `prettier_preserves_prose`: assert the config plus a paragraph round-trip.
- `no_ci_badge_or_list_topics`: the template repo has neither the badge nor the
  `awesome` and `awesome-list` topics.
- `toc_shape`: generated TOC is first, one level deep, free of denied sections.
- `no_archived_url_in_main_list`: no main-list entry points at an archive
  location, while `legacy.md` may.
- `local_archive_stays_opt_in`: with `links.archive = "off"`, no file is written
  under `archive/`.
- `guideline_pin_currency`: every rule cites a source URL, line, and hash.

## Guideline compliance as a hard constraint

Compliance drives the design. Two sources of truth, pinned by commit SHA and
content hash in `src/awesome_list/submission/awesome_re_rules.py`:

- `sindresorhus/awesome`: `awesome.md`, `pull_request_template.md`,
  `create-list.md`, `contributing.md`.
- `awesome-lint` 2.3.0, the executable subset of the same conventions.

Resolution order when they disagree: the awesome.re files win, and the template
satisfies both wherever possible. Where this spec is stricter on purpose, the
rule cites both sources and states the difference. A weekly job re-fetches the
upstream files, compares hashes, and opens an issue when the requirements move.

### What automation may never do

| Guideline                                                                                                                                                                             | Constraint on the automation                                                                                                                                                         |
| ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| "Is not AI-generated", "Fully AI-generated pull requests are not accepted"                                                                                                            | No automation writes entry text, section prose, or descriptions. The triage job copies the contributor's own words verbatim. Commits made by a bot carry a trailer naming the tool.  |
| "Does not contain items that are unmaintained, has archived repo, deprecated, or missing docs. If you really need to include such items, they should be in a separate Markdown file." | Dead entry handling never rewrites a main-list URL to an archive. The entry moves to `legacy.md`, with a local single-file copy in `archive/` when `links.archive = "local"` is set. |
| "Has a Table of Contents section", named `Contents`, first section, one level of nesting at most, no `Contributing` or `Footnotes` line                                               | `sync_contents` emits exactly that shape, and `check_toc_freshness` fails any readme that departs from it.                                                                           |
| "Does not use hard-wrapping"                                                                                                                                                          | Prettier runs with `proseWrap: "preserve"`, and the generator never wraps lines it writes. A test asserts the setting.                                                               |
| "Does not include a CI badge"                                                                                                                                                         | The badge check is a rule, not a habit. The template repo itself carries no CI badge and no `awesome` or `awesome-list` topic, because it is not a list.                             |
| "Non-generated Markdown file in a GitHub repo"                                                                                                                                        | `readme.md` is human-authored prose. The build reads it and never writes it. Only the Contents block is machine-managed, and only when `make toc` asks.                              |
| "Only has awesome items"                                                                                                                                                              | No automation adds an entry. Every entry change goes through human review, and auto-merge is limited to dependency and tooling files.                                                |
| "You have to review at least 4 other open pull requests", and the other process rules                                                                                                 | The readiness report prints these as manual items with the upstream wording, so they are surfaced rather than silently skipped.                                                      |

## Submission compliance (what `make submission-check` encodes)

Every row is a data entry in `awesome_re_rules.py` carrying the upstream file,
line, and content hash it came from.

| Requirement                                                                                                                                                                                                               | How it is checked                                                  |
| ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------ |
| Repo name is lowercase slug `awesome-<name>`                                                                                                                                                                              | local directory plus `origin` URL                                  |
| Heading is `# Awesome Name`, title case                                                                                                                                                                                   | parse H1, compare against config                                   |
| Topic description at the top of the readme, not a description of the list itself (rejected upstream: "Resources and tools for iOS development", "Awesome Framer packages and tools")                                      | first paragraph plus a phrasing rule with a fix hint               |
| Badge present, unmodified, right of the heading, link resolves. Upstream says the badge should link back to the list while the manifesto shows a link to awesome.re, so either is accepted and a working link is required | token stream plus link check                                       |
| If a header image is present it links out, and the heading does not repeat its wording                                                                                                                                    | token stream plus alt text comparison                              |
| `Contents` section named exactly `Contents`, and it is the first section                                                                                                                                                  | token stream                                                       |
| One level of nesting in the TOC at most                                                                                                                                                                                   | token stream                                                       |
| `Contributing`, `Footnotes`, and `Related Lists` absent from the TOC                                                                                                                                                      | token stream, matching awesome-lint's denylist                     |
| Entries use `- [Name](url) - Description.`                                                                                                                                                                                | `check_entry_grammar`                                              |
| Descriptions start uppercase and end with a period                                                                                                                                                                        | `check_entry_grammar`                                              |
| No hard wrapping                                                                                                                                                                                                          | line length plus paragraph reconstruction                          |
| No duplicate URLs                                                                                                                                                                                                         | `check_duplicate_urls`                                             |
| No archived, deprecated, or unmaintained entry in the main list                                                                                                                                                           | `check_entry_status`                                               |
| Repo has topics `awesome` and `awesome-list`                                                                                                                                                                              | GitHub API through `gh`                                            |
| Repo description set                                                                                                                                                                                                      | GitHub API                                                         |
| License detected by GitHub, CC family                                                                                                                                                                                     | GitHub API plus the `license` file                                 |
| Repo at least 30 days old                                                                                                                                                                                                 | GitHub API, first commit date                                      |
| No CI badge in readme                                                                                                                                                                                                     | awesome-lint rule plus a local check, `no_ci_badge_or_list_topics` |
| `contributing.md` exists                                                                                                                                                                                                  | file check                                                         |
| `code-of-conduct.md` exists and is Contributor Covenant 2.1                                                                                                                                                               | file check plus a heading marker                                   |
| Default branch is `main`                                                                                                                                                                                                  | `git symbolic-ref`                                                 |
| No `Inspired by awesome-<x>` line near the top                                                                                                                                                                            | token stream                                                       |
| Non-generated Markdown in a GitHub repo                                                                                                                                                                                   | file check plus `readme_is_never_written_by_build`                 |
| Not a duplicate list                                                                                                                                                                                                      | manual, printed reminder                                           |
| At least 4 reviewed open PRs at submission time                                                                                                                                                                           | manual, printed reminder                                           |
| Not AI-generated content                                                                                                                                                                                                  | manual reminder plus the bot trailer audit                         |
| At least one human-authored entry edit in the history                                                                                                                                                                     | git log plus the bot trailer convention                            |

## Migration of existing lists

`code/awesome-kiwi-data` and `code/awesome-olitreadwell` move onto this engine.
Order matters.

1. Extract the reusable parts of `awesome-kiwi-data/scripts/build_site.py` and
   `validate_readme.py` into `src/awesome_list/`, with tests written first. The
   glyph vocabulary (type, access, status) becomes `awesome.toml` config.
2. Run the engine against each existing list in report-only mode:
   `make list-check --report-only` prints violations and exits zero.
3. Fix or accept each violation in a reviewed commit. Nothing is auto-fixed.
4. Flip that list to enforcing: `list-check` fails the pre-push hook.
5. Only then turn on the site for a list that wants one. `awesome-kiwi-data`
   already publishes a site, so its existing output is compared against the
   engine's output before the old scripts are deleted.

`docs/migration.md` records the per-list state so a half-migrated list is never a
mystery.

## Boundaries

Always:

- Run `make check` before offering a branch for review, and let pre-push run it.
- Run `make hooks-install` after cloning.
- Write the failing test or failing fixture first.
- Update `readme.md` as the source of truth, then regenerate. Never hand-edit
  generated output.
- Keep `awesome-lint` passing, including its TOC and list-item rules.
- Run `make compliance-audit` whenever `readme.md`, `awesome.toml`, or anything
  under `src/awesome_list/submission/` changes.

Ask first:

- Changing the entry model or `schemas/`.
- Adding a dependency.
- Changing the tag vocabulary in `awesome.toml`.
- Editing a recorded guideline rule or the source it cites.
- Turning on the site, local archiving, auto-merge, or issue-to-PR.
- Migrating another list onto the engine.

Never:

- Commit generated output to `main`, or commit a CI badge into `readme.md`.
  awesome.re rejects CI badges in the readme.
- Auto-merge to `main` without review, or auto-merge any path that reaches
  `readme.md`.
- Add a license section to `readme.md`. A code license is wrong for a list, and
  the license belongs in `license` only.
- Generate list entries with an LLM, or let a bot write entry text, section
  prose, or a description.
- Point a main-list entry at an archived copy or a deprecated tool. It moves to
  `legacy.md` or it comes out.
- Put the awesome badge, or the `awesome` and `awesome-list` topics, on this
  template repo. It is a template, not a list.
- Make a hosted workflow the only path to a check. `ci/adapters/` is optional,
  and `checks_are_not_actions_only` enforces it.
- Commit secrets. `gitleaks` runs in the pre-commit hook and nightly.
- Disable a rule or skip a test to make a branch pass.

## Success Criteria

S1. `make check` passes on a fresh clone on macOS and Linux, on Python 3.12,
3.13, and 3.14, with no CI provider configured, in under 5 minutes on a
laptop.
S2. Only `readme.md` and `awesome.toml` edited, `make submission-check` reports
every automatable requirement as pass and prints the manual items.
S3. `make export` writes `data.json`, `data.csv`, `feed.xml`, and `sitemap.xml`;
`data.json` validates against `schemas/data.schema.json`; entry count equals
the count of entry bullets in the readme.
S4. A duplicate URL, a description without a trailing period, and a relative URL
each fail `make list-check` with rule name, file, line, and fix hint.
S5. A stale TOC fails `make toc-check`; `make toc` rewrites it; a second run
produces no diff.
S6. `make links-diff` on a 20-URL branch completes under 60 seconds and does not
fail on 429 or bot-wall responses after retries and allowlisting.
S7. `make jobs-links` opens one issue titled `Link check: <n> broken links`,
updates that issue instead of opening a second one, and closes it when the
list is clean.
S8. With `site.enabled = false`, no `site/` directory is produced, no Playwright
or Lighthouse run happens, and `make check` is unaffected. With it true, the
site builds, axe reports zero serious or critical violations, and Lighthouse
accessibility is 100.
S9. Every rule in `src/awesome_list/rules/` has a clean fixture, a dirty fixture,
and a test that failed before the rule existed.
S10. Coverage gates in Testing Strategy hold in CI-less local runs, and lowering
a gate requires a review comment on the branch that attempts it.
S11. `make compliance-audit` passes: every recorded guideline rule cites a source
URL, line, and hash; awesome-lint is clean on the fixture readme; the
guardrail tests pass.
S12. The build never writes `readme.md`. A test runs the full build and asserts
the file is byte-identical afterward, and only `make toc` changes it.
S13. Weekly drift reports a changed upstream requirement as an issue within 7
days of the change, and names the rule that needs updating.
S14. A seeded regression is caught by the pre-push hook, and the push is refused
without `--no-verify`.
S15. `make jobs-due` after a two week gap runs every overdue job once, in order,
and a second run does nothing.
S16. No check requires GitHub Actions. Disabling Actions in a scratch repo
changes nothing about `make check`, `make jobs-due`, or publishing.
S17. With `links.archive = "off"`, a dead entry produces a report and nothing
else. With `"local"`, the page is saved under `archive/`, the entry moves to
`legacy.md`, and the main list gains no archive URL.
S19. With `[github] stats = true`, an entry that links a repository without a
stats segment fails `make list-check` and names `make stats` as the fix. `make
stats` adds the segment and writes `github-stats.json`, `make stats-check`
passes with no network, a snapshot older than `max_age_days` warns instead of
failing, and `make stats` run while `gh` is unreachable leaves both files byte
identical.

S18. `awesome-kiwi-data` and `awesome-olitreadwell` both pass
`make list-check` after migration, with their existing entries intact
except for violations recorded in `docs/migration.md`.

## Open Questions

1. Issue-to-PR: this is the automation where the triage job turns a verified
   issue into a branch. The label question is whether it should stop at a
   verified comment (a human copies the entry in) or open the branch itself once
   a maintainer adds a label. Default in this spec is opt-in, off, because the
   guidelines care about who wrote the text: the bot would copy the
   contributor's own description, never author it.
2. Scheduler host: launchd on this Mac as the primary, with systemd and cron as
   documented alternates, and `jobs/run-due.sh` covering sleep.
3. Publish host: `gh-pages` branch with Pages deploy-from-branch by default,
   with Cloudflare Pages and Netlify direct upload documented.
4. Does `ci/adapters/` ship at all, or is it dropped so nobody is tempted to make
   the adapter the only path? Default is ship, commented, not installed.
5. Are E2E and Lighthouse in pre-push when the site is on, or in
   `make check-full` plus the nightly audit? Default is check-full.
6. Local archive size policy: cap per file and per total (`archive.` limits in
   `awesome.toml`), and whether archives are committed or gitignored with an
   example kept. Default is gitignored plus a documented example.
7. Migration order: `awesome-kiwi-data` first, since it has the parser and site
   to port, or `awesome-olitreadwell` first, since it is the smaller target?
8. `awesome.toml` versus `awesome.json`: the spec says TOML for comments and the
   standard library reader, and switching later is cheap.
