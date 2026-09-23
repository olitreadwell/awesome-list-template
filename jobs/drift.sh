#!/usr/bin/env bash
# Weekly upstream drift check: has sindresorhus/awesome changed the rules?
#
# The guideline registry is not written yet. Until it exists this job says so
# and exits zero, so a schedule that runs it is never red for nothing.
set -euo pipefail

cd "$(dirname "$0")/.."

registry="src/awesome_list/submission/awesome_re_rules.py"
if [[ ! -f "$registry" ]]; then
  echo "drift: $registry is not written yet; nothing to compare against upstream"
  exit 0
fi

echo "drift: comparing $registry against upstream"
uv run python -m awesome_list.cli.run_submission_check --drift
