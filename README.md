# dstack

Dan's software factory. One place for how every DASSoft project gets built:

- **[HOW-I-WORK.md](HOW-I-WORK.md):** the build rules every agent follows.
- **`/kickoff`:** paste a project's scope prompt (or run it in an existing repo) and it sets
  the repo up: AGENTS.md, Locked ADRs, a spec with a check per criterion, the `check`
  command, CI and the Linear project. It shows everything and waits for Dan's yes first.
- **Templates:** what `/kickoff` copies into each repo.
- **Enforcement:** a secret scan and message-format checks in git hooks and CI, plus three
  Claude hooks (session check, approval gate for messages, merge guard).

It works alongside [Matt Pocock's skills](https://github.com/mattpocock/skills), which do
the day-to-day work (`/to-spec`, `/to-tickets`, `/implement`, `tdd`, `code-review`). See
[ADR-0001](docs/adr/0001-pocock-base-plus-kickoff.md).

## Set up on a PC (once)

Each step is its own Linear issue, done with Dan's OK.

1. Put gitleaks 8.30.1 in `DASSoft/Tools/`.
2. `git config --global core.hooksPath C:/Users/Sickl/.cursor/DASSoft/dstack/git-hooks`
3. In Claude Code: `/plugin marketplace add dsickles/dstack`, then `/plugin install dstack@dstack`.
4. Install the full set of Matt Pocock's skills at account level.
5. `~/.claude/CLAUDE.md` is one line: `@C:/Users/Sickl/.cursor/DASSoft/dstack/HOW-I-WORK.md`
6. GitHub: dstack → Settings → Actions → Access → allow Dan's repositories, so other private
   repos can call `guard.yml`.

## Use in a repo

Run `/kickoff`. It adds `.claude/settings.json` (enables this plugin, also in cloud
sessions) and a CI workflow that calls the guard.

## Develop dstack

`bash scripts/check.sh` runs everything. How it fits together:
[docs/architecture.md](docs/architecture.md).
