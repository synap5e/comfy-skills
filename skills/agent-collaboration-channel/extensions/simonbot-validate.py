#!/usr/bin/env python3
"""simonbot extension checks layered on the shared agent-collab validator."""

from __future__ import annotations

import html
import importlib.util
import re
import sys
from pathlib import Path

_BASE = Path(__file__).resolve().parent.parent / "scripts" / "validate-message.py"
_spec = importlib.util.spec_from_file_location("validate_message", _BASE)
assert _spec and _spec.loader
base = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(base)

_BOLD = re.compile(r"(?m)^[*_]+([A-Za-z][A-Za-z ]*:)[*_]+")


def _field(name: str, text: str) -> bool:
    # A field starts a line, or follows " · " on a packed meta line (`Obligation: OBL-3 · Status: open · Owed by: a`).
    return bool(re.search(rf"(?im)(?:^|\s·\s)[*_]*{name}[*_]*:\s*\S+", text))


TOP_LEVEL_LIMIT = 400
_LINK = re.compile(r"<[^>|]+\|([^>]+)>|<([^>]+)>")
_STATE_KEYS = "Obligation|Status|Owed by|Owed to|Waiting on|Priority|Claim|Claim until|Next check|Decision owner"
_FIELD_LINE = re.compile(rf"^\s*[*_]*(?:{_STATE_KEYS})[*_]*:\s*\S", re.I)
_ENVELOPE = re.compile(r"^\s*\[agent-collab/[^\]]+\]")
_ENVELOPE_FIELD = re.compile(r"^\s*(from|to|work)\s*:", re.I)


def prose_length(text: str) -> int:
    """Characters people read on a top-level card: no envelope line(s), no `Key: value` field lines (packed or not),
    Slack links counted as their label. WHY: the 400-char limit is about reading; field lines are state (obl-post
    applies the same rule, so hand-posted and tool-posted cards are measured alike)."""
    kept = []
    for line in text.splitlines():
        if _ENVELOPE.match(line) or _ENVELOPE_FIELD.match(line) or line.strip().lower().startswith("x-"):
            continue
        if _FIELD_LINE.match(line):
            continue
        kept.append(_LINK.sub(lambda m: m.group(1) or m.group(2), line))
    return len("\n".join(kept).strip().replace("~", ""))


def validate(text: str, **kwargs) -> list[str]:
    text = _BOLD.sub(r"\1", html.unescape(text))
    threaded = kwargs.pop("threaded", False)
    # WHY threaded=True for the base: the base counts every character toward 400; this extension counts prose only.
    errors = base.validate(text, threaded=True, **kwargs)
    if not threaded and prose_length(text) > TOP_LEVEL_LIMIT:
        errors.append(f"top-level prose is {prose_length(text)} chars (limit {TOP_LEVEL_LIMIT}, field lines excluded); move detail to a thread")
    first = next((ln.strip() for ln in text.splitlines() if ln.strip()), "")
    match = re.match(r"^\[agent-collab/v0\]\s+([A-Z]+)", first)
    body_lines = [ln for ln in text.splitlines()[1:] if ln.strip()]
    if match and body_lines and all(
        ln.strip().lower().startswith(("x-", "from:", "to:", "work:")) for ln in body_lines
    ):
        errors.append("message body is empty (only extension or envelope lines)")
    if match and match.group(1) in {"OWE", "RECONCILE"}:
        for name in ("Owed by", "Owed to"):
            if not _field(name, text):
                errors.append(f"{match.group(1)} message body must include '{name}: <participant>'")
    return errors


def main() -> int:
    path = sys.argv[1] if len(sys.argv) > 1 else "-"
    text = sys.stdin.read() if path == "-" else Path(path).read_text(encoding="utf-8")
    errors = validate(text)
    for error in errors:
        print(f"error: {error}", file=sys.stderr)
    if not errors:
        print("valid agent-collab message (simonbot extension)")
    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
