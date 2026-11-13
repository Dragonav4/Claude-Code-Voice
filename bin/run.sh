#!/bin/sh
# Runs a plugin script with a real Python 3.10+.
#
# Claude Code runs hooks through sh/bash on every OS (Git Bash on Windows).
# On Windows `python3` is often a Microsoft Store stub that exits with code 49,
# so each candidate is checked before use. Usage: run.sh <script.py> [args...]

for candidate in python3 python py; do
  if command -v "$candidate" >/dev/null 2>&1 &&
    "$candidate" -c 'import sys; sys.exit(sys.version_info < (3, 10))' >/dev/null 2>&1; then
    exec "$candidate" "$@"
  fi
done

echo "voice-personas: Python 3.10+ not found (tried python3, python, py)" >&2
exit 0  # a missing Python must never block Claude Code
