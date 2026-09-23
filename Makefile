SHELL := /bin/bash
.DEFAULT_GOAL := check

READMES := readme.md

.PHONY: install check check-fast fix coverage lint typecheck format fmt-check \
	list-check toc toc-check stats stats-check sources export site \
	submission-check \
	compliance-audit \
	links links-diff jobs-due jobs-links jobs-drift jobs-triage jobs-publish \
	hooks-install repo-setup test docs-serve

install:
	uv sync --frozen --group dev
	cd tools && npm ci

# export, site, and e2e join this list once those modules exist.
check: lint typecheck fmt-check toc-check list-check stats-check awesome-lint coverage

check-fast:
	uv run ruff format --check --diff $(shell git diff --name-only --diff-filter=ACMR -- '*.py' 2>/dev/null || true)
	uv run codespell readme.md src tests
	uv run python -m awesome_list.cli.run_toc --check --readme tests/fixtures/readme/clean.md --config tests/fixtures/readme/awesome.toml
	uv run python -m awesome_list.cli.run_list_check --readme tests/fixtures/readme/clean.md --config tests/fixtures/readme/awesome.toml

check-full: check site e2e lighthouse

lint:
	uv run ruff check

typecheck:
	uv run mypy

format:
	uv run ruff format

fmt-check:
	uv run ruff format --check
	@test -x tools/node_modules/.bin/prettier || (echo "run: cd tools && npm ci" && exit 3)
	tools/node_modules/.bin/prettier --check .

fix:
	uv run ruff check --fix
	uv run ruff format
	uv run codespell --write-changes readme.md src tests

test:
	uv run pytest

coverage:
	uv run pytest --cov=awesome_list --cov-branch --cov-report=term-missing --cov-fail-under=90

list-check:
	uv run python -m awesome_list.cli.run_list_check --readme tests/fixtures/readme/clean.md --config tests/fixtures/readme/awesome.toml

stats:
	uv run python -m awesome_list.cli.run_stats --readme tests/fixtures/readme/github.md --config tests/fixtures/readme/awesome.toml

stats-check:
	uv run python -m awesome_list.cli.run_stats --check --readme tests/fixtures/readme/github.md --config tests/fixtures/readme/awesome.toml

sources:
	uv run python -m awesome_list.cli.run_sources --stdout

toc:
	uv run python -m awesome_list.cli.run_toc --readme tests/fixtures/readme/clean.md --config tests/fixtures/readme/awesome.toml

toc-check:
	uv run python -m awesome_list.cli.run_toc --check --readme tests/fixtures/readme/clean.md --config tests/fixtures/readme/awesome.toml

export:
	uv run python -m awesome_list.cli.run_export

site:
	uv run python -m awesome_list.cli.run_site

e2e:
	uv run pytest -m e2e

lighthouse:
	cd tools && npx @lhci/cli autorun --config=../lighthouserc.json

awesome-lint:
	ci/awesome-lint-fixture.sh

submission-check:
	uv run python -m awesome_list.cli.run_submission_check

compliance-audit:
	uv run python -m awesome_list.cli.run_compliance_audit

links:
	lychee --config lychee.toml readme.md

links-diff:
	uv run python -m awesome_list.cli.run_links_diff

jobs-due:
	jobs/run-due.sh

jobs-links:
	jobs/links.sh

jobs-drift:
	jobs/drift.sh

jobs-triage:
	jobs/triage.sh

jobs-publish:
	jobs/publish.sh

hooks-install:
	uv run python -m awesome_list.cli.run_hooks_install

repo-setup:
	uv run python -m awesome_list.cli.run_repo_setup

docs-serve:
	uv run python -m http.server --directory site 8000
