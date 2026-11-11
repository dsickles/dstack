"""Tests for lib/rules.py: the pure logic behind the git hooks, CI guard and Claude hooks."""

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "lib"))

import rules  # noqa: E402


class CommitMessage(unittest.TestCase):
    def test_accepts(self):
        for msg in [
            "feat: add menu",
            "fix(engine): round cents down",
            "feat!: drop old save format",
            "chore(digest): daily transient retry 2026-W39",
            "docs: explain check (DAS-66)",
            "capture: 2026-11-01-caleb-solids",
            "triage: 3 inbox items (sydney, rocky)",
            "Merge pull request #10 from dsickles/foo",
            "Merge branch 'main' into feature",
            'Revert "feat: add menu"',
            "# a comment line\nfeat: add menu",
        ]:
            with self.subTest(msg=msg):
                self.assertTrue(rules.commit_msg_ok(msg))

    def test_rejects(self):
        for msg in [
            "Add CLAUDE.md with the Linear-first process",
            "WIP",
            "feat:no space",
            "Feat: capitalised type",
            "feature: unknown type",
            "",
            "# only a comment",
            "fixup! feat: add menu",
            "squash! feat: add menu",
            "amend! feat: add menu",
        ]:
            with self.subTest(msg=msg):
                self.assertFalse(rules.commit_msg_ok(msg))


class PrTitle(unittest.TestCase):
    def test_accepts(self):
        for title in [
            "feat: add menu (DAS-66)",
            "fix(saves): keep last slot (DAS-7)",
            "chore: kickoff (DAS-125)",
            "chore(digest): weekly digest 2026-W44",
        ]:
            with self.subTest(title=title):
                self.assertTrue(rules.pr_title_ok(title))

    def test_rejects(self):
        for title in [
            "DAS-121: local model harness",
            "feat: add menu",
            "feat: add menu (DAS-66, DAS-67)",
            "Roadmap 2.0 living blueprints",
            "feat: add menu (das-66)",
        ]:
            with self.subTest(title=title):
                self.assertFalse(rules.pr_title_ok(title))


class ApprovalGate(unittest.TestCase):
    def test_asks_for_messages_to_people(self):
        for tool in [
            "mcp__gmail__send_email",
            "mcp__1234-abcd__send_message",
            "mcp__slack__slack_post_message",
            "mcp__gcal__create_event",
            "mcp__gcal__update_event",
            "mcp__mail__reply_to_thread",
            "mcp__mail__forward_email",
            "mcp__messages__send_text",
            "mcp__google-calendar__create_events",
            "mcp__google-calendar__update_events",
            "mcp__gmail__SendEmail",
            "mcp__gmail__sendEmail",
            "mcp__slack__postMessage",
            "mcp__slack__chat_postMessage",
        ]:
            with self.subTest(tool=tool):
                self.assertEqual(rules.gate_decision(tool), "ask")

    def test_lets_trackers_and_reads_through(self):
        for tool in [
            "mcp__383cf952-f48a__save_comment",
            "mcp__383cf952-f48a__save_issue",
            "mcp__github__add_issue_comment",
            "mcp__github__create_pull_request",
            "mcp__gmail__search_threads",
            "mcp__gcal__list_events",
            "mcp__ccd_session_mgmt__send_message",
            "Bash",
        ]:
            with self.subTest(tool=tool):
                self.assertIsNone(rules.gate_decision(tool))

    def test_lets_claude_app_thread_tools_through(self):
        for tool in [
            "mcp__hearthbot__post_message",
            "mcp__hearthbot__message_coordinator",
            "mcp__hearthbot__message_thread",
            "mcp__claude-code-remote__send_later",
        ]:
            with self.subTest(tool=tool):
                self.assertIsNone(rules.gate_decision(tool))


class Autonomy(unittest.TestCase):
    def test_parse(self):
        self.assertEqual(rules.parse_autonomy("x\n**Autonomy level:** 3 Automate (cron)\n"), 3)
        self.assertEqual(rules.parse_autonomy("Autonomy level: 1 Shape"), 1)
        self.assertIsNone(rules.parse_autonomy("no level here"))
        self.assertIsNone(rules.parse_autonomy(None))

    def test_only_whole_levels_on_the_declaration_line(self):
        self.assertIsNone(rules.parse_autonomy("Autonomy level: 30"))
        self.assertIsNone(rules.parse_autonomy("Autonomy level: 4"))
        self.assertEqual(rules.parse_autonomy("# Note: Autonomy level: 3\n**Autonomy level:** 1 Shape\n"), 1)
        self.assertIsNone(rules.parse_autonomy("We may reach Autonomy level: 3 later"))
        self.assertEqual(rules.parse_autonomy("Autonomy level: 3\nAutonomy level: 1\n"), 1)


class MergeGuard(unittest.TestCase):
    def bash(self, cmd, branch="feature", autonomy=2, upstream=None, push_default=None):
        return rules.merge_guard_decision("Bash", {"command": cmd}, autonomy, branch,
                                          upstream, push_default)

    def test_denies_merges_and_main_pushes(self):
        for cmd in [
            "gh pr merge 12 --squash",
            "cd repo && gh pr merge --auto",
            "git push origin main",
            "git push -u origin HEAD:main",
            "git push origin master",
            "git push --force origin +main",
            "npm test; git push origin main",
            "git push origin --all",
            "git push --mirror origin",
            "git status\ngh pr merge 1 --squash",
            "FOO=1 gh pr merge 1",
            "command gh pr merge 1",
            "bash -c 'gh pr merge 1'",
            "gh.exe pr merge 1",
            "GH pr merge 1",
            "gh api --method PUT repos/o/r/pulls/1/merge",
        ]:
            with self.subTest(cmd=cmd):
                self.assertEqual(self.bash(cmd), "deny")

    def test_denies_bare_push_on_main(self):
        self.assertEqual(self.bash("git push", branch="main"), "deny")
        self.assertEqual(self.bash("git push origin", branch="master"), "deny")

    def test_head_means_the_current_branch(self):
        self.assertEqual(self.bash("git push origin HEAD", branch="main"), "deny")
        self.assertEqual(self.bash("git push origin @", branch="main"), "deny")
        self.assertIsNone(self.bash("git push -u origin HEAD", branch="feature"))

    def test_bare_push_follows_upstream_and_push_default(self):
        self.assertEqual(self.bash("git -c push.default=upstream push", upstream="main"), "deny")
        self.assertEqual(self.bash("git push", upstream="main"), "deny")
        self.assertEqual(self.bash("git -c push.default=matching push"), "deny")
        self.assertEqual(self.bash("git push", push_default="matching"), "deny")
        self.assertIsNone(self.bash("git push", upstream="feature", push_default="simple"))

    def test_allows_branch_work(self):
        for cmd in [
            "git push -u origin sicklesdan/das-125-dstack",
            "git push",
            "gh pr create --draft",
            "gh pr view 12",
            "git push origin maintenance-fix",
            "echo merge main",
        ]:
            with self.subTest(cmd=cmd):
                self.assertIsNone(self.bash(cmd))

    def test_denies_mcp_merges(self):
        for tool in ["mcp__github__merge_pull_request", "mcp__383cf952__merge_diff"]:
            with self.subTest(tool=tool):
                self.assertEqual(rules.merge_guard_decision(tool, {}, 1, "feature"), "deny")

    def test_level_three_allows_everything(self):
        self.assertIsNone(self.bash("git push origin main", autonomy=3))
        self.assertIsNone(self.bash("gh pr merge 3", autonomy=3))

    def test_unknown_level_is_guarded(self):
        self.assertEqual(self.bash("gh pr merge 3", autonomy=None), "deny")

    # Hopper round 3 blockers. tests/test_push_probes.py checks the pushes against real git.
    def test_glob_and_matching_refspecs_are_denied(self):
        for cmd in ["git push origin refs/heads/*", "git push origin refs/heads/*:refs/heads/*",
                    "git push origin +refs/heads/*", "git push origin 'refs/heads/*'",
                    "git push origin :", "git push origin +:"]:
            with self.subTest(cmd=cmd):
                self.assertEqual(self.bash(cmd), "deny")

    def test_git_found_after_assignments_wrappers_and_paths(self):
        for cmd in ["FOO=1 git push origin main", "command git push origin main",
                    "env git push origin main", "env FOO=1 git push origin main",
                    "/usr/bin/git push origin main", "sudo git push origin main",
                    "sudo -u dan git push origin main", "exec git push origin main",
                    "nohup git push origin main", "time git push origin main",
                    "git.exe push origin main", "Git push origin main", "GIT.EXE push origin main",
                    r'"C:\Program Files\Git\bin\git.exe" push origin main',
                    "(git push origin main)", "git status & git push origin main",
                    "git -C . push origin main", "git --no-pager push origin main"]:
            with self.subTest(cmd=cmd):
                self.assertEqual(self.bash(cmd), "deny")

    def test_last_push_default_wins_and_key_is_case_insensitive(self):
        # No saved upstream, or the upstream-is-main check would hide the bug.
        for cmd in ["git -c push.default=simple -c push.default=matching push",
                    "git -c push.Default=matching push", "git -c PUSH.DEFAULT=matching push",
                    "git --config-env=push.default=PD push"]:
            with self.subTest(cmd=cmd):
                self.assertEqual(self.bash(cmd, upstream=None, push_default=None), "deny")
        self.assertIsNone(self.bash("git -c push.default=matching -c push.default=simple push"))
        self.assertEqual(self.bash("git -c push.default=simple push", push_default="matching"),
                         None)

    def test_upstream_set_on_the_command_line(self):
        cmd = ("git -c branch.feature.remote=origin -c branch.feature.merge=refs/heads/main "
               "-c push.default=upstream push")
        self.assertEqual(self.bash(cmd), "deny")
        self.assertEqual(self.bash("git -c Branch.feature.Merge=refs/heads/main push"), "deny")
        # The branch name is case-sensitive: this sets another branch's upstream.
        self.assertIsNone(self.bash("git -c branch.Feature.merge=refs/heads/main push"))
        self.assertIsNone(self.bash("git -c branch.feature.merge=refs/heads/feature push"))
        self.assertEqual(self.bash("git -c remote.origin.push=HEAD:main push origin"), "deny")

    def test_quoted_gh_pr_merge(self):
        for cmd in ['gh pr "merge" 1', "gh pr 'merge' 1", 'gh "pr" merge 1', "'gh' pr merge 1",
                    "FOO=1 /usr/local/bin/gh pr 'merge' 1", 'gh "api" -X PUT repos/o/r/pulls/1/merge']:
            with self.subTest(cmd=cmd):
                self.assertEqual(self.bash(cmd), "deny")

    def test_earlier_parts_of_the_command_count(self):
        for cmd in ["git config push.default matching && git push",
                    "git config set push.default matching; git push",
                    "git config branch.feature.merge refs/heads/main && git push",
                    "git checkout main && git push", "git switch main && git push origin HEAD",
                    "git checkout -b fresh origin/main && git push",
                    "cd ../other && git push", "GIT_CONFIG_PARAMETERS=x git push"]:
            with self.subTest(cmd=cmd):
                self.assertEqual(self.bash(cmd), "deny")
        for cmd in ["git config --get push.default && git push",
                    "git checkout -- README.md && git push",
                    "git checkout -b fresh && git push -u origin fresh",
                    "cd sub && git push origin feature"]:
            with self.subTest(cmd=cmd):
                self.assertIsNone(self.bash(cmd))

    # Hopper round 4. tests/test_push_probes.py runs each one against real git.
    def test_round_four_state_changes(self):
        for cmd in ["git checkout - && git push origin HEAD", "git switch - && git push",
                    "git checkout @{-1} && git push origin HEAD",
                    "git branch -M main && git push origin HEAD",
                    "git branch -M feature main && git push",
                    "git branch -u origin/main && git push",
                    "git branch --set-upstream-to=origin/main && git push",
                    "command cd ../x && git push origin HEAD",
                    "builtin cd ../x && git push", "git -c include.path=/tmp/x push",
                    "git -c includeIf.onbranch:feature.path=/tmp/x push"]:
            with self.subTest(cmd=cmd):
                self.assertEqual(self.bash(cmd), "deny")
        for cmd in ["git branch -m feature2 && git push origin HEAD",
                    "git branch -u origin/feature && git push",
                    "git branch -M old main && git push origin HEAD"]:
            with self.subTest(cmd=cmd):
                self.assertIsNone(self.bash(cmd))

    def test_every_remote_push_value_counts(self):
        cmd = ("git -c remote.origin.push=refs/heads/feature:refs/heads/main "
               "-c remote.origin.push=refs/heads/feature:refs/heads/feature push origin")
        self.assertEqual(self.bash(cmd), "deny")
        saved = ["refs/heads/feature:refs/heads/feature", "HEAD:refs/heads/main"]
        self.assertEqual(rules.merge_guard_decision("Bash", {"command": "git push origin"}, 2,
                                                    "feature", remote_push=saved), "deny")
        self.assertIsNone(rules.merge_guard_decision("Bash", {"command": "git push origin feature"},
                                                     2, "feature", remote_push=saved))

    def test_aliases_are_expanded(self):
        for cmd in ["git -c alias.ship='push origin main' ship",
                    "git -c alias.ship='!git push origin main' ship",
                    "git -c alias.ship='!f() { git push origin main; }; f' ship",
                    "git config alias.ship 'push --all' && git ship",
                    "git -c alias.a=b -c alias.b=a a"]:
            with self.subTest(cmd=cmd):
                self.assertEqual(self.bash(cmd), "deny")
        saved = {"ship": "push origin HEAD:main", "p": "push -u origin HEAD"}
        decide = lambda c: rules.merge_guard_decision("Bash", {"command": c}, 2, "feature",
                                                      aliases=saved)
        self.assertEqual(decide("git Ship"), "deny")
        self.assertIsNone(decide("git p"))
        self.assertIsNone(self.bash("git -c alias.push='push origin main' push origin feature"))

    # Hopper round 5. tests/test_push_probes.py runs each one against real git.
    def test_round_five(self):
        for cmd in ["env -i -C ../x git push origin HEAD", "if cd ../x; then git push; fi",
                    "GIT_DIR=../x/.git git push origin @", "git checkout --orphan=main && git push",
                    "git -c remote.origin.mirror=yes push origin",
                    "GIT_CONFIG_COUNT=1 git ship", "git -c include.path=/x ship",
                    "git http-push https://x/r.git main", "git send-pack ../o.git",
                    "git send-pack --all ../o.git"]:
            with self.subTest(cmd=cmd):
                self.assertEqual(self.bash(cmd), "deny")
        self.assertEqual(rules.merge_guard_decision("Bash", {"command": "git push origin"}, 2,
                                                    "feature", mirror=True), "deny")
        for cmd in ["git config --type bool core.x true && git push origin feature",
                    "GIT_DIR=../x/.git git log", "env FOO=1 git push origin feature",
                    "git symbolic-ref HEAD refs/heads/fix && git push origin HEAD"]:
            with self.subTest(cmd=cmd):
                self.assertIsNone(self.bash(cmd))

    def test_non_string_command_raises(self):
        with self.assertRaises(TypeError):
            rules.merge_guard_decision("Bash", {"command": ["gh", "pr", "merge"]}, 1, "feature")

class PluginVersion(unittest.TestCase):
    def test_shipped_changes_need_a_bump(self):
        for files in [["lib/rules.py"], ["hooks/hooks.json"], ["skills/kickoff/SKILL.md"],
                      ["HOW-I-WORK.md"], ["templates/AGENTS.md"], ["docs/x.md", "lib/rules.py"]]:
            with self.subTest(files=files):
                self.assertTrue(rules.version_bump_needed(files))

    def test_docs_tests_and_ci_need_no_bump(self):
        for files in [[], ["docs/architecture.md"], ["tests/test_rules.py"],
                      [".github/workflows/ci.yml"], ["README.md", "AGENTS.md"],
                      ["libx/a.py"], ["scripts/check.sh"]]:
            with self.subTest(files=files):
                self.assertFalse(rules.version_bump_needed(files))

    def test_version_raised(self):
        self.assertTrue(rules.version_raised("0.1.0", "0.1.1"))
        self.assertTrue(rules.version_raised("0.1.9", "0.2.0"))
        self.assertTrue(rules.version_raised("0.9.0", "0.10.0"))
        self.assertFalse(rules.version_raised("0.1.0", "0.1.0"))
        self.assertFalse(rules.version_raised("0.2.0", "0.1.9"))
        self.assertFalse(rules.version_raised("0.1.0", "banana"))


if __name__ == "__main__":
    unittest.main()
