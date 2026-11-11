#!/usr/bin/env bash
# Scan for secrets with gitleaks.
#   secret-scan.sh            staged changes (pre-commit)
#   secret-scan.sh A..B       a commit range (CI)
# Finds gitleaks via $GITLEAKS, then PATH, then a Tools folder next to the dstack folder.
set -euo pipefail

here="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
tools="$here/../../Tools"
bin="${GITLEAKS:-}"
if [ -z "$bin" ]; then
  bin="$(command -v gitleaks || true)"
fi
for candidate in "$tools/gitleaks.exe" "$tools/gitleaks"; do
  if [ -z "$bin" ] && [ -x "$candidate" ]; then bin="$candidate"; fi
done
if [ -z "$bin" ]; then
  echo "dstack: gitleaks not found. Put it on PATH, in ../Tools next to dstack, or set GITLEAKS (see dstack README)." >&2
  exit 1
fi

if [ $# -eq 0 ]; then
  "$bin" git --pre-commit --staged --redact --no-banner -v .
else
  "$bin" git --log-opts="$1" --redact --no-banner -v .
fi
