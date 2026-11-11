"""End-to-end tests for hooks/pretooluse.py: JSON on stdin, decision on stdout."""

import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

HOOK = Path(__file__).resolve().parent.parent / "hooks" / "pretooluse.py"


def run_raw(payload, project):
    # HOME is the project too, so the machine's own ~/.dstack/config.json can't leak in.
    env = dict(os.environ, CLAUDE_PROJECT_DIR=str(project), HOME=str(project),
               USERPROFILE=str(project))
    r = subprocess.run([sys.executable, str(HOOK)], input=json.dumps(payload),
                       capture_output=True, text=True, env=env, check=True)
    return json.loads(r.stdout)["hookSpecificOutput"] if r.stdout.strip() else None


def run(payload, project):
    out = run_raw(payload, project)
    return out["permissionDecision"] if out else None


class PreToolUse(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.project = Path(self.tmp.name)

    def tearDown(self):
        self.tmp.cleanup()

    def test_merge_denied_without_level_three(self):
        (self.project / "AGENTS.md").write_text("**Autonomy level:** 2 Build\n")
        p = {"tool_name": "Bash", "tool_input": {"command": "gh pr merge 4"}, "cwd": str(self.project)}
        self.assertEqual(run(p, self.project), "deny")

    def test_merge_allowed_at_level_three(self):
        (self.project / "AGENTS.md").write_text("**Autonomy level:** 3 Automate\n")
        p = {"tool_name": "Bash", "tool_input": {"command": "gh pr merge 4"}, "cwd": str(self.project)}
        self.assertIsNone(run(p, self.project))

    def test_messages_name_the_owner_from_config(self):
        merge = {"tool_name": "Bash", "tool_input": {"command": "gh pr merge 4"},
                 "cwd": str(self.project)}
        send = {"tool_name": "mcp__gmail__send_email", "tool_input": {}}
        self.assertIn("the owner merges", run_raw(merge, self.project)["permissionDecisionReason"])
        (self.project / ".dstack").mkdir()
        (self.project / ".dstack" / "config.json").write_text(json.dumps({"owner": "Ada"}))
        self.assertIn("Ada merges", run_raw(merge, self.project)["permissionDecisionReason"])
        self.assertIn("for Ada", run_raw(send, self.project)["permissionDecisionReason"])

    def test_message_asks(self):
        p = {"tool_name": "mcp__gmail__send_email", "tool_input": {}}
        self.assertEqual(run(p, self.project), "ask")

    def test_ordinary_tools_pass(self):
        for p in [{"tool_name": "Bash", "tool_input": {"command": "ls"}},
                  {"tool_name": "mcp__linear__save_comment", "tool_input": {}}]:
            with self.subTest(p=p):
                self.assertIsNone(run(p, self.project))

    def test_bad_input_is_denied(self):
        for raw in ["not json", "[]", json.dumps({"tool_name": "Bash", "tool_input": {"command": 5}})]:
            with self.subTest(raw=raw):
                r = subprocess.run([sys.executable, str(HOOK)], input=raw, capture_output=True,
                                   text=True, env=dict(os.environ, CLAUDE_PROJECT_DIR=str(self.project)))
                self.assertEqual(r.returncode, 0)
                self.assertEqual(json.loads(r.stdout)["hookSpecificOutput"]["permissionDecision"], "deny")

    def test_unreadable_agents_md_is_denied(self):
        (self.project / "AGENTS.md").mkdir()
        p = {"tool_name": "Bash", "tool_input": {"command": "gh pr merge 4"}, "cwd": str(self.project)}
        self.assertEqual(run(p, self.project), "deny")

    def test_bare_push_tracking_main_is_denied(self):
        git = ["git", "-C", str(self.project)]
        subprocess.run([*git, "init", "-q", "-b", "feature"], check=True)
        subprocess.run([*git, "config", "branch.feature.remote", "origin"], check=True)
        subprocess.run([*git, "config", "branch.feature.merge", "refs/heads/main"], check=True)
        (self.project / "AGENTS.md").write_text("**Autonomy level:** 2 Build\n")
        p = {"tool_name": "Bash", "tool_input": {"command": "git push"}, "cwd": str(self.project)}
        self.assertEqual(run(p, self.project), "deny")


if __name__ == "__main__":
    unittest.main()
