#!/usr/bin/env bash
# Run any scheduled job whose last success is older than its interval.
#
# A laptop that sleeps misses schedules. Each job records when it last
# succeeded in .state/<job>.last, and this tick runs whatever is overdue.
#
#   jobs/run-due.sh            run anything overdue
#   jobs/run-due.sh --list     print the schedule and exit
set -euo pipefail

cd "$(dirname "$0")/.."

STATE_DIR="${STATE_DIR:-.state}"
DEFAULT_INTERVAL_DAYS=7
JOBS="${JOBS:-links stats drift}"

if [[ "${1:-}" == "--list" ]]; then
  for job in $JOBS; do
    printf '%s\t%s\n' "$job" "$DEFAULT_INTERVAL_DAYS"
  done
  exit 0
fi

mkdir -p "$STATE_DIR"
now=$(date -u +%s)
ran=0

for job in $JOBS; do
  script="jobs/$job.sh"
  [[ -x "$script" ]] || continue
  stamp="$STATE_DIR/$job.last"
  due=1
  if [[ -f "$stamp" ]]; then
    last=$(cat "$stamp")
    if [[ "$last" =~ ^[0-9]+$ ]]; then
      age=$(( (now - last) / 86400 ))
      (( age < DEFAULT_INTERVAL_DAYS )) && due=0
    fi
  fi
  if (( due )); then
    echo "run-due: $job is overdue, running $script"
    if "$script"; then
      date -u +%s > "$stamp"
      ran=$(( ran + 1 ))
    else
      echo "run-due: $job failed; the stamp was left alone" >&2
    fi
  else
    echo "run-due: $job is up to date"
  fi
done

echo "run-due: ran $ran job(s)"
