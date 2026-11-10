# 0002. Enforcement in scripts and CI first, Claude hooks second

**Status:** Locked
**Date:** 2026-11-02
**Decided by:** Dan

## Context

Dan uses Claude Code, Cursor and Grok bots. A rule enforced only by a Claude hook binds only
Claude.

## Decision

- Secret scanning (gitleaks), commit-message format and PR-title format run as git hooks
  on Dan's PC and in CI (`guard.yml`). Each repo's CI also runs its `check` command.
- Claude-only hooks are limited to three: the SessionStart check, the approval gate for
  messages sent for Dan, and the merge guard.
- The approval gate covers messages to people. Linear and GitHub activity is part of the
  normal ticket and PR flow and passes without a prompt.

## Consequences

- Every agent and Dan's own commits meet the same checks.
- Cloud sessions skip local git hooks; CI catches what they miss.
- PM-Agent-OS keeps its own stricter preview-every-write gate.
