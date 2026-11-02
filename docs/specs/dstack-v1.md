---
linear_project: dstack (https://linear.app/dassoft/project/dstack-782fd6442893)
status: agreed
---

# dstack v1

## Problem

Dan starts projects by pasting a large scope prompt into a new repo. With no shared kit,
each session improvises the setup (Ledger got a CLAUDE.md instead of AGENTS.md, its spec in
a claude.ai artifact, and a different PR title format), and every repo carries its own copy
of the rules.

## Solution

One repo holds Dan's build rules, a `/kickoff` skill that sets up any repo, templates, and
enforcement that applies to every repo, agent and tool.

## In scope

- HOW-I-WORK.md, `/kickoff`, templates, git hooks, the reusable CI guard, Claude hooks,
  dstack's own docs and `check`.

## Out of scope

- Installing anything on Dan's PC (gitleaks, global hooks path, enabling the plugin, the
  full Pocock skill set, `~/.claude/CLAUDE.md`, the Cursor user rule). Follow-up issues,
  each with Dan's OK.
- Migrating other repos. Rollout order: Ledger, Threshold, AI-Digest, PlanSpecBuild,
  FamilyCalendar, PM-Agent-OS, grok-bot-sdlc-portable. Almanac is paused.

## Acceptance criteria

| # | Criterion | Check |
|---|---|---|
| 1 | HOW-I-WORK.md holds Dan's build rules, vendor-neutral, under 150 lines | Manual read by Dan; `check` enforces the length |
| 2 | `/kickoff` covers new-project and existing-repo modes and creates nothing before Dan approves | Manual read; first real run on Ledger |
| 3 | Templates exist for AGENTS.md, docs/agents/ (4 docs), ADR, spec, CI caller and `.claude/settings.json` | File list in the PR |
| 4 | Commit messages: conventional, `chore(<bot>):`, Almanac prefixes, merges and reverts pass; anything else fails | `tests/test_rules.py` |
| 5 | PR titles need `type: summary (DAS-n)`, except `chore(<bot>):` automation | `tests/test_rules.py`, `tests/test_guard_workflow.py` |
| 6 | The approval gate asks before MCP tools that message people; Linear and GitHub pass | `tests/test_rules.py`, `tests/test_pretooluse.py` |
| 7 | The merge guard denies merges and main pushes below autonomy level 3 | `tests/test_rules.py`, `tests/test_pretooluse.py` |
| 8 | SessionStart says "run /kickoff" in an unset repo, else reports branch, changes, commits behind | `tests/test_session_start.py` |
| 9 | gitleaks scans staged changes locally and the PR range in CI | CI run on the PR |
| 10 | `scripts/check.sh` runs all of the above and CI runs it | CI run on the PR |

## Slices

1. DAS-125: dstack v1 (this whole spec, one PR)

## Open questions

- Does `CLAUDE_CODE_REMOTE` reliably mark cloud sessions? (Confirm on the first cloud run.)
- Can cloud sessions install a plugin from this private repo? (Confirm on the first cloud run.)
