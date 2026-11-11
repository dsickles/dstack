"""Tests for scripts/version_check.py against a throwaway git repo."""

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))

import version_check  # noqa: E402


def _git(repo, *args):
    subprocess.run(["git", *args], cwd=repo, check=True, capture_output=True,
                   env={"GIT_AUTHOR_NAME": "t", "GIT_AUTHOR_EMAIL": "t@t",
                        "GIT_COMMITTER_NAME": "t", "GIT_COMMITTER_EMAIL": "t@t",
                        "PATH": "/usr/bin:/bin:/usr/local/bin"})


class VersionCheck(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.repo = Path(self.tmp.name)
        _git(self.repo, "init", "-q", "-b", "main")
        (self.repo / ".claude-plugin").mkdir()
        self._version("0.1.0")
        (self.repo / "lib").mkdir()
        (self.repo / "lib" / "rules.py").write_text("x = 1\n" * 20)
        (self.repo / "GLOBAL-AGENTS.md").write_text("rules\n" * 20)
        _git(self.repo, "add", "-A")
        _git(self.repo, "commit", "-qm", "base")
        self.base = subprocess.run(["git", "rev-parse", "HEAD"], cwd=self.repo,
                                   capture_output=True, text=True).stdout.strip()

    def tearDown(self):
        self.tmp.cleanup()

    def _version(self, v):
        (self.repo / ".claude-plugin" / "plugin.json").write_text(json.dumps({"version": v}))

    def _commit(self):
        _git(self.repo, "add", "-A")
        _git(self.repo, "commit", "-qm", "change")

    def check(self):
        return version_check.main(self.base, self.repo)

    def test_rename_out_of_a_shipped_path_needs_a_bump(self):
        for src, dst in [("GLOBAL-AGENTS.md", "docs/GLOBAL-AGENTS.md"), ("lib/rules.py", "old/rules.py")]:
            with self.subTest(src=src):
                _git(self.repo, "reset", "-q", "--hard", self.base)
                (self.repo / dst).parent.mkdir(exist_ok=True)
                _git(self.repo, "mv", src, dst)
                self._commit()
                self.assertEqual(self.check(), 1)

    def test_shipped_edit_passes_only_with_a_bump(self):
        (self.repo / "lib" / "rules.py").write_text("x = 2\n")
        self._commit()
        self.assertEqual(self.check(), 1)
        self._version("0.1.1")
        self._commit()
        self.assertEqual(self.check(), 0)

    def test_docs_only_change_passes(self):
        (self.repo / "docs").mkdir()
        (self.repo / "docs" / "a.md").write_text("a\n")
        self._commit()
        self.assertEqual(self.check(), 0)

    def test_empty_base_fails(self):
        self.assertEqual(version_check.main("", self.repo), 1)


if __name__ == "__main__":
    unittest.main()
