# dstack

A small software factory for building with AI agents. One place for how every project
gets built:

- **[GLOBAL-AGENTS.md](GLOBAL-AGENTS.md):** the build rules every agent follows.
- **`/kickoff`:** paste a project's scope prompt (or run it in an existing repo) and it sets
  the repo up: AGENTS.md, Locked ADRs, a spec with a check per criterion, the `check`
  command, CI and the Linear project. It shows everything and waits for the owner's yes.
- **Templates:** what `/kickoff` copies into each repo.
- **Enforcement:** a secret scan and message-format checks in git hooks and CI, plus three
  Claude hooks (session check, approval gate for messages, merge guard).

It works alongside [Matt Pocock's skills](https://github.com/mattpocock/skills), which do
the day-to-day work (`/to-spec`, `/to-tickets`, `/implement`, `tdd`, `code-review`). See
[ADR-0001](docs/adr/0001-pocock-base-plus-kickoff.md).

## Your config

The kit says "the owner", "the review bot" and `<PREFIX>`. Your details live in a JSON
file that never goes into this repo:

```json
{
  "owner": "Ada",
  "about": "Product manager; reads diffs and tests the result, agents write the code.",
  "tracker": "Linear workspace acme, team Acme",
  "ticket_prefix": "ACME",
  "review_bot": "Rex"
}
```

- `~/.dstack/config.json` holds your defaults. In a cloud environment, write it from the
  setup script.
- A repo's `.dstack/config.json` overrides it key by key. `/kickoff` writes one with the
  repo's `ticket_prefix`. Keep personal keys out of public repos.
- Every key is optional. The session start prints what it found. The PR-title check
  (locally and in `guard.yml`) uses `ticket_prefix`, and accepts any `ABC-123` key
  without one.

## Set up

**Claude Code cloud sessions.** Create a cloud environment with this setup script, and
pick it in each project's settings:

```bash
claude plugin marketplace add dsickles/dstack || true
claude plugin install dstack@dstack || true
mkdir -p ~/.dstack && cat > ~/.dstack/config.json <<'JSON'
{"owner": "Ada", "ticket_prefix": "ACME", "review_bot": "Rex"}
JSON
python3 - <<'PY'
import json, pathlib
p = pathlib.Path.home() / ".claude" / "settings.json"
s = json.loads(p.read_text()) if p.exists() else {}
allow = s.setdefault("permissions", {}).setdefault("allow", [])
for rule in ["mcp__Linear", "mcp__claude_ai_Linear", "mcp__github"]:
    if rule not in allow:
        allow.append(rule)
p.parent.mkdir(exist_ok=True)
p.write_text(json.dumps(s, indent=2))
PY
```

The last step pre-approves the Linear and GitHub tools, so cloud threads don't stop on
them. Threads in a claude.ai project ignore a repo's own `.claude/settings.json`
permissions, so this has to live in the environment. dstack's hooks still run first: the
merge guard still denies merges and writes to main.

**Claude Code on a PC.**

1. `/plugin marketplace add dsickles/dstack`, then `/plugin install dstack@dstack`.
2. `~/.claude/CLAUDE.md` is one line: `@<path to dstack>/GLOBAL-AGENTS.md`.
3. Optional git hooks: put gitleaks on PATH, then
   `git config --global core.hooksPath <path to dstack>/git-hooks`.
4. Install Matt Pocock's skills.

## Use in a repo

Run `/kickoff`. It adds `.claude/settings.json` (enables this plugin), `.dstack/config.json`
and a CI workflow that calls the guard.

## Develop dstack

`bash scripts/check.sh` runs everything, including a leak check. That check fails if a
tracked file contains a word from `scripts/leak-hashes.txt`, which stores only hashes.
Add your own private words with `python3 scripts/leak_check.py --add WORD`. How it fits
together: [docs/architecture.md](docs/architecture.md).

## Built on

dstack keeps its own code small. Its ideas come, with thanks, from these projects (some
are in dstack now, the rest are on the way):

- [Matt Pocock's skills](https://github.com/mattpocock/skills): the day-to-day engineering
  skills dstack runs alongside, and the `docs/agents/` config-doc pattern.
- [pstack](https://github.com/cursor/plugins/tree/main/pstack): a personal stack packaged
  as a plugin, and interrogating the work before review.
- [PLAID](https://github.com/BuildGreatProducts/plaid): idea validation, design and launch
  stages ahead of the build.
- [BMAD Method](https://github.com/bmad-code-org/BMAD-METHOD): structured brainstorming
  and ideation.
- [GSD Core](https://github.com/open-gsd/gsd-core): plan checks with severities, and fresh
  subagents per task.
- [Spec Kit](https://github.com/github/spec-kit): `[NEEDS CLARIFICATION]` markers and
  short clarification rounds.
- [Superpowers](https://github.com/obra/superpowers): verification before completion, and
  how to receive code review.
- [Beads](https://github.com/gastownhall/beads): "ready work" as a first-class idea.
- [no-mistakes](https://github.com/kunchenguid/no-mistakes) and
  [backpass](https://github.com/kunchenguid/backpass), plus treehouse and firstmate, by
  [Kun Chen](https://github.com/kunchenguid): a review gate before a PR leaves draft,
  sorting findings into fixes and questions, and changing a rule only on evidence.
- [PM Agent OS](https://github.com/dsickles/PM-Agent-OS): the validation gate and success
  measures on the product side.

Risk-based testing tiers, when they land, follow long-standing practice: risk-based
testing, change types in ITIL, size labels in Kubernetes, CODEOWNERS and Danger.
