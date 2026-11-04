"""Check the merge guard against real git: every probe is dry-run in a temp repo.

If git's dry-run would update main, the guard must deny. Controls that leave main alone
must pass. Setup: a bare origin; local main one commit ahead of origin/main; branch
`feature` checked out with no upstream and no saved push.default.
"""

import os
import re
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "lib"))

import rules  # noqa: E402

GIT = shutil.which("git")

UPDATES_MAIN = [
    # round 2/3 blocker 1: glob refspecs
    "git push origin refs/heads/*",
    "git push origin refs/heads/*:refs/heads/*",
    "git push origin +refs/heads/*",
    "git push origin :",
    # blocker 2: git not the first word
    "FOO=1 git push origin main",
    "command git push origin main",
    "env git push origin main",
    f"{GIT} push origin main",
    "git status & git push origin main",
    # blocker 3: last -c wins, key is case-insensitive (no saved upstream)
    "git -c push.default=simple -c push.default=matching push",
    "git -c push.Default=matching push",
    "git -c PUSH.DEFAULT=matching push",
    # blocker 4: upstream set on the command line
    "git -c branch.feature.remote=origin -c branch.feature.merge=refs/heads/main"
    " -c push.default=upstream push",
    "git -c remote.origin.push=refs/heads/feature:refs/heads/main push origin",
    # same class: earlier parts of the command change what a bare push does
    "git config push.default matching && git push",
    "git checkout main && git push origin HEAD",
    "GIT_CONFIG_COUNT=1 GIT_CONFIG_KEY_0=push.default GIT_CONFIG_VALUE_0=matching git push",
]

LEAVES_MAIN = [
    "git push origin feature",
    "git push -u origin HEAD",
    "git push origin feature:feature",
    "git -c push.default=matching -c push.default=simple push origin feature",
    "git push origin maintenance-fix:maintenance-fix",
]


def sh(cmd, cwd, check=True):
    return subprocess.run(cmd, cwd=cwd, shell=True, capture_output=True, text=True,
                          check=check, env=dict(os.environ, GIT_TERMINAL_PROMPT="0"))


def main_updated(porcelain: str) -> bool:
    for line in porcelain.splitlines():
        parts = line.split("\t")
        if len(parts) >= 2 and parts[1].endswith(":refs/heads/main") and parts[0] not in "=!":
            return True
    return False


@unittest.skipUnless(GIT, "git not installed")
class PushProbes(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.TemporaryDirectory()
        root = Path(cls.tmp.name) / "template"
        root.mkdir()
        cfg = "-c user.name=t -c user.email=t@t -c init.defaultBranch=main"
        sh(f"git {cfg} init -q --bare origin.git", root)
        sh(f"git {cfg} init -q work", root)
        for cmd in ["git config user.name t", "git config user.email t@t",
                    "git remote add origin ../origin.git",
                    "git commit -q --allow-empty -m base", "git push -q origin main",
                    "git branch -u origin/main main",
                    "git commit -q --allow-empty -m ahead",
                    "git checkout -q -b feature", "git commit -q --allow-empty -m feat",
                    "git branch maintenance-fix"]:
            sh(cmd, root / "work")
        cls.template = root

    @classmethod
    def tearDownClass(cls):
        cls.tmp.cleanup()

    def fresh_repo(self, name):
        root = Path(self.tmp.name) / name
        shutil.copytree(self.template, root, symlinks=True)
        return root / "work"

    def dry_run(self, cmd, n):
        """Fresh repo per probe, so a probe that checks out main or writes config can't
        leak into the next one."""
        dry = re.sub(r"(?<=\s)push(?=\s|$)", "push --dry-run --porcelain", cmd, count=1)
        r = sh(dry, self.fresh_repo(f"{self._testMethodName}-{n}"), check=False)
        return main_updated(r.stdout)

    def guard(self, cmd):
        return rules.merge_guard_decision("Bash", {"command": cmd}, 2, "feature", None, None)

    def test_pushes_that_update_main_are_denied(self):
        for n, cmd in enumerate(UPDATES_MAIN):
            with self.subTest(cmd=cmd):
                self.assertTrue(self.dry_run(cmd, n), "probe no longer updates main in git")
                self.assertEqual(self.guard(cmd), "deny")

    def test_pushes_that_leave_main_alone_pass(self):
        for n, cmd in enumerate(LEAVES_MAIN):
            with self.subTest(cmd=cmd):
                self.assertFalse(self.dry_run(cmd, n))
                self.assertIsNone(self.guard(cmd))


if __name__ == "__main__":
    unittest.main()
