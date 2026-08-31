#!/usr/bin/env python3
"""Check solution/solve.sh for inlined source that belongs in a file of its own.

guard-mark-unwind failed the quality review on 2026-08-31 for exactly this, with every
other gate green and the reference genuinely scoring 1. The reviewer's finding:

    solve.sh inlines them as three heredocs of 42, 48 and 48 lines (139 of the file's 149
    lines), well past the ~20-line threshold for keeping files separate. Byte-identical
    copies of all three already exist as solution/ref/pick.py, stop.py and knot.py, which
    solve.sh does not use, so the reference is duplicated in two places and can silently
    drift.

Two separate defects there, and this checks both. A heredoc past the threshold is the
style half. The duplication is the real half: the same source existing twice in one
bundle, with nothing keeping the copies equal.

The fix is the shape typeahead-query-controller shipped, which is the only solve.sh in
this repo to have cleared the quality review: the reference sits beside solve.sh, and
solve.sh resolves its own directory and copies it in. The platform hands the oracle agent
the whole solution/ directory, so files next to solve.sh are readable at run time.

Usage:
    python tools/solvecheck.py <slug>          one task
    python tools/solvecheck.py --all           every task in tasks/

Exit code 0 if clean, 1 on any finding.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent

# The reviewer's own number. Past this many lines, inlined content is a file.
MAX_INLINE = 20

# A heredoc opener: `cat > x <<'EOF'`, `<<EOF`, `<<-"EOF"`.
HEREDOC = re.compile(r"<<-?\s*(['\"]?)([A-Za-z_][A-Za-z0-9_]*)\1")


def heredocs(text: str) -> list[tuple[str, int, list[str]]]:
    """Return (delimiter, opening line number, body lines) for each heredoc."""
    lines = text.splitlines()
    out: list[tuple[str, int, list[str]]] = []
    i = 0
    while i < len(lines):
        m = HEREDOC.search(lines[i])
        if not m:
            i += 1
            continue
        delim = m.group(2)
        start = i
        body: list[str] = []
        i += 1
        while i < len(lines) and lines[i].strip() != delim:
            body.append(lines[i])
            i += 1
        out.append((delim, start + 1, body))
        i += 1
    return out


def norm(text: str) -> str:
    """Compare on content, ignoring trailing whitespace and blank edges."""
    return "\n".join(ln.rstrip() for ln in text.strip().splitlines())


def shipped_files(task: Path) -> dict[str, list[Path]]:
    """Every text file in the bundle, keyed by normalised content.

    authoring/variants/ is excluded on purpose. An alternative correct implementation is
    the reference with one decision made differently, so its other files are byte-identical
    to the reference by construction. Reporting those every run would be noise on a real
    finding, and the next session would learn to skip the whole check.
    """
    out: dict[str, list[Path]] = {}
    skip = {".git", "__pycache__", ".pytest_cache", "variants"}
    for p in sorted(task.rglob("*")):
        if not p.is_file() or any(part in skip for part in p.parts):
            continue
        if p.suffix not in {".py", ".ts", ".js", ".txt", ".json", ".sh"}:
            continue
        try:
            body = norm(p.read_text())
        except (UnicodeDecodeError, OSError):
            continue
        if body:
            out.setdefault(body, []).append(p)
    return out


def check(task: Path) -> list[str]:
    solve = task / "solution" / "solve.sh"
    if not solve.is_file():
        return ["solution/solve.sh is missing"]

    text = solve.read_text()
    found: list[str] = []
    docs = heredocs(text)
    by_content = shipped_files(task)

    for delim, line, body in docs:
        n = len(body)
        if n > MAX_INLINE:
            found.append(
                "solve.sh:%d: heredoc <<%s inlines %d lines (limit %d) - keep it as a "
                "file beside solve.sh and copy it in" % (line, delim, n, MAX_INLINE)
            )
        twins = by_content.get(norm("\n".join(body)), [])
        twins = [t for t in twins if t != solve]
        if twins:
            where = ", ".join(str(t.relative_to(task)) for t in twins)
            found.append(
                "solve.sh:%d: heredoc <<%s duplicates %s - one of the two copies will "
                "drift" % (line, delim, where)
            )

    inlined = sum(len(b) for _, _, b in docs)
    total = len(text.splitlines())
    if total and inlined > total / 2 and inlined > MAX_INLINE:
        found.append(
            "solve.sh is %d lines of which %d are inlined heredoc bodies - the script is "
            "mostly transcribed source" % (total, inlined)
        )
    return found


def main(argv: list[str]) -> int:
    if len(argv) < 2:
        print(__doc__)
        return 2
    if argv[1] == "--all":
        tasks = sorted(p for p in (REPO / "tasks").iterdir() if p.is_dir())
    else:
        tasks = [REPO / "tasks" / argv[1]]

    bad = 0
    for task in tasks:
        if not task.is_dir():
            print("no such task: %s" % task)
            return 2
        found = check(task)
        if found:
            bad += 1
            print("%s:" % task.name)
            for f in found:
                print("  %s" % f)
        else:
            print("%s: clean" % task.name)
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
