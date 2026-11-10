#!/usr/bin/env bash
# dstack's one check command. CI runs this; run it before calling work done.
set -euo pipefail
cd "$(dirname "${BASH_SOURCE[0]}")/.."
py="$(command -v python3 || command -v python)"

echo "== unit tests"
"$py" -m unittest discover -s tests

echo "== JSON files parse"
for f in hooks/hooks.json .claude-plugin/plugin.json .claude-plugin/marketplace.json templates/claude-settings.json; do
  "$py" -c "import json,sys; json.load(open(sys.argv[1], encoding='utf-8'))" "$f"
done

echo "== shell scripts parse"
for f in scripts/*.sh git-hooks/*; do
  bash -n "$f"
done

echo "== always-loaded docs stay under 150 lines"
for f in HOW-I-WORK.md AGENTS.md templates/AGENTS.md; do
  n=$(wc -l < "$f")
  if [ "$n" -gt 150 ]; then echo "$f is $n lines (limit 150)" >&2; exit 1; fi
done

echo "check passed"
