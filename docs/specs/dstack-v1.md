---
linear_project: dstack (in the owner's Linear workspace)
status: agreed
---

# dstack v1

## Problem

The owner starts projects by pasting a large scope prompt into a new repo. With no shared kit,
each session improvises the setup (one repo got a CLAUDE.md instead of AGENTS.md, its spec in
a claude.ai artifact, and a different PR title format), and every repo carries its own copy
of the rules.

## Solution

One repo holds the owner's build rules, a `/kickoff` skill that sets up any repo, templates, and
enforcement that applies to every repo, agent and tool.

## In scope

- HOW-I-WORK.md, `/kickoff`, templates, git hooks, the reusable CI guard, Claude hooks,
  dstack's own docs and `check`.

## Out of scope

- Installing anything on the owner's PC (gitleaks, global hooks path, enabling the plugin, the
  full Pocock skill set, `~/.claude/CLAUDE.md`, the Cursor user rule). Follow-up issues,
  each with the owner's OK.
- Migrating the owner's other repos. Each is its own issue, one repo at a time.

## Acceptance criteria

| # | Criterion | Check |
|---|---|---|
| 1 | HOW-I-WORK.md (now GLOBAL-AGENTS.md) holds the build rules, vendor-neutral, under 150 lines | Manual read by the owner; `check` enforces the length |
| 2 | `/kickoff` covers new-project and existing-repo modes and creates nothing before the owner approves | Manual read; first real run on an existing repo |
| 3 | Templates exist for AGENTS.md, docs/agents/ (4 docs), ADR, spec, CI caller and `.claude/settings.json` | File list in the PR |
| 4 | Commit messages: conventional, `chore(<bot>):`, content-bot prefixes, merges and reverts pass; anything else fails | `tests/test_rules.py` |
| 5 | PR titles need `type: summary (<PREFIX>-n)`, except `chore(<bot>):` automation | `tests/test_rules.py`, `tests/test_guard_workflow.py` |
| 6 | The approval gate asks before MCP tools that message people; Linear and GitHub pass | `tests/test_rules.py`, `tests/test_pretooluse.py` |
| 7 | The merge guard denies merges and main pushes below autonomy level 3, for every command in its tests. The bypasses under Known limits in `docs/architecture.md` are accepted; new ones go to a follow-up issue (agreed with the owner 2026-11-09) | `tests/test_rules.py::MergeGuard`, `tests/test_pretooluse.py`, `tests/test_push_probes.py` |
| 8 | SessionStart says "run /kickoff" in an unset repo, else reports branch, changes, commits behind | `tests/test_session_start.py` |
| 9 | gitleaks scans staged changes locally and the PR range in CI | CI run on the PR |
| 10 | `scripts/check.sh` runs all of the above and CI runs it | CI run on the PR |

## Slices

1. dstack v1 (this whole spec, one PR)

## Open questions

- Does `CLAUDE_CODE_REMOTE` reliably mark cloud sessions? (Confirm on the first cloud run.)
- Can cloud sessions install a plugin from this private repo? (Confirm on the first cloud run.)
