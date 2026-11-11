# 0002. Enforcement in scripts and CI first, Claude hooks second

**Status:** Locked
**Date:** 2026-11-02
**Decided by:** the owner

## Context

The owner uses Claude Code, Cursor and review bots. A rule enforced only by a Claude hook
binds only Claude.

## Decision

- Secret scanning (gitleaks), commit-message format and PR-title format run as git hooks
  on the owner's PC and in CI (`guard.yml`). Each repo's CI also runs its `check` command.
- Claude-only hooks are limited to three: the SessionStart check, the approval gate for
  messages sent for the owner, and the merge guard.
- The approval gate covers messages to people. Linear and GitHub activity is part of the
  normal ticket and PR flow and passes without a prompt.

## Consequences

- Every agent and the owner's own commits meet the same checks.
- Cloud sessions skip local git hooks; CI catches what they miss.
- A repo with its own stricter gate (for example, preview every write) keeps it.
