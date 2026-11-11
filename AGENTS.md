# dstack

A software factory for building with AI agents: the shared build rules, the `/kickoff`
skill, templates and enforcement that every repo using dstack shares. It is a Claude Code
plugin and a plain folder: Claude loads it as a plugin; Cursor and review bots read the
files. The repo is public; the owner's personal details live only in their own
`.dstack/config.json`, never here.

The global rules: [GLOBAL-AGENTS.md](GLOBAL-AGENTS.md). This file adds what is specific to
dstack.

**Autonomy level:** 1 Shape (a change here changes every repo)
**Linear:** the dstack project in the owner's workspace. Rules: docs/agents/issue-tracker.md.

## Invariants

- Matt Pocock's skills are the base, used unchanged; dstack adds only what they lack
  ([ADR-0001](docs/adr/0001-pocock-base-plus-kickoff.md)).
- Enforcement lives in plain scripts and CI first; Claude hooks are extra triggers
  ([ADR-0002](docs/adr/0002-scripts-and-ci-first.md)).
- `guard.yml` stays self-contained: it runs in the caller's checkout and reads only the
  caller's `.dstack/config.json`.

## Where things are

| What | Where |
|---|---|
| How dstack works | docs/architecture.md |
| Decisions | docs/adr/ |
| Current spec | docs/specs/dstack-v1.md |
| Issue tracker, PR and testing rules | docs/agents/ |
| The rule logic (commit, PR title, gate, merge guard) | lib/rules.py |

## Commands

- **check:** `bash scripts/check.sh` (unit tests, JSON, shell syntax, 150-line limits,
  leak check). CI runs it.

## Repo-specific rules

- Every rule change goes in `lib/rules.py` with a test in `tests/`. `guard.yml` keeps a
  copy of the PR-title patterns; `tests/test_guard_workflow.py` fails if they drift.
- `templates/` is copied into other repos by `/kickoff`. Keep placeholders as `<...>`.
- GLOBAL-AGENTS.md and templates/AGENTS.md stay under 150 lines (`check` enforces it).
- A PR that changes what the plugin ships (`skills/`, `hooks/`, `lib/`, `templates/`,
  GLOBAL-AGENTS.md) raises `version` in `.claude-plugin/plugin.json`; CI fails otherwise.
- Write "the owner", "the review bot" and `<PREFIX>`, never a real name, company or
  ticket key. `check` runs `scripts/leak_check.py`, which fails on the words hashed in
  `scripts/leak-hashes.txt`. Add your own with `--add WORD`.

## How the owner checks the work

Read the PR's criteria table. For hooks, the owner tries the behaviour in a real Claude
session after the plugin is enabled.
