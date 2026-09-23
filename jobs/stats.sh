#!/usr/bin/env bash
# Weekly stats refresh. Commits the snapshot only when the numbers moved.
set -euo pipefail

cd "$(dirname "$0")/.."

make stats
if git diff --quiet -- github-stats.json; then
  echo "stats: nothing moved"
  exit 0
fi

git add github-stats.json
git -c user.email=bot@localhost -c user.name="awesome-list-bot" \
  commit -m "chore: refresh GitHub stars and activity"
echo "stats: committed the refreshed snapshot"
