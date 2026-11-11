"""The owner's personal settings, kept out of the shared kit.

Read from `~/.dstack/config.json` (the owner's defaults) and then the project's
`.dstack/config.json`, which wins key by key. Missing keys fall back to generic words, so
the kit works with no config at all. A file that can't be read is ignored.
"""

import json
from pathlib import Path

DEFAULTS = {
    "owner": "the owner",
    "about": "",
    "tracker": "the issue tracker named in this repo's docs/agents/issue-tracker.md",
    "ticket_prefix": "",
    "review_bot": "the review bot",
}

LABELS = {
    "owner": "Owner",
    "about": "About the owner",
    "tracker": "Issue tracker",
    "ticket_prefix": "Ticket prefix",
    "review_bot": "Review bot",
}


def _read(path: Path) -> dict:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {}
    if not isinstance(data, dict):
        return {}
    return {k: v.strip() for k, v in data.items() if k in DEFAULTS and isinstance(v, str)
            and v.strip()}


def load(project_dir=None, home=None) -> dict:
    cfg = dict(DEFAULTS)
    cfg.update(_read(Path(home or Path.home()) / ".dstack" / "config.json"))
    if project_dir:
        cfg.update(_read(Path(project_dir) / ".dstack" / "config.json"))
    return cfg


def describe(cfg: dict) -> str:
    """Plain lines for the session start, only for keys that differ from the defaults."""
    lines = [f"- {LABELS[k]}: {cfg[k]}" for k in DEFAULTS if cfg.get(k) and cfg[k] != DEFAULTS[k]]
    if not lines:
        return ("dstack config: none found. Rules say \"the owner\"; add .dstack/config.json "
                "to name them (see the dstack README).")
    return "dstack config (who \"the owner\" and the other roles in the rules are):\n" + \
        "\n".join(lines)
