"""guard.yml can't import lib/rules.py, so its copies of the title rule must match it."""

import json
import os
import re
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
WORKFLOW = (ROOT / ".github" / "workflows" / "guard.yml").read_text(encoding="utf-8")
sys.path.insert(0, str(ROOT / "lib"))

import rules  # noqa: E402


def workflow_env(name):
    return re.search(rf"^\s*{name}: '(.*)'$", WORKFLOW, re.MULTILINE).group(1)


def title_script():
    """The python heredoc in the pr-title job, de-indented."""
    body = re.search(r"python3 - <<'EOF'\n(.*?)\n\s*EOF", WORKFLOW, re.DOTALL).group(1)
    lines = body.splitlines()
    indent = min(len(l) - len(l.lstrip()) for l in lines if l.strip())
    return "\n".join(l[indent:] for l in lines)


class GuardWorkflow(unittest.TestCase):
    def test_patterns_match_rules(self):
        self.assertEqual(workflow_env("PR_TITLE_TEMPLATE"), rules.PR_TITLE_TEMPLATE)
        self.assertEqual(workflow_env("ANY_PREFIX"), rules.ANY_PREFIX)
        self.assertEqual(workflow_env("AUTOMATION_PR_PATTERN"), rules.AUTOMATION_PR.pattern)

    def run_title(self, title, config=None):
        with tempfile.TemporaryDirectory() as repo:
            if config is not None:
                (Path(repo) / ".dstack").mkdir()
                (Path(repo) / ".dstack" / "config.json").write_text(
                    config if isinstance(config, str) else json.dumps(config))
            env = dict(os.environ, TITLE=title,
                       PR_TITLE_TEMPLATE=workflow_env("PR_TITLE_TEMPLATE"),
                       ANY_PREFIX=workflow_env("ANY_PREFIX"),
                       AUTOMATION_PR_PATTERN=workflow_env("AUTOMATION_PR_PATTERN"))
            return subprocess.run([sys.executable, "-c", title_script()], cwd=repo, env=env,
                                  capture_output=True, text=True).returncode

    def test_title_script_agrees_with_rules(self):
        cases = [
            ("feat: add menu (ABC-6)", None), ("feat: add menu (ABC-6)", {"ticket_prefix": "ABC"}),
            ("feat: add menu (XYZ-6)", {"ticket_prefix": "ABC"}), ("feat: add menu", None),
            ("chore(bot): sync", {"ticket_prefix": "ABC"}), ("feat: x (A.B-1)", {"ticket_prefix": "A.B"}),
            ("feat: x (AxB-1)", {"ticket_prefix": "A.B"}), ("feat: x (ABC-1)", "{broken"),
            ("feat: x (ABC-1)", {"ticket_prefix": 7}), ("feat: x (ABC-1)", "[1]"),
        ]
        for title, cfg in cases:
            prefix = cfg.get("ticket_prefix", "") if isinstance(cfg, dict) else ""
            want = rules.pr_title_ok(title, prefix if isinstance(prefix, str) else "")
            with self.subTest(title=title, cfg=cfg):
                self.assertEqual(self.run_title(title, cfg) == 0, want)


if __name__ == "__main__":
    unittest.main()
