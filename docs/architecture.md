# How dstack works

dstack is one repo used three ways: as a Claude Code plugin, as a folder other tools read,
and as a source of templates that `/kickoff` copies into other repos.

## Pieces

| Piece | Files | Used by |
|---|---|---|
| Build rules | `HOW-I-WORK.md` | Claude via `~/.claude/CLAUDE.md` import (local) or the SessionStart hook (cloud); Cursor via a user rule |
| `/kickoff` skill | `skills/kickoff/SKILL.md` | Claude through the plugin |
| Templates | `templates/` | `/kickoff`, copied into each repo |
| Rule logic | `lib/rules.py` | git hooks, Claude hooks, tests |
| Git hooks | `git-hooks/` | every repo on Dan's PC via `git config --global core.hooksPath` |
| CI guard | `.github/workflows/guard.yml` | every repo's CI via `uses: dsickles/dstack/.github/workflows/guard.yml@main` |
| Claude hooks | `hooks/hooks.json`, `hooks/*.py` | Claude sessions with the plugin enabled |

## Enforcement layers

1. **Git hooks (Dan's PC).** `pre-commit` runs gitleaks on staged changes; `commit-msg`
   checks the message format. Each then runs the repo's own hook (`scripts/hooks/<name>`
   or `.git/hooks/<name>`), because a global hooks path hides them.
2. **CI (every PR).** `guard.yml` scans the PR's commits with gitleaks and checks the PR
   title. It is self-contained because a caller's token cannot read dstack's files, so it
   carries a copy of the title patterns; a test keeps that copy in sync with `lib/rules.py`.
   The repo's own job runs its `check`.
3. **Claude hooks (extra triggers).**
   - `SessionStart` (`session_start.py`): says "run /kickoff" in a repo without AGENTS.md or
     docs/agents/; otherwise reports branch, uncommitted changes and commits behind GitHub.
     In cloud sessions (`CLAUDE_CODE_REMOTE=true`) it also prints HOW-I-WORK.md.
   - `PreToolUse` (`pretooluse.py`): the merge guard denies `gh pr merge`, MCP merge tools
     and pushes to main/master unless the project's AGENTS.md says autonomy level 3; the
     approval gate asks before MCP tools whose names send, reply, forward, invite or create
     calendar events. Linear and GitHub tools pass. If the hook can't read a call or
     crashes, it denies.

## How a repo gets dstack

`/kickoff` writes the repo's `.claude/settings.json` from `templates/claude-settings.json`,
which registers dstack as a plugin marketplace and enables the plugin. That works in cloud
sessions too, where `~/.claude` does not exist.

## Known limits

- The approval gate matches tool names, so a messaging tool with an unusual verb slips
  through, and browser clicks that send messages are not covered.
- The merge guard reads the command text. A push hidden inside `bash -c '...'` or a
  script file is not seen; CI and Dan's merge are the backstop. Nor is a push through a
  shell variable (`b=main; git push origin $b`).
- The guard is fail-closed where it can't tell: any word that is `git` starts a check (so
  `echo git push origin main` is denied), and after `cd`, `git -C`, `GIT_DIR`/`GIT_CONFIG*`,
  `-c include.path` or a checkout, a push without a branch named (`git push`) is
  denied. Name the branch. Aliases (`-c alias.*`, saved, or set earlier in the command)
  are expanded, and with unreadable config any non-builtin subcommand is denied.
  `git send-pack`/`http-push` get the same refspec rules. `tests/test_push_probes.py`
  runs every push against real git and checks origin's refs as well as the pre-push hook.
- Local git hooks don't run in cloud sessions; CI is the backstop there.
- The cloud signal `CLAUDE_CODE_REMOTE` and private-repo plugin install in cloud sessions
  are to be confirmed on first use.
