"""guard.yml can't import lib/rules.py, so its copies of the title patterns must match."""

import re
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "lib"))

import rules  # noqa: E402


def workflow_env(name):
    text = (ROOT / ".github" / "workflows" / "guard.yml").read_text(encoding="utf-8")
    m = re.search(rf"^\s*{name}: '(.*)'$", text, re.MULTILINE)
    return m.group(1)


class GuardWorkflow(unittest.TestCase):
    def test_title_patterns_match_rules(self):
        self.assertEqual(workflow_env("PR_TITLE_PATTERN"), rules.PR_TITLE.pattern)
        self.assertEqual(workflow_env("AUTOMATION_PR_PATTERN"), rules.AUTOMATION_PR.pattern)


if __name__ == "__main__":
    unittest.main()
