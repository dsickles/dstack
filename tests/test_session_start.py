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

    def test_cloud_session_gets_how_i_work(self):
        env = dict(os.environ, CLAUDE_CODE_REMOTE="true")
        self.assertTrue(session_start.include_how_i_work(env))
        self.assertFalse(session_start.include_how_i_work({}))


if __name__ == "__main__":
    unittest.main()
