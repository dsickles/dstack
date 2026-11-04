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
UNKNOWN = "<unknown>"  # a value the command sets in a way the guard can't read

# gh pr merge anywhere in the raw text (catches bash -c '...' and echo too; fail-closed),
# and the REST merge endpoint through gh api. Quoted words are caught as tokens below.
GH_MERGE = re.compile(r"\bgh(\.exe)?['\"]?\s+pr\s+merge\b", re.IGNORECASE)
GH_API_MERGE = re.compile(r"\bgh(\.exe)?\s+api\b[^\n;|&]*pulls/[^\s/]+/merge\b", re.IGNORECASE)
API_MERGE_PATH = re.compile(r"pulls/[^\s/]+/merge\b", re.IGNORECASE)
PUSH_ALL = {"--all", "--mirror", "--branches"}
GIT_ENV = re.compile(r"\bGIT_(CONFIG|DIR|WORK_TREE)")  # env vars that change git's config
GIT_OPT_WITH_ARG = {"-c", "-C", "--git-dir", "--work-tree", "--namespace", "--config-env",
                    "--super-prefix"}
NEW_BRANCH_OPTS = {"-b", "-B", "-c", "-C", "--orphan"}
WRAPPERS = {"command", "builtin", "env", "exec", "sudo", "nohup", "time", "xargs"}
ASSIGNMENT = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*=")
NOT_ALIASABLE = {"push", "config", "checkout", "switch", "branch"}  # git ignores such aliases
INCLUDE = ("include.", "includeif.")


def _segments(command: str):
    return [s for s in re.split(r"&&|\|\||[;|&\n()`]", command) if s.strip()]


def _words(segment: str):
    try:
        return shlex.split(segment)
    except ValueError:
        return segment.split()


def _prog(word: str) -> str:
    """/usr/bin/git, git.exe, Git and (git all become git."""
    return re.split(r"[\\/]", word.lstrip("$({`"))[-1].lower().removesuffix(".exe")


def _config_key(key: str) -> str:
    """Section and key are case-insensitive; a subsection (branch name) is not."""
    parts = key.split(".")
    if len(parts) < 2:
        return key.lower()
    return ".".join([parts[0].lower(), *parts[1:-1], parts[-1].lower()])


def _multi(key: str) -> bool:
    return key.startswith("remote.") and key.endswith(".push")


def _set(config, key, value):
    """remote.<name>.push keeps every value (git pushes them all); other keys: last wins."""
    if _multi(key):
        config.setdefault(key, []).append(value)
    else:
        config[key] = value


def _merge(saved, cli):
    out = {k: list(v) if _multi(k) else v for k, v in saved.items()}
    for k, v in cli.items():
        out[k] = out.get(k, []) + v if _multi(k) else v
    return out


def _git_call(words, j):
    """Parse `git [global options] <subcommand> <args>` at words[j].

    Returns the subcommand, the `-c` settings, the arguments, where the subcommand sits,
    and whether -C/--git-dir/--work-tree point git at another repo.
    """
    config, elsewhere, i = {}, False, j + 1
    while i < len(words) and words[i].startswith("-"):
        name, eq, val = words[i].partition("=")
        if name in GIT_OPT_WITH_ARG and not eq:
            i += 1
            val = words[i] if i < len(words) else ""
        if name == "-c":
            key, _, value = val.partition("=")
            _set(config, _config_key(key), value or "true")
        elif name == "--config-env":
            _set(config, _config_key(val.partition("=")[0]), UNKNOWN)
        elif name in ("-C", "--git-dir", "--work-tree"):
            elsewhere = True
        i += 1
    sub = words[i] if i < len(words) else ""
    return sub, config, words[i + 1:], i, elsewhere


def _config_write(args):
    """`git config [--global|--add] key value` or `git config set key value`: (key, value)."""
    if any(a.startswith(("--get", "--unset", "--list", "--remove", "--rename", "-l"))
           for a in args):
        return None
    pos = [a for a in args if not a.startswith("-")]
    if pos and pos[0] in ("set", "get", "unset", "list"):
        if pos[0] != "set":
            return None
        pos = pos[1:]
    return (_config_key(pos[0]), pos[1]) if len(pos) >= 2 else None


def _checkout_target(args):
    """The branch `git checkout/switch` moves to, or None (e.g. `git checkout -- file`)."""
    for i, a in enumerate(args):
        if a in NEW_BRANCH_OPTS:
            return args[i + 1] if i + 1 < len(args) else UNKNOWN
        if a == "--":
            return None
        if a == "-" or a.startswith("@{"):  # the previous branch: can't tell which
            return UNKNOWN
        if not a.startswith("-"):
            return a
    return None


def _branch_cmd(args, st):
    """`git branch -m/-M` renames the current branch; `-u` sets its upstream."""
    pos = [a for a in args if not a.startswith("-")]
    up = None
    for i, a in enumerate(args):
        if a in ("-u", "--set-upstream-to"):
            up = args[i + 1] if i + 1 < len(args) else UNKNOWN
        elif a.startswith("--set-upstream-to="):
            up = a.partition("=")[2]
        elif a.startswith("-u") and not a.startswith("--"):
            up = a[2:]
    if up is not None:
        others = [p for p in pos if p != up]
        if not others or others[0] == st["branch"]:
            st["upstream"] = UNKNOWN if up == UNKNOWN else up.split("/", 1)[-1]
    elif {"-m", "-M", "--move"} & set(args):
        if len(pos) == 1 or (len(pos) == 2 and pos[0] in (st["branch"], UNKNOWN)):
            st["branch"] = pos[-1]


def _push_denied(args, branch, upstream, push_default, remote_push) -> bool:
    if PUSH_ALL & set(args):
        return True
    targets = [w for w in args if not w.startswith("-")]
    refspecs = targets[1:] or remote_push  # no refspec: git uses remote.<name>.push
    if not refspecs:  # then the branch, its upstream and push.default decide
        return (branch in PROTECTED or upstream in PROTECTED or UNKNOWN in (branch, upstream)
                or push_default in ("matching", UNKNOWN))
    for ref in refspecs:
        ref = ref.lstrip("+")
        if ref == UNKNOWN or "*" in ref or ref == ":":  # globs and ":" (matching) push main
            return True
        dest = ref.split(":")[-1].removeprefix("refs/heads/")
        if dest in ("HEAD", "@"):
            dest = branch
        if dest in PROTECTED or dest == UNKNOWN:
            return True
    return False


def _gh_merges(words) -> bool:
    for j, w in enumerate(words):
        if _prog(w) != "gh":
            continue
        rest = [x.lower() for x in words[j + 1:]]
        if rest[:2] == ["pr", "merge"]:
            return True
        if rest[:1] == ["api"] and any(API_MERGE_PATH.search(x) for x in rest[1:]):
            return True
    return False


def _first_command(words) -> str:
    for w in words:
        if not (ASSIGNMENT.match(w) or _prog(w) in WRAPPERS or w.startswith("-")):
            return _prog(w)
    return ""


def _git(words, j, st, depth) -> bool:
    """Check one git call; update the tracked state for calls that change it."""
    sub, cli, args, at, elsewhere = _git_call(words, j)
    cfg = _merge(st["config"], cli)
    alias = None if sub in NOT_ALIASABLE else cfg.get(f"alias.{sub.lower()}",
                                                          st["aliases"].get(sub.lower()))
    if alias:
        if alias == UNKNOWN:
            return True
        rest = " " + shlex.join(args) if args else ""
        if alias.startswith("!"):  # a shell alias runs as its own command
            return _walk(alias[1:] + rest, st, depth + 1)
        return _walk(shlex.join(words[j:at]) + " " + alias + rest, st, depth + 1)
    if sub == "config" and (kv := _config_write(args)):
        _set(st["config"], *kv)
    elif sub in ("checkout", "switch"):
        target = _checkout_target(args)
        if target and target != st["branch"]:
            st["branch"], st["upstream"] = target, UNKNOWN
    elif sub == "branch":
        _branch_cmd(args, st)
    elif sub == "push":
        b, up, pd = (UNKNOWN,) * 3 if elsewhere else (st["branch"], st["upstream"], st["push_default"])
        up = cfg.get(f"branch.{b}.merge", up)
        up = up.removeprefix("refs/heads/") if isinstance(up, str) else up
        pd = cfg.get("push.default", pd)
        remote_push = [v for k, vals in cfg.items() if _multi(k) for v in vals] + st["remote_push"]
        if st["opaque"] or any(k.startswith(INCLUDE) for k in cfg):  # config we can't read
            up, pd, remote_push = UNKNOWN, UNKNOWN, remote_push + [UNKNOWN]
        return _push_denied(args, b, up, pd, remote_push)
    return False


def _walk(command, st, depth=0) -> bool:
    """Walk the command in order, tracking what earlier parts change (cd, checkout,
    branch -m/-u, git config, aliases), and check every `git ... push` wherever git
    appears in a segment. Seeing git anywhere (e.g. `echo git push origin main`) is
    fail-closed on purpose.
    """
    if depth > 5:  # an alias loop: git refuses it, and so do we
        return True
    if GIT_ENV.search(command):
        st["opaque"] = True
    for segment in _segments(command):
        words = _words(segment)
        if _first_command(words) in ("cd", "pushd"):
            st.update(branch=UNKNOWN, upstream=UNKNOWN, push_default=UNKNOWN)
        for j, w in enumerate(words):
            if _prog(w) == "git" and _git(words, j, st, depth):
                return True
    return False


def merge_guard_decision(tool_name, tool_input, autonomy, current_branch,
                         upstream=None, push_default=None, remote_push=(), aliases=None):
    """Return "deny" when an agent tries to merge or push to main below autonomy level 3.

    The rest is the repo's saved git config: upstream is the branch the current branch
    tracks (e.g. "main"), push_default is push.default, remote_push lists every
    remote.<name>.push value, and aliases maps alias names (lowercase) to their bodies.
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
    if any(_gh_merges(_words(s)) for s in _segments(command)):
        return "deny"
    st = {"branch": current_branch, "upstream": upstream, "push_default": push_default,
          "remote_push": list(remote_push), "aliases": dict(aliases or {}), "config": {},
          "opaque": False}
    return "deny" if _walk(command, st) else None
