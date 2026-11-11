"""Tests for scripts/leak_check.py against a throwaway git repo."""

import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))

import leak_check  # noqa: E402


class LeakCheck(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.repo = Path(self.tmp.name)
        subprocess.run(["git", "init", "-q"], cwd=self.repo, check=True)
        (self.repo / "scripts").mkdir()
        self.assertEqual(leak_check.main(["x", "--add", "Zorblat"], self.repo), 0)

    def tearDown(self):
        self.tmp.cleanup()

    def track(self, name, data):
        path = self.repo / name
        path.write_bytes(data) if isinstance(data, bytes) else path.write_text(data)
        subprocess.run(["git", "add", name], cwd=self.repo, check=True)

    def test_the_word_itself_is_not_stored(self):
        stored = (self.repo / leak_check.HASHES).read_text()
        self.assertNotIn("zorblat", stored.lower())
        self.assertIn(leak_check.digest("ZORBLAT"), stored)

    def test_finds_any_case_and_names_only_file_and_line(self):
        self.track("a.md", "fine\nask zorblat-12 (ZORBLAT's)\n")
        self.assertEqual(leak_check.find_leaks(self.repo, leak_check.load_hashes(self.repo)),
                         ["a.md:2"])
        self.assertEqual(leak_check.main(["x"], self.repo), 1)

    def test_ignores_untracked_binary_and_partial_words(self):
        self.track("b.md", "zorblats and xzorblat are other words\n")
        self.track("c.bin", b"\xff\xfe zorblat \x00")
        (self.repo / "untracked.md").write_text("zorblat\n")
        self.assertEqual(leak_check.main(["x"], self.repo), 0)

    def test_dstack_itself_is_clean(self):
        self.assertEqual(leak_check.main(["x"], ROOT), 0)


if __name__ == "__main__":
    unittest.main()
