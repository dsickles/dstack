"""The settings dstack hands out pre-approve the tools the workflow calls."""

import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "lib"))
import rules  # noqa: E402

# Real tool names, as they appear in a claude.ai cloud project thread (Linear, github)
# and with claude.ai connectors in Claude Code on a PC (claude_ai_Linear).
WORKFLOW_CALLS = [
    "mcp__Linear__save_issue",
    "mcp__Linear__save_comment",
    "mcp__claude_ai_Linear__save_issue",
    "mcp__github__create_pull_request",
    "mcp__github__update_pull_request",
]


def load(path):
    return json.loads((ROOT / path).read_text(encoding="utf-8"))


def allowed(rule, tool):
    """Claude Code's MCP rule forms: mcp__server, mcp__server__*, mcp__server__tool."""
    if rule.endswith("__*"):
        return tool.startswith(rule[:-1])
    return tool == rule or tool.startswith(rule + "__") and rule.count("__") == 1


class SettingsTemplate(unittest.TestCase):
    def test_template_pre_approves_every_workflow_call(self):
        allow = load("templates/claude-settings.json")["permissions"]["allow"]
        for tool in WORKFLOW_CALLS:
            with self.subTest(tool=tool):
                self.assertTrue(any(allowed(r, tool) for r in allow), allow)

    def test_matcher_is_exact_about_server_names(self):
        self.assertTrue(allowed("mcp__Linear", "mcp__Linear__save_issue"))
        self.assertFalse(allowed("mcp__Linear", "mcp__linear__save_issue"))
        self.assertFalse(allowed("mcp__Linear", "mcp__LinearX__save_issue"))

    def test_template_still_enables_dstack(self):
        self.assertIs(load("templates/claude-settings.json")["enabledPlugins"]["dstack@dstack"], True)

    def test_dstack_uses_its_own_template(self):
        self.assertEqual(load(".claude/settings.json"), load("templates/claude-settings.json"))

    def test_readme_setup_script_adds_the_same_allow_list(self):
        # Project threads ignore a repo's permission rules, so the cloud setup script
        # writes the same list into the session's ~/.claude/settings.json.
        allow = load("templates/claude-settings.json")["permissions"]["allow"]
        readme = (ROOT / "README.md").read_text(encoding="utf-8")
        for rule in allow:
            self.assertIn(f'"{rule}"', readme)


if __name__ == "__main__":
    unittest.main()
