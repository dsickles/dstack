# 0001. Pocock's skills as the base, plus /kickoff only

**Status:** Locked
**Date:** 2026-11-02
**Decided by:** Dan

## Context

The first draft proposed five shared skills: /kickoff, /next-ticket, /ship,
/record-decision and /harvest. Three of them duplicated Matt Pocock's skills: `/implement`
already runs tdd, code review and the PR (deferring PR rules to the repo's
`docs/agents/pull-requests.md`), and `domain-modeling` records ADRs. His skills stay
generic and read per-repo config docs for local rules, so Dan's rules fit without forking
them.

## Decision

- Pocock's skills are installed unchanged, at account level, and updated from upstream.
- dstack adds one skill, `/kickoff`, which sets a repo up for Dan's workflow.
- Dan's rules reach Pocock's skills through `docs/agents/` config docs written from
  dstack's templates.
- /next-ticket, /ship, /record-decision and /harvest are not built. Release-close steps
  live in `docs/agents/issue-tracker.md`.

## Consequences

- Upstream updates to Pocock's skills arrive without merge work.
- A rule that his skills don't read from config has nowhere to go but a new dstack skill;
  that needs Dan's yes (this ADR is Locked).
