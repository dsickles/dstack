---
name: kickoff
description: "Set up a repo for Dan's workflow: standard docs, Locked ADRs, spec, check command, CI and Linear. Use when the user says /kickoff, pastes a project scope prompt, or the repo has no AGENTS.md or docs/agents/."
---

# Kickoff

Bring a repo up to Dan's standard: every rule an agent needs is in AGENTS.md or behind a
pointer from it, every hard rule is a Locked ADR, the release has a spec with a check per
criterion, `check` runs in CI, and the work is in Linear.

Templates live in this plugin at [`../../templates/`](../../templates/). Dan's general
rules are [`../../HOW-I-WORK.md`](../../HOW-I-WORK.md); keep them out of the repo's
AGENTS.md, which carries only what is specific to this repo.

**Nothing is written, committed or created in Linear until Dan approves the full draft in
step 4.** Until then, every artifact is shown, not saved.

## 1. Pick the mode

- **New project:** Dan pasted a scope prompt (often a long Gemini brainstorm) and the repo
  has little or no code.
- **Existing repo:** the repo has code but lacks the standard docs.

Done when you have told Dan which mode and why, in one line.

## 2. Inventory

**New project:** restate the prompt in five lines: the problem, who it is for, what v1
must do, what is out of scope, the biggest risk. Then list every decision the prompt leaves
open.

**Existing repo:** check each item and record what exists and where:

- AGENTS.md, CLAUDE.md, `docs/architecture.md`, `docs/adr/`, `docs/specs/`, `docs/agents/`,
  GLOSSARY.md
- the `check` command, CI workflows, git hooks
- rules living elsewhere: CLAUDE.md sections, `.cursor/rules/`, constitutions, "locked" or
  "must not break" files, README sections that give agents orders
- open work in scratch planning folders (`.planning/`, `.spec/`, `_bmad*`, task lists)
- the Linear initiative and projects for this repo
- whether the checkout is behind GitHub

Done when every item above has a line saying "exists at X", "missing", or "lives in Y,
should move to Z".

## 3. Grill Dan on his decisions

Use the `grilling` skill if available; otherwise ask one question at a time, each with
your recommended answer. Cover only what is Dan's to decide:

- the v1 boundary (in, out, later)
- the autonomy level (1 Shape, 2 Build, 3 Automate), with your recommendation
- public or private repo; what data may appear in it
- the hard rules that must never break (each becomes a Locked ADR)
- cost limits and outside services
- how Dan will check the work (device, browser, playtest)

Find facts yourself (stack versions, commands, file layout). Done when every open decision
from step 2 has Dan's answer.

## 4. Draft everything and get approval

Draft from the templates, then show Dan the full set in one message:

- `AGENTS.md` (under 150 lines) and `CLAUDE.md` (`@AGENTS.md`)
- `docs/agents/issue-tracker.md`, `pull-requests.md`, `testing.md`, `domain.md`
- `docs/architecture.md`: for a new project, the intended design, labelled as intended
- `docs/adr/`: one ADR per hard rule (status Locked) and one for the stack (Accepted)
- `docs/specs/<linear-project-slug>.md`: use `to-spec` if available; every acceptance
  criterion has its check from the testing rules
- the `check` command, `.github/workflows/ci.yml` from `templates/ci.yml`,
  `.claude/settings.json` from `templates/claude-settings.json`
- Linear: the initiative (if new), the first project (release), and its issues as
  tracer-bullet slices with blocked-by order (use `to-tickets` if available)
- **Existing repo only:** the migration table: each rule or file found in step 2, where it
  goes, and what gets archived

Done when Dan has said yes to the whole set. Apply his changes and show again until he
does.

## 5. Land it

1. Create the Linear items: initiative and project assigned to Dan, the spec linked from
   the project, a kickoff issue, then the slice issues.
2. Branch from the kickoff issue's Linear branch name.
3. Commit the approved files, run `check`, push, and open a draft PR titled
   `chore: kickoff (DAS-n)` following `docs/agents/pull-requests.md`.
4. Mark it ready and move the kickoff issue to In Review.

Done when the PR is open with CI green and the PR link is on the issue. Dan merges.

## 6. Hand off

Tell Dan which slice to start first and why, and anything only he can do (accounts,
devices, secrets).
