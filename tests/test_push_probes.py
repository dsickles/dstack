"""Check the merge guard against real git.

Each probe runs for real in a fresh temp repo whose pre-push hook records the refs git
is about to push, then aborts, so nothing is pushed. That is git's own answer, so it
covers aliases, includes and shell tricks with no rewriting of the command. If git
would update main, the guard must deny; controls that leave main alone must pass.

The guard is called through hooks/pretooluse.py, so saved config (upstream, aliases,
remote.<name>.push) is read the way Claude's hook reads it.

Setup: a bare origin; local main one commit ahead of origin/main; branch `feature`
(created from main) checked out with no upstream and no saved push.default; `../work2`
is a second clone on main, also one commit ahead.
"""

import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

HOOK = Path(__file__).resolve().parent.parent / "hooks" / "pretooluse.py"
GIT = shutil.which("git")
BASH = shutil.which("bash")

# (saved setup run before the guard looks, command). Setup "" means none.
UPDATES_MAIN = [
    # round 3 blockers
    ("", "git push origin refs/heads/*"),
    ("", "git push origin refs/heads/*:refs/heads/*"),
    ("", "git push origin +refs/heads/*"),
    ("", "git push origin :"),
    ("", "FOO=1 git push origin main"),
    ("", "command git push origin main"),
    ("", "env git push origin main"),
    ("", f"{GIT} push origin main"),
    ("", "git status & git push origin main"),
    ("", "git -c push.default=simple -c push.default=matching push"),
    ("", "git -c push.Default=matching push"),
    ("", "git -c PUSH.DEFAULT=matching push"),
    ("", "git -c branch.feature.remote=origin -c branch.feature.merge=refs/heads/main"
         " -c push.default=upstream push"),
    ("", "git -c remote.origin.push=refs/heads/feature:refs/heads/main push origin"),
    ("", "git config push.default matching && git push"),
    ("", "git checkout main && git push origin HEAD"),
    ("", "GIT_CONFIG_COUNT=1 GIT_CONFIG_KEY_0=push.default GIT_CONFIG_VALUE_0=matching git push"),
    # round 4: previous branch
    ("", "git checkout - && git push origin HEAD"),
    ("", "git checkout -q - && git push"),
    ("", "git switch - && git push origin @"),
    ("", "git checkout @{-1} && git push origin HEAD"),
    # round 4: rename onto main
    ("", "git branch -M main && git push origin HEAD"),
    ("", "git branch -M feature main && git push"),
    # round 4: upstream set by git branch -u
    ("", "git branch --set-upstream-to=origin/main && git -c push.default=upstream push"),
    ("git config push.default upstream", "git branch -u origin/main && git push"),
    # round 4: every remote.<name>.push value, and the saved ones
    ("", "git -c remote.origin.push=refs/heads/feature:refs/heads/main"
         " -c remote.origin.push=refs/heads/feature:refs/heads/feature push origin"),
    ("", "git config --add remote.origin.push refs/heads/feature:refs/heads/main &&"
         " git config --add remote.origin.push refs/heads/feature:refs/heads/feature &&"
         " git push origin"),
    ("git config remote.origin.push refs/heads/feature:refs/heads/main", "git push origin"),
    # round 4: aliases, from -c, from git config in the command, and saved
    ("", "git -c alias.ship='push origin main' ship"),
    ("", "git -c alias.ship='push origin HEAD:refs/heads/main' ship"),
    ("", "git -c alias.ship='push --all' ship"),
    ("", "git -c alias.ship='!git push origin main' ship"),
    ("", "git config alias.ship 'push origin main' && git ship"),
    ("git config alias.ship 'push origin main'", "git ship"),
    ("git config alias.Ship 'push origin main'", "git SHIP"),
    # round 4: include.path
    ("", "printf '[push]\\ndefault = matching\\n' > inc && git -c include.path=$PWD/inc push"),
    # round 4: cd behind a wrapper
    ("", "command cd ../work2 && git push origin HEAD"),
    ("", "builtin cd ../work2 && git push origin HEAD"),
]

LEAVES_MAIN = [
    ("", "git push origin feature"),
    ("", "git push -u origin HEAD"),
    ("", "git push origin feature:feature"),
    ("", "git -c push.default=matching -c push.default=simple push origin feature"),
    ("", "git push origin maintenance-fix:maintenance-fix"),
    ("", "git branch -m feature2 && git push origin HEAD"),
    ("", "git -c alias.p='push origin feature' p"),
    ("git config alias.p 'push -u origin HEAD'", "git p"),
    ("", "git -c alias.push='push origin main' push origin feature"),
]


def sh(cmd, cwd, check=True):
    return subprocess.run([BASH, "-c", cmd], cwd=cwd, capture_output=True, text=True,
                          check=check, env=dict(os.environ, GIT_TERMINAL_PROMPT="0"))


RECORDER = """#!/usr/bin/env bash
cat >> "$(git rev-parse --git-common-dir)/pushed-refs"
exit 1
"""


def guard(cmd, repo):
    payload = {"tool_name": "Bash", "tool_input": {"command": cmd}, "cwd": str(repo)}
    r = subprocess.run([sys.executable, str(HOOK)], input=json.dumps(payload), text=True,
                       capture_output=True, check=True,
                       env=dict(os.environ, CLAUDE_PROJECT_DIR=str(repo)))
    return json.loads(r.stdout)["hookSpecificOutput"]["permissionDecision"] if r.stdout.strip() else None


@unittest.skipUnless(GIT and BASH, "git or bash not installed")
class PushProbes(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.TemporaryDirectory()
        root = Path(cls.tmp.name) / "template"
        root.mkdir()
        cfg = "-c user.name=t -c user.email=t@t -c init.defaultBranch=main"
        sh(f"git {cfg} init -q --bare origin.git", root)
        sh(f"git {cfg} init -q work", root)
        work = root / "work"
        for cmd in ["git config user.name t", "git config user.email t@t",
                    "git remote add origin ../origin.git",
                    "git commit -q --allow-empty -m base", "git push -q origin main",
                    "git branch -u origin/main main",
                    "git commit -q --allow-empty -m ahead",
                    "git checkout -q -b feature", "git commit -q --allow-empty -m feat",
                    "git branch maintenance-fix"]:
            sh(cmd, work)
        sh(f"git {cfg} clone -q origin.git work2", root)
        sh("git -c user.name=t -c user.email=t@t commit -q --allow-empty -m ahead2", root / "work2")
        hooks = root / "hooks"
        hooks.mkdir()
        (hooks / "pre-push").write_text(RECORDER)
        (hooks / "pre-push").chmod(0o755)
        for repo in (work, root / "work2"):
            sh("git config core.hooksPath ../hooks", repo)
            (repo / "AGENTS.md").write_text("**Autonomy level:** 2 Build\n")
        cls.template = root

    @classmethod
    def tearDownClass(cls):
        cls.tmp.cleanup()

    def probe(self, setup, cmd, n):
        """Fresh repos per probe. Returns (guard decision, whether git would update main)."""
        root = Path(self.tmp.name) / f"{self._testMethodName}-{n}"
        shutil.copytree(self.template, root, symlinks=True)
        work = root / "work"
        if setup:
            sh(setup, work)
        decision = guard(cmd, work)
        sh(cmd, work, check=False)
        pushed = ""
        for repo in (work, root / "work2"):
            log = repo / ".git" / "pushed-refs"
            pushed += log.read_text() if log.exists() else ""
        # pre-push stdin: <local ref> <local sha> <remote ref> <remote sha>
        updates = any(f.split()[2] == "refs/heads/main" and f.split()[1] != f.split()[3]
                      for f in pushed.splitlines() if len(f.split()) == 4)
        return decision, updates

    def test_pushes_that_update_main_are_denied(self):
        for n, (setup, cmd) in enumerate(UPDATES_MAIN):
            with self.subTest(cmd=cmd, setup=setup):
                decision, updates = self.probe(setup, cmd, n)
                self.assertTrue(updates, "probe no longer updates main in git")
                self.assertEqual(decision, "deny")

    def test_pushes_that_leave_main_alone_pass(self):
        for n, (setup, cmd) in enumerate(LEAVES_MAIN):
            with self.subTest(cmd=cmd, setup=setup):
                decision, updates = self.probe(setup, cmd, n)
                self.assertFalse(updates)
                self.assertIsNone(decision)


if __name__ == "__main__":
    unittest.main()
