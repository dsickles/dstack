# Testing

Every acceptance criterion maps to a check, chosen before coding and written in the issue.

| Kind of work | Check | In dstack |
|---|---|---|
| Rule logic (commit format, PR title, gate, merge guard) | A failing test first | `tests/test_rules.py` (Python `unittest`, no dependencies) |
| Hook scripts | End-to-end test: JSON in, decision out | `tests/test_pretooluse.py`, `tests/test_session_start.py` |
| Bugs | A test that reproduces the bug first | same files |
| Skills and templates | Manual read by the owner; first real run on a repo | the PR's criteria table |
| CI guard | A CI run on the PR | the `guard` jobs |

## The check command

`bash scripts/check.sh` runs everything automated. CI runs it on every PR.

## Commands

- All tests: `python3 -m unittest discover -s tests`
- One file: `python3 -m unittest tests.test_rules`
