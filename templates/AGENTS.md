# <Project name>

<One paragraph: what it is, who it's for, the stack.>

Dan's general rules are in dstack's HOW-I-WORK.md (loaded globally). This file adds what
is specific to this repo and wins where it is stricter.

**Autonomy level:** <1 Shape | 2 Build | 3 Automate> (<one line why>)
**Linear:** initiative <name>; current project <name>. Rules: docs/agents/issue-tracker.md.

## Invariants

Each is a Locked ADR. Changing one needs Dan's explicit yes.

- <rule> ([ADR-000N](docs/adr/000N-<slug>.md))

## Where things are

| What | Where |
|---|---|
| How the system works now | docs/architecture.md |
| Decisions (newest wins; Locked = ask Dan) | docs/adr/ |
| Spec for the current release | docs/specs/<linear-project-slug>.md |
| Terms | GLOSSARY.md |
| Issue tracker, PR and testing rules | docs/agents/ |

## Commands

- **check:** `<exact command>`. CI runs it; run it before calling work done.
- **run:** `<exact command>`
- <other: export, publish, seed data>

## Repo-specific rules

- <what is easy to get wrong here: generated files, folders to leave alone, gotchas>

## How Dan checks the work

<Where and how Dan verifies: device, browser, the "what to look for" list format.>
