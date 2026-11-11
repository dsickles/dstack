"""The settings /kickoff copies into each repo pre-approve the workflow's tools."""

import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "lib"))
import rules  # noqa: E402

WORKFLOW_SERVERS = {"mcp__Linear", "mcp__claude_ai_Linear", "mcp__github"}


def load(path):
    return json.loads((ROOT / path).read_text(encoding="utf-8"))


class SettingsTemplate(unittest.TestCase):
    def test_template_pre_approves_linear_and_github(self):
        allow = set(load("templates/claude-settings.json")["permissions"]["allow"])
        self.assertTrue(WORKFLOW_SERVERS <= allow, allow)

    def test_template_still_enables_dstack(self):
        self.assertIs(load("templates/claude-settings.json")["enabledPlugins"]["dstack@dstack"], True)

    def test_dstack_uses_its_own_template(self):
        self.assertEqual(load(".claude/settings.json"), load("templates/claude-settings.json"))

    def test_pre_approved_tools_pass_the_gate(self):
        # The allow list skips Claude Code's own prompt; dstack's gate must agree.
        for tool in ("mcp__Linear__save_issue", "mcp__claude_ai_Linear__save_comment",
                     "mcp__github__create_pull_request"):
            self.assertIsNone(rules.gate_decision(tool), tool)


if __name__ == "__main__":
    unittest.main()
