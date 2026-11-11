"""Tests for hooks/session_start.py against throwaway git repos."""

import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "hooks"))

import session_start  # noqa: E402


def git(cwd, *args):
    subprocess.run(["git", *args], cwd=cwd, check=True, capture_output=True)


class SessionStart(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.repo = Path(self.tmp.name) / "repo"
        self.repo.mkdir()
        git(self.repo, "init", "-q", "-b", "main")
        git(self.repo, "config", "user.email", "t@example.com")
        git(self.repo, "config", "user.name", "t")

    def tearDown(self):
        self.tmp.cleanup()

    def test_unset_repo_points_to_kickoff(self):
        report = session_start.report(self.repo, fetch=False)
        self.assertIn("/kickoff", report)

    def test_set_up_repo_reports_state(self):
        (self.repo / "AGENTS.md").write_text("# x\n")
        (self.repo / "docs" / "agents").mkdir(parents=True)
        (self.repo / "docs" / "agents" / "issue-tracker.md").write_text("x\n")
        git(self.repo, "add", ".")
        git(self.repo, "commit", "-q", "-m", "chore: init")
        (self.repo / "scratch.txt").write_text("x\n")
        report = session_start.report(self.repo, fetch=False)
        self.assertNotIn("/kickoff", report)
        self.assertIn("Branch: main", report)
        self.assertIn("1 uncommitted", report)

    def test_reports_commits_behind(self):
        (self.repo / "AGENTS.md").write_text("# x\n")
        (self.repo / "docs" / "agents").mkdir(parents=True)
        (self.repo / "docs" / "agents" / "issue-tracker.md").write_text("x\n")
        git(self.repo, "add", ".")
        git(self.repo, "commit", "-q", "-m", "chore: init")
        clone = Path(self.tmp.name) / "clone"
        git(self.tmp.name, "clone", "-q", str(self.repo), str(clone))
        for i in range(2):
            (self.repo / f"f{i}.txt").write_text("x\n")
            git(self.repo, "add", ".")
            git(self.repo, "commit", "-q", "-m", f"feat: f{i}")
        report = session_start.report(clone, fetch=True)
        self.assertIn("2 commits behind", report)

    def test_not_a_git_repo(self):
        plain = Path(self.tmp.name) / "plain"
        plain.mkdir()
        self.assertIn("/kickoff", session_start.report(plain, fetch=False))

    def test_cloud_session_gets_global_rules(self):
        env = dict(os.environ, CLAUDE_CODE_REMOTE="true")
        self.assertTrue(session_start.include_global_rules(env))
        self.assertFalse(session_start.include_global_rules({}))

    def test_main_prints_config(self):
        (self.repo / ".dstack").mkdir()
        (self.repo / ".dstack" / "config.json").write_text('{"owner": "Ada", "review_bot": "Rex"}')
        env = dict(os.environ, CLAUDE_PROJECT_DIR=str(self.repo), HOME=self.tmp.name,
                   USERPROFILE=self.tmp.name, CLAUDE_CODE_REMOTE="true")
        out = subprocess.run([sys.executable, str(ROOT / "hooks" / "session_start.py")],
                             env=env, capture_output=True, text=True, check=True).stdout
        self.assertIn("- Owner: Ada", out)
        self.assertIn("- Review bot: Rex", out)
        self.assertIn("# Global agent rules", out)


if __name__ == "__main__":
    unittest.main()
