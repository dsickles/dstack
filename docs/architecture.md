# How dstack works

dstack is one repo used three ways: as a Claude Code plugin, as a folder other tools read,
and as a source of templates that `/kickoff` copies into other repos.

## Pieces

| Piece | Files | Used by |
|---|---|---|
| Build rules | `GLOBAL-AGENTS.md` | Claude via `~/.claude/CLAUDE.md` import (local) or the SessionStart hook (cloud); Cursor via a user rule |
| Owner config | `lib/config.py` reads `~/.dstack/config.json`, then the repo's `.dstack/config.json` | Claude hooks, the PR-title check, `guard.yml` (prefix only) |
| `/kickoff` skill | `skills/kickoff/SKILL.md` | Claude through the plugin |
| Templates | `templates/` | `/kickoff`, copied into each repo |
| Rule logic | `lib/rules.py` | git hooks, Claude hooks, tests |
| Git hooks | `git-hooks/` | every repo on the owner's PC via `git config --global core.hooksPath` |
| CI guard | `.github/workflows/guard.yml` | every repo's CI via `uses: dsickles/dstack/.github/workflows/guard.yml@main` |
| Claude hooks | `hooks/hooks.json`, `hooks/*.py` | Claude sessions with the plugin enabled |
| Leak check | `scripts/leak_check.py`, `scripts/leak-hashes.txt` | `check`, so CI |

## Enforcement layers

1. **Git hooks (the owner's PC).** `pre-commit` runs gitleaks on staged changes; `commit-msg`
   checks the message format. Each then runs the repo's own hook (`scripts/hooks/<name>`
   or `.git/hooks/<name>`), because a global hooks path hides them.
2. **CI (every PR).** `guard.yml` scans the PR's commits with gitleaks and checks the PR
   title, with the ticket prefix from the caller's `.dstack/config.json` (any upper-case
   key when there is none). It runs in the caller's checkout, so it carries a copy of the
   title rule; a test keeps that copy in sync with `lib/rules.py` and runs it.
   The repo's own job runs its `check`.
3. **Claude hooks (extra triggers).**
   - `SessionStart` (`session_start.py`): says "run /kickoff" in a repo without AGENTS.md or
     docs/agents/; otherwise reports branch, uncommitted changes and commits behind GitHub.
     It prints the owner config, so agents know who "the owner" is. In cloud sessions
     (`CLAUDE_CODE_REMOTE=true`) it also prints GLOBAL-AGENTS.md.
   - `PreToolUse` (`pretooluse.py`): the merge guard denies `gh pr merge`, MCP merge tools
     and pushes to main/master unless the project's AGENTS.md says autonomy level 3; the
     approval gate asks before MCP tools whose names send, reply, forward, invite or create
     calendar events. Linear and GitHub tools pass, and so do the Claude app's own tools
     (`ccd_*`, `hearthbot`, `claude-code-remote`), which reply to the owner in their project
     threads or wake the same session. Both hooks name the owner from config. If the hook can't read a call or crashes, it denies.

## How a repo gets dstack

`/kickoff` writes the repo's `.claude/settings.json` from `templates/claude-settings.json`,
which registers dstack as a plugin marketplace, enables the plugin, and pre-approves the
Linear and GitHub connector tools (`permissions.allow`). Cloud threads run Claude Code's own
safety check on each tool call, and it sometimes refused Linear writes the workflow needs
(seen 2026-11-11); pre-approved tools skip it. dstack's hooks run before allow rules, so
the merge guard's deny (merges, and GitHub connector writes to main) and the approval
gate's ask still apply.

Where those repo permissions load (Claude Code settings docs, checked 2026-11-11):

- **Threads in a claude.ai project:** never, however many repositories the project has.
  The cloud environment's setup script writes the same allow list into the session
  machine's own `~/.claude/settings.json` (README, Set up). **This is observed, not
  documented:** the settings docs list `~/.claude/settings.json` as not read in a cloud
  session, meaning the file on your PC. What was seen in project threads on the dstack
  environment (2026-11-11): the setup script's `claude plugin install` writes dstack's
  `enabledPlugins` into that file, and nothing else enables dstack there, yet dstack's
  SessionStart hook runs at session start. And a `permissions.deny` rule added to that file
  mid-session removed the tool from the session; removing it brought the tool back. If
  Claude Code stops reading the file, the plugin stops loading too, so it shows at once.
- **A cloud session with one repository, outside a project:** yes.
- **A cloud session with several repositories:** only `enabledPlugins` and
  `extraKnownMarketplaces`.
- **Claude Code on a PC:** yes.

dstack uses the same file.

In cloud sessions the repo file did not install the plugin (tested 2026-11-11), and plugins added in claude.ai Customize
did not sync either. Cloud projects get dstack from a cloud environment whose setup script
runs `claude plugin marketplace add dsickles/dstack` and `claude plugin install dstack@dstack`.

A new session's machine installs the latest dstack. A session that was already running
keeps its copy until `claude plugin marketplace update dstack` and
`claude plugin update dstack@dstack` run, and that update only happens when the version in
`.claude-plugin/plugin.json` went up. So CI (`scripts/version_check.py`) fails a PR that
changes shipped files without raising it.

## Known limits

- The approval gate matches tool names, so a messaging tool with an unusual verb slips
  through, and browser clicks that send messages are not covered.
- The merge guard reads the command text. A push hidden inside `bash -c '...'` or a
  script file is not seen; CI and the owner's merge are the backstop. Nor is a push through a
  shell variable (`b=main; git push origin $b`).
- The guard is fail-closed where it can't tell: any word that is `git` starts a check (so
  `echo git push origin main` is denied), and after `cd`, `git -C`, `GIT_DIR`/`GIT_CONFIG*`,
  `-c include.path` or a checkout, a push without a branch named (`git push`) is
  denied. Name the branch. Aliases (`-c alias.*`, saved, or set earlier in the command)
  are expanded, and with unreadable config any non-builtin subcommand is denied.
  `git send-pack`/`http-push` get the same refspec rules. `tests/test_push_probes.py`
  runs every push against real git and checks origin's refs as well as the pre-push hook.
- These limits are accepted for v1 (AC 7, agreed with the owner 2026-11-09). New bypasses,
  and a GitHub rule on `main` that refuses direct pushes server-side, are tracked in the
  issue tracker.
- Local git hooks don't run in cloud sessions; CI is the backstop there.
- The leak check only knows the words in `scripts/leak-hashes.txt`, and git history from
  before it existed still holds whatever it held.
