"""Fail if a tracked file names the owner, their company or other private words.

The words themselves never enter the repo: scripts/leak-hashes.txt holds the sha256 of
each lower-case word, and every word in every tracked text file is hashed and compared.
Output names only the file and line, so CI logs don't repeat the word either.

  python3 scripts/leak_check.py             check (check.sh runs this)
  python3 scripts/leak_check.py --add WORD  add a word's hash to the list
"""

import hashlib
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
HASHES = "scripts/leak-hashes.txt"
WORD = re.compile(r"[A-Za-z0-9]+")


def digest(word: str) -> str:
    return hashlib.sha256(word.lower().encode()).hexdigest()


def load_hashes(repo: Path) -> set:
    path = repo / HASHES
    if not path.exists():
        return set()
    return {l.split()[0] for l in path.read_text(encoding="utf-8").splitlines()
            if l.strip() and not l.startswith("#")}


def find_leaks(repo: Path, hashes: set):
    files = subprocess.run(["git", "ls-files", "-z"], cwd=repo, check=True,
                           capture_output=True).stdout.decode().split("\0")
    hits = []
    for name in filter(None, files):
        try:
            text = (repo / name).read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError):
            continue  # binary or unreadable
        for n, line in enumerate(text.splitlines(), 1):
            if any(digest(w) in hashes for w in WORD.findall(line)):
                hits.append(f"{name}:{n}")
    return hits


def main(argv, repo: Path = ROOT) -> int:
    if len(argv) == 3 and argv[1] == "--add":
        with open(repo / HASHES, "a", encoding="utf-8") as f:
            f.write(digest(argv[2]) + "\n")
        print("leak check: added one word")
        return 0
    hits = find_leaks(repo, load_hashes(repo))
    if not hits:
        print("leak check: no private words")
        return 0
    print("leak check: a private word (see scripts/leak-hashes.txt) appears at:", file=sys.stderr)
    for h in hits:
        print(f"  {h}", file=sys.stderr)
    return 1


if __name__ == "__main__":
    sys.exit(main(sys.argv))
