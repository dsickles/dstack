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

PR_TITLE = re.compile(rf"^({TYPES}){SCOPE}!?: \S.* \(DAS-\d+\)$")
AUTOMATION_PR = re.compile(r"^chore\([a-z0-9-]+\): \S")


def commit_msg_ok(message: str) -> bool:
    """The first non-comment line must be a conventional, Almanac, merge or revert subject."""
    lines = [l for l in message.splitlines() if l.strip() and not l.startswith("#")]
    if not lines:
        return False
    subject = lines[0]
    return any(p.match(subject) for p in (CONVENTIONAL, ALMANAC, MERGE, REVERT))


def pr_title_ok(title: str) -> bool:
    """`type: summary (DAS-n)`, or a `chore(<bot>): ...` automation PR."""
    return bool(PR_TITLE.match(title) or AUTOMATION_PR.match(title))


# Verbs that put words in front of a person. Matched on the tool's own name, not the
# server's, because MCP server names are often opaque ids.
MESSAGE_VERB = re.compile(
    r"(^|_)(send|reply|forward|invite|post_message|create_event|update_event)s?(_|$)"
)


def _snake(name: str) -> str:
    """sendEmail and SendEmail become send_email, so camelCase tools match too."""
    return re.sub(r"([a-z0-9])([A-Z])", r"\1_\2", name).lower()


def gate_decision(tool_name: str):
    """Return "ask" for MCP tools that message people for Dan, else None."""
    if not tool_name.startswith("mcp__"):
        return None
    server, _, tool = tool_name[len("mcp__"):].partition("__")
    if server.startswith("ccd_"):  # Claude app internals (sessions, panes), not people
        return None
    return "ask" if MESSAGE_VERB.search(_snake(tool)) else None


# The declaration line only: "**Autonomy level:** 2 Build" or "Autonomy level: 2".
AUTONOMY = re.compile(r"^\**Autonomy level:\**\s*(\d+)\b", re.IGNORECASE | re.MULTILINE)


def parse_autonomy(agents_md):
    """Read the autonomy level (1-3) from an AGENTS.md, or None if absent or unclear.

    Several declarations resolve to the lowest, so a stray line can only tighten the guard.
    """
    if not agents_md:
        return None
    levels = {int(m.group(1)) for m in AUTONOMY.finditer(agents_md)}
    if not levels or not levels <= {1, 2, 3}:
        return None
    return min(levels)


PROTECTED = {"main", "master"}

# gh pr merge anywhere in the command (newlines, env prefixes, bash -c, gh.exe), and the
# REST merge endpoint through gh api.
GH_MERGE = re.compile(r"\bgh(\.exe)?['\"]?\s+pr\s+merge\b", re.IGNORECASE)
GH_API_MERGE = re.compile(r"\bgh(\.exe)?\s+api\b[^\n;|&]*pulls/[^\s/]+/merge\b", re.IGNORECASE)
PUSH_ALL = {"--all", "--mirror", "--branches"}


def _segments(command: str):
    return [s for s in re.split(r"&&|\|\||;|\||\n", command) if s.strip()]


def _words(segment: str):
    try:
        return shlex.split(segment)
    except ValueError:
        return segment.split()


def _push_default(words, configured):
    """`git -c push.default=X push` overrides the configured value."""
    for i, w in enumerate(words):
        if w == "-c" and i + 1 < len(words) and words[i + 1].startswith("push.default="):
            return words[i + 1].split("=", 1)[1]
    return configured


def _pushes_protected(words, current_branch, upstream, push_default) -> bool:
    i = words.index("push")
    args = words[i + 1:]
    if PUSH_ALL & set(args):
        return True
    targets = [w for w in args if not w.startswith("-")]
    refspecs = targets[1:]  # targets[0] is the remote
    if not refspecs:
        # No refspec: git decides from the branch, its upstream and push.default.
        return (current_branch in PROTECTED or upstream in PROTECTED
                or _push_default(words[:i], push_default) == "matching")
    for ref in refspecs:
        dest = ref.lstrip("+").split(":")[-1]
        dest = dest.removeprefix("refs/heads/")
        if dest in ("HEAD", "@"):
            dest = current_branch
        if dest in PROTECTED:
            return True
    return False


def merge_guard_decision(tool_name, tool_input, autonomy, current_branch,
                         upstream=None, push_default=None):
    """Return "deny" when an agent tries to merge or push to main below autonomy level 3.

    upstream is the remote branch the current branch tracks (e.g. "main"); push_default is
    git's configured push.default.
    """
    if autonomy == 3:
        return None
    if tool_name.startswith("mcp__"):
        tool = tool_name.rpartition("__")[2].lower()
        return "deny" if "merge" in tool else None
    if tool_name != "Bash":
        return None
    command = tool_input["command"]
    if not isinstance(command, str):
        raise TypeError("Bash command is not a string")
    if GH_MERGE.search(command) or GH_API_MERGE.search(command):
        return "deny"
    for segment in _segments(command):
        words = _words(segment)
        if len(words) >= 2 and words[0] == "git" and "push" in words:
            if _pushes_protected(words, current_branch, upstream, push_default):
                return "deny"
    return None
