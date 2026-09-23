#!/usr/bin/env bash
# Lint a fixture readme with awesome-lint, inside a scratch repository, so the
# template repo itself never has to look like an awesome list.
#
# Usage: ci/awesome-lint-fixture.sh [--fixture path/to/readme.md]
set -euo pipefail

root="$(cd "$(dirname "$0")/.." && pwd)"
fixture="$root/tests/fixtures/readme/clean.md"

while [[ $# -gt 0 ]]; do
  case "$1" in
    --fixture) fixture="$2"; shift 2 ;;
    *) echo "unknown argument: $1" >&2; exit 2 ;;
  esac
done

linter="$root/tools/node_modules/.bin/awesome-lint"
if [[ ! -x "$linter" ]]; then
  echo "awesome-lint-fixture: tools are not installed, run: cd tools && npm ci" >&2
  exit 3
fi

work="$(mktemp -d)"
trap 'rm -rf "$work"' EXIT

cp "$fixture" "$work/readme.md"
cp "$root/contributing.md" "$work/contributing.md"
cp "$root/code-of-conduct.md" "$work/code-of-conduct.md"
cp "$root/license" "$work/license"

git -C "$work" init -q
# The GitHub rule reads repository metadata, which says nothing about list
# content. Point the probe at a known-good list so that rule is satisfied and the
# report is about the fixture's entries.
git -C "$work" remote add origin https://github.com/sindresorhus/awesome-nodejs.git

output="$(cd "$work" && "$linter" readme.md 2>&1 || true)"
clean="$(printf '%s\n' "$output" | sed 's/\x1b\[[0-9;]*[a-zA-Z]//g')"
# The GitHub rule needs the repository this list lives in, which a scratch probe
# does not have, so its messages are dropped. Everything else must be clean.
problems="$(printf '%s\n' "$clean" \
  | grep -E '^[[:space:]]+✖[[:space:]]+[0-9]+:[0-9]+' \
  | grep -v 'awesome-github' || true)"

if [[ -n "$problems" ]]; then
  printf '%s\n' "$problems"
  exit 1
fi

echo "awesome-lint: clean ($(basename "$fixture"))"
