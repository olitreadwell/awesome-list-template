#!/usr/bin/env bash
# Weekly link check. Runs lychee over the whole list and, with --open-issue,
# opens or updates the one issue that reports dead links.
set -euo pipefail

cd "$(dirname "$0")/.."

OPEN_ISSUE=0
[[ "${1:-}" == "--open-issue" ]] && OPEN_ISSUE=1

report="${REPORT:-reports/links.md}"
mkdir -p "$(dirname "$report")"

set +e
make links > "$report" 2>&1
status=$?
set -e

echo "links: lychee exited $status; wrote $report"

if (( OPEN_ISSUE )); then
  command -v gh >/dev/null || { echo "links: gh is not installed" >&2; exit "$status"; }
  title="Dead links in the list"
  existing=$(gh issue list --state open --search "$title in:title" --json number --jq '.[0].number // empty')
  if [[ -n "$existing" ]]; then
    gh issue comment "$existing" --body-file "$report"
    echo "links: commented on issue #$existing"
  else
    gh issue create --title "$title" --body-file "$report"
    echo "links: opened a new issue"
  fi
fi

exit "$status"
