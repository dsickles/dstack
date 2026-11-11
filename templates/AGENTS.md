# <Project name>

<One paragraph: what it is, who it's for, the stack.>

The global rules are in dstack's GLOBAL-AGENTS.md (loaded for every session), and the
owner's details are in `.dstack/config.json`. This file adds what is specific to this repo
and wins where it is stricter.

**Autonomy level:** <1 Shape | 2 Build | 3 Automate> (<one line why>)
**Linear:** initiative <name>; current project <name>. Rules: docs/agents/issue-tracker.md.

## Invariants

Each is a Locked ADR. Changing one needs the owner's explicit yes.

- <rule> ([ADR-000N](docs/adr/000N-<slug>.md))

## Where things are

| What | Where |
|---|---|
| How the system works now | docs/architecture.md |
| Decisions (newest wins; Locked = ask the owner) | docs/adr/ |
| Spec for the current release | docs/specs/<linear-project-slug>.md |
| Terms | GLOSSARY.md |
| Issue tracker, PR and testing rules | docs/agents/ |

## Commands

- **check:** `<exact command>`. CI runs it; run it before calling work done.
- **run:** `<exact command>`
- <other: export, publish, seed data>

## Repo-specific rules

- <what is easy to get wrong here: generated files, folders to leave alone, gotchas>

## How the owner checks the work

<Where and how the owner verifies: device, browser, the "what to look for" list format.>
