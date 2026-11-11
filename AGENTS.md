# dstack

Dan's software factory: the shared build rules, the `/kickoff` skill, templates and
enforcement that every DASSoft repo uses. It is a Claude Code plugin and a plain folder:
Claude loads it as a plugin; Cursor and Grok bots read the files.

Dan's general rules: [HOW-I-WORK.md](HOW-I-WORK.md). This file adds what is specific to
dstack.

**Autonomy level:** 1 Shape (a change here changes every repo)
**Linear:** initiative Agentic Workflows; project dstack. Rules: docs/agents/issue-tracker.md.

## Invariants

- Matt Pocock's skills are the base, used unchanged; dstack adds only what they lack
  ([ADR-0001](docs/adr/0001-pocock-base-plus-kickoff.md)).
- Enforcement lives in plain scripts and CI first; Claude hooks are extra triggers
  ([ADR-0002](docs/adr/0002-scripts-and-ci-first.md)).
- `guard.yml` stays self-contained: callers' tokens cannot read this private repo.

## Where things are

| What | Where |
|---|---|
| How dstack works | docs/architecture.md |
| Decisions | docs/adr/ |
| Current spec | docs/specs/dstack-v1.md |
| Issue tracker, PR and testing rules | docs/agents/ |
| The rule logic (commit, PR title, gate, merge guard) | lib/rules.py |

## Commands

- **check:** `bash scripts/check.sh` (unit tests, JSON, shell syntax, 150-line limits).
  CI runs it.

## Repo-specific rules

- Every rule change goes in `lib/rules.py` with a test in `tests/`. `guard.yml` keeps a
  copy of the PR-title patterns; `tests/test_guard_workflow.py` fails if they drift.
- `templates/` is copied into other repos by `/kickoff`. Keep placeholders as `<...>`.
- HOW-I-WORK.md and templates/AGENTS.md stay under 150 lines (`check` enforces it).
- A PR that changes what the plugin ships (`skills/`, `hooks/`, `lib/`, `templates/`,
  HOW-I-WORK.md) raises `version` in `.claude-plugin/plugin.json`; CI fails otherwise.

## How Dan checks the work

Read the PR's criteria table. For hooks, Dan tries the behaviour in a real Claude session
after the plugin is enabled.
