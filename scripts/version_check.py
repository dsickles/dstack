"""CI: a PR that changes what the plugin ships must raise plugin.json's version.

Usage: python3 scripts/version_check.py <base-sha>
"""

import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "lib"))

import rules  # noqa: E402

MANIFEST = ".claude-plugin/plugin.json"


def _git(repo, *args):
    return subprocess.run(["git", *args], cwd=repo, check=True, capture_output=True,
                          text=True).stdout


def main(base: str, repo: Path = ROOT) -> int:
    if not base.strip():
        print("version check: no base commit given", file=sys.stderr)
        return 1
    # --no-renames lists a move as delete + add, so moving a file out of a shipped path
    # still counts as a shipped change.
    changed = _git(repo, "diff", "--no-renames", "--name-only", f"{base}...HEAD").splitlines()
    if not rules.version_bump_needed(changed):
        print("version check: no shipped files changed")
        return 0
    old = json.loads(_git(repo, "show", f"{base}:{MANIFEST}"))["version"]
    new = json.loads((Path(repo) / MANIFEST).read_text(encoding="utf-8"))["version"]
    if rules.version_raised(old, new):
        print(f"version check: {old} -> {new}")
        return 0
    print(f"version check: this PR changes what the plugin ships, so raise \"version\" in "
          f"{MANIFEST} above {old} (it is {new}). Without it, `claude plugin update` "
          f"keeps running sessions on the old copy.", file=sys.stderr)
    return 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1]))
