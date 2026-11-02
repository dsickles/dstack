"""Claude PreToolUse hook: the message approval gate and the merge guard.

Reads the hook payload on stdin. Prints a decision only when one applies; otherwise
exits silently so Claude's normal permission rules decide.
"""

import json
import os
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "lib"))

import rules  # noqa: E402


def _decision(kind, reason):
    return {"hookSpecificOutput": {"hookEventName": "PreToolUse",
                                   "permissionDecision": kind,
                                   "permissionDecisionReason": reason}}


def _repo_state(cwd):
    project = Path(os.environ.get("CLAUDE_PROJECT_DIR") or cwd or os.getcwd())
    agents = project / "AGENTS.md"
    autonomy = rules.parse_autonomy(agents.read_text(encoding="utf-8")) if agents.exists() else None
    try:
        branch = subprocess.run(["git", "branch", "--show-current"], cwd=cwd or project,
                                capture_output=True, text=True, timeout=5).stdout.strip()
    except (OSError, subprocess.TimeoutExpired):
        branch = ""
    return autonomy, branch


def decide(payload):
    tool = payload.get("tool_name", "")
    tool_input = payload.get("tool_input") or {}

    if tool == "Bash" or (tool.startswith("mcp__") and "merge" in tool.rpartition("__")[2].lower()):
        autonomy, branch = _repo_state(payload.get("cwd"))
        if rules.merge_guard_decision(tool, tool_input, autonomy, branch) == "deny":
            return _decision("deny", "dstack merge guard: Dan merges, and agents never push to main "
                                     "below autonomy level 3. Push a branch and open a PR instead.")

    if rules.gate_decision(tool) == "ask":
        return _decision("ask", f"dstack approval gate: {tool} sends a message to a person for Dan. "
                                "Approve only if Dan saw the exact text and recipients.")
    return None


def main() -> int:
    try:
        payload = json.load(sys.stdin)
    except ValueError:
        return 0
    result = decide(payload)
    if result:
        print(json.dumps(result))
    return 0


if __name__ == "__main__":
    sys.exit(main())
