"""Claude SessionStart hook: is this repo set up, and is the checkout current?

Prints plain text; Claude adds it to the session context.
"""

import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "lib"))

import config  # noqa: E402


def _git(repo, *args, timeout=10):
    try:
        r = subprocess.run(["git", *args], cwd=repo, capture_output=True, text=True, timeout=timeout)
    except (OSError, subprocess.TimeoutExpired):
        return None
    return r.stdout.strip() if r.returncode == 0 else None


def include_global_rules(env) -> bool:
    """Cloud sessions have no ~/.claude/CLAUDE.md, so they get GLOBAL-AGENTS.md from here."""
    return env.get("CLAUDE_CODE_REMOTE", "").lower() == "true"


def report(repo: Path, fetch: bool = True) -> str:
    repo = Path(repo)
    lines = ["dstack session check:"]
    if not (repo / "AGENTS.md").exists() or not (repo / "docs" / "agents").is_dir():
        lines.append(
            "- This repo is not set up for the dstack workflow (no AGENTS.md or docs/agents/). "
            "Before building anything, suggest running /kickoff."
        )
    if _git(repo, "rev-parse", "--is-inside-work-tree") != "true":
        return "\n".join(lines)

    branch = _git(repo, "branch", "--show-current") or "(detached)"
    lines.append(f"- Branch: {branch}")
    status = _git(repo, "status", "--porcelain") or ""
    changed = len([l for l in status.splitlines() if l.strip()])
    if changed:
        lines.append(f"- {changed} uncommitted change(s). Ask the owner before touching changes you didn't make.")

    if fetch and _git(repo, "fetch", "--quiet", timeout=15) is None:
        lines.append("- Could not reach GitHub to check for newer commits.")
    behind = _git(repo, "rev-list", "--count", "HEAD..@{u}")
    if behind and behind != "0":
        lines.append(f"- {behind} commits behind GitHub. Tell the owner and pull before starting work.")
    return "\n".join(lines)


def main() -> int:
    repo = Path(os.environ.get("CLAUDE_PROJECT_DIR") or os.getcwd())
    print(report(repo))
    print("\n" + config.describe(config.load(repo)))
    if include_global_rules(os.environ):
        rules_file = ROOT / "GLOBAL-AGENTS.md"
        if rules_file.exists():
            print("\n" + rules_file.read_text(encoding="utf-8"))
    return 0


if __name__ == "__main__":
    sys.exit(main())
