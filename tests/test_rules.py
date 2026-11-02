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

    def test_non_string_command_raises(self):
        with self.assertRaises(TypeError):
            rules.merge_guard_decision("Bash", {"command": ["gh", "pr", "merge"]}, 1, "feature")


if __name__ == "__main__":
    unittest.main()
