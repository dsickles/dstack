#!/usr/bin/env bash
# Run a repo's own hook after dstack's: scripts/hooks/<name> (Ledger style), then
# .git/hooks/<name>. A global core.hooksPath hides both, so dstack calls them itself.
set -euo pipefail
name="$1"; shift
top="$(git rev-parse --show-toplevel)"
gitdir="$(git rev-parse --absolute-git-dir)"

for hook in "$top/scripts/hooks/$name" "$gitdir/hooks/$name"; do
  if [ -f "$hook" ]; then
    bash "$hook" "$@"
  fi
done
