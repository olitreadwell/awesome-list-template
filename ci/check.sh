#!/usr/bin/env bash
# The one command any runner calls. It runs make check and nothing else.
set -euo pipefail
cd "$(dirname "$0")/.."
exec make check
