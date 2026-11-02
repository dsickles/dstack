"""Pure rule logic shared by the git hooks, the CI guard and the Claude hooks.

No I/O here, so every rule is unit-tested in tests/test_rules.py.
"""

import re
import shlex

TYPES = "feat|fix|chore|docs|refactor|test|perf|build|ci|style|revert"
SCOPE = r"(\([a-z0-9._/-]+\))?"

CONVENTIONAL = re.compile(rf"^({TYPES}){SCOPE}!?: \S")
ALMANAC = re.compile(r"^(capture|triage|harvest|health|context): \S")
MERGE = re.compile(r"^Merge (branch|pull request|remote-tracking branch) ")
REVERT = re.compile(r'^Revert ".+"')
AUTOSQUASH = re.compile(r"^(fixup|squash|amend)! ")

PR_TITLE = re.compile(rf"^({TYPES}){SCOPE}!?: \S.* \(DAS-\d+\)$")
AUTOMATION_PR = re.compile(r"^chore\([a-z0-9-]+\): \S")


def commit_msg_ok(message: str) -> bool:
    """The first non-comment line must be a conventional, Almanac, merge or revert subject."""
    lines = [l for l in message.splitlines() if l.strip() and not l.startswith("#")]
    if not lines:
        return False
    subject = lines[0]
    return any(p.match(subject) for p in (CONVENTIONAL, ALMANAC, MERGE, REVERT, AUTOSQUASH))


def pr_title_ok(title: str) -> bool:
    """`type: summary (DAS-n)`, or a `chore(<bot>): ...` automation PR."""
    return bool(PR_TITLE.match(title) or AUTOMATION_PR.match(title))


# Verbs that put words in front of a person. Matched on the tool's own name, not the
# server's, because MCP server names are often opaque ids.
MESSAGE_VERB = re.compile(
    r"(^|_)(send|reply|forward|invite|post_message|create_event|update_event)(_|$)"
)


def gate_decision(tool_name: str):
    """Return "ask" for MCP tools that message people for Dan, else None."""
    if not tool_name.startswith("mcp__"):
        return None
    server, _, tool = tool_name[len("mcp__"):].partition("__")
    if server.startswith("ccd_"):  # Claude app internals (sessions, panes), not people
        return None
    return "ask" if MESSAGE_VERB.search(tool.lower()) else None


AUTONOMY = re.compile(r"Autonomy level:\**\s*(\d)", re.IGNORECASE)


def parse_autonomy(agents_md):
    """Read the autonomy level (1-3) from an AGENTS.md, or None if absent."""
    if not agents_md:
        return None
    m = AUTONOMY.search(agents_md)
    return int(m.group(1)) if m else None


PROTECTED = {"main", "master"}


def _segments(command: str):
    return [s for s in re.split(r"&&|\|\||;|\|", command) if s.strip()]


def _words(segment: str):
    try:
        return shlex.split(segment)
    except ValueError:
        return segment.split()


def _pushes_protected(words, current_branch) -> bool:
    i = words.index("push")
    targets = [w for w in words[i + 1:] if not w.startswith("-")]
    refspecs = targets[1:]  # targets[0] is the remote
    if not refspecs:
        return current_branch in PROTECTED
    for ref in refspecs:
        dest = ref.lstrip("+").split(":")[-1]
        dest = dest.removeprefix("refs/heads/")
        if dest in PROTECTED:
            return True
    return False


def merge_guard_decision(tool_name, tool_input, autonomy, current_branch):
    """Return "deny" when an agent tries to merge or push to main below autonomy level 3."""
    if autonomy == 3:
        return None
    if tool_name.startswith("mcp__"):
        tool = tool_name.rpartition("__")[2].lower()
        return "deny" if "merge" in tool else None
    if tool_name != "Bash":
        return None
    for segment in _segments(tool_input.get("command", "")):
        words = _words(segment)
        if words[:3] == ["gh", "pr", "merge"]:
            return "deny"
        if len(words) >= 2 and words[0] == "git" and "push" in words:
            if _pushes_protected(words, current_branch):
                return "deny"
    return None
