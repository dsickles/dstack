# Testing

Every acceptance criterion maps to a check, chosen before coding and written in the issue.

| Kind of work | Check | In this repo |
|---|---|---|
| Logic, data and rules | A failing test first, then the code that turns it green | <test framework, where tests live> |
| Bugs | A test that reproduces the bug first | <same> |
| UI and feel | Manual steps written in the issue first, plus a cheap smoke test | <smoke test tool; the owner's device> |
| Content | A validator in CI | <validator command> |
| Prototypes | No tests; never merged as-is | |

## The check command

`<exact command>` runs everything automated. CI runs it on every PR; run it before calling
work done.

## Commands

- All tests: `<command>`
- One test file: `<command>`
