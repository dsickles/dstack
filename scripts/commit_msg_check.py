"""Check a commit message file (git commit-msg hook) or a PR title (--title)."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "lib"))

import config  # noqa: E402
import rules  # noqa: E402

COMMIT_HELP = """Commit message doesn't match the dstack format. Use one of:
  feat: add menu            (types: feat fix chore docs refactor test perf build ci style revert)
  fix(engine): round cents  (optional scope)
  chore(<bot>): ...         (automation)
  capture: / triage: ...    (content-repo bots)"""

TITLE_HELP = """PR title must be `type: summary ({p}-n)`, for example `feat: add menu ({p}-66)`.
Automation PRs may use `chore(<bot>): ...` without a ticket. The prefix comes from
`ticket_prefix` in .dstack/config.json; without one, any upper-case key is accepted."""


def main(argv) -> int:
    if len(argv) == 3 and argv[1] == "--title":
        prefix = config.load(Path.cwd())["ticket_prefix"]
        if rules.pr_title_ok(argv[2], prefix):
            return 0
        print(f"{TITLE_HELP.format(p=prefix or 'ABC')}\nGot: {argv[2]}", file=sys.stderr)
        return 1
    if len(argv) != 2:
        print("usage: commit_msg_check.py <message-file> | --title <title>", file=sys.stderr)
        return 2
    message = Path(argv[1]).read_text(encoding="utf-8", errors="replace")
    if rules.commit_msg_ok(message):
        return 0
    print(COMMIT_HELP, file=sys.stderr)
    return 1


if __name__ == "__main__":
    sys.exit(main(sys.argv))
