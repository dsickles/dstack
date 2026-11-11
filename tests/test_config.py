"""Tests for lib/config.py."""

import json
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "lib"))

import config  # noqa: E402


class Config(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.home = Path(self.tmp.name) / "home"
        self.project = Path(self.tmp.name) / "project"
        for d in (self.home, self.project):
            (d / ".dstack").mkdir(parents=True)

    def tearDown(self):
        self.tmp.cleanup()

    def write(self, where, data):
        (where / ".dstack" / "config.json").write_text(
            data if isinstance(data, str) else json.dumps(data))

    def load(self):
        return config.load(self.project, home=self.home)

    def test_defaults_without_files(self):
        self.assertEqual(self.load(), config.DEFAULTS)

    def test_project_overrides_home_key_by_key(self):
        self.write(self.home, {"owner": "Ada", "review_bot": "Rex"})
        self.write(self.project, {"ticket_prefix": "ABC", "review_bot": "Max"})
        cfg = self.load()
        self.assertEqual(cfg["owner"], "Ada")
        self.assertEqual(cfg["review_bot"], "Max")
        self.assertEqual(cfg["ticket_prefix"], "ABC")

    def test_bad_files_and_values_are_ignored(self):
        self.write(self.home, "{not json")
        self.write(self.project, {"owner": "  ", "ticket_prefix": 5, "unknown": "x"})
        self.assertEqual(self.load(), config.DEFAULTS)
        self.write(self.project, "[1, 2]")
        self.assertEqual(self.load(), config.DEFAULTS)

    def test_describe(self):
        self.assertIn("none found", config.describe(config.DEFAULTS))
        text = config.describe(dict(config.DEFAULTS, owner="Ada", ticket_prefix="ABC"))
        self.assertIn("- Owner: Ada", text)
        self.assertIn("- Ticket prefix: ABC", text)
        self.assertNotIn("Review bot", text)


if __name__ == "__main__":
    unittest.main()
