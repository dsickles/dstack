# Global agent rules

These rules apply to every agent on every project that uses dstack. A repo's AGENTS.md
can be stricter; where it is looser, this file wins.

"The owner" is the person these agents work for. Their name, the issue tracker, the
ticket prefix and the review bot come from `.dstack/config.json` (the session start
prints them). The owner builds with AI agents: they read diffs and test the result, and
agents write most of the code.

## Talking to the owner

- Plain language. Explain any jargon in one line.
- Recommend one option and say why.
- Ask the owner only for decisions that are really theirs: scope, feel, story, cost,
  anything public. Find facts yourself.
- Short answers. Say what is done, what is not, and what was not checked.
- Use commas, colons or parentheses where an em dash would go.

## Agree before building

- Every piece of work starts as an issue in the issue tracker. One issue = one PR.
- Before coding, agree the scope and acceptance criteria, and name the check for each
  criterion (see Testing).
- The repo's AGENTS.md states an autonomy level:
  - **1 Shape:** the owner approves the plan for every issue.
  - **2 Build:** the owner approves the plan only for big issues.
  - **3 Automate:** commit straight to main.
- These always need the owner's yes first, at every level: a new dependency, spending
  money, anything public or hard to reverse, a message sent for the owner, a change to a
  Locked ADR, and any change of scope.
- A new idea found mid-build becomes its own issue; the current PR stays on its ticket.

## Testing

Every acceptance criterion maps to a check chosen before coding:

- **Logic, data and rules:** a failing test first.
- **Bugs:** a test that reproduces the bug first.
- **UI and feel:** manual steps written in the issue first, plus a cheap smoke test.
- **Content repos:** a validator in CI.
- **Prototypes:** no tests, and never merged as-is.

Each repo has one `check` command, and CI runs it. Report a test as passing only after
running it.

## Docs and decisions

- The code wins over stale docs.
- Every PR answers three questions:
  1. Did this change how the system works? Update `docs/architecture.md`.
  2. Did it make a hard-to-reverse choice? Add an ADR in `docs/adr/`.
  3. Did it add a term? Update `GLOSSARY.md`.
- ADR status is Accepted, Locked or Superseded. Only the owner locks or unlocks one.
- The agreed spec for a release lives in `docs/specs/<project-slug>.md`, linked from the
  tracker's project.
- Planning-framework folders (`.planning/`, `.spec/` and the like) are scratch. Status
  lives only in the tracker. When a tracker project closes, what lasts moves into the
  standard docs.

## Branches, commits and PRs

- Branch: the issue's branch name from the tracker. Push as soon as you commit; pull
  before you start.
- Commits: `type: summary` (feat, fix, chore, docs, refactor, test, perf, build, ci,
  style, revert). Automation: `chore(<bot>): ...`.
- PR title: `type: summary (PREFIX-n)`, with the ticket prefix from config, for example
  `feat: add menu (ABC-66)`.
- Open every PR as a draft. Before it leaves draft, list every acceptance criterion in
  the PR body, word for word, with its proof: a test name, a `file:line`, a CI run, or
  "Needs the owner's device" with what the owner should do.
- When the PR leaves draft, move the issue to In Review and comment the PR link. The
  review bot starts on that move.
- Review rounds, for every issue the PR covers: move it to In Progress when you start
  on the review's changes. When the fixes are pushed and CI is green, move it back to
  In Review and comment on the PR which fix answers which item. The review bot starts
  again on that move.
- The owner merges, with squash. Merging marks the issue Done.

## Secrets and privacy

- Secrets, passwords, account numbers and real personal data stay out of repos, tickets,
  PRs and logs. Write a pointer instead ("in the password manager: <entry name>").
- Public repos use demo data only.

## New projects

Start with `/kickoff` and paste the scope prompt.
