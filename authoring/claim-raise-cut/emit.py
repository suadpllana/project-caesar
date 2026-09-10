"""Write the cheat scripts.

Each wrong-reading cheat is a whole submission - the reference with one decision taken the other
way - so a score of 0 is attributable to that decision and not to four other things being wrong
at once. Module docstrings are stripped on the way out: a cheat script is a probe, not a place
to restate the solution. Run this after every make_readings.py, never before, or the scripts
carry a reading that has since been repaired.
"""

import ast
import stat
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
TASK = HERE.parent.parent / "tasks" / "claim-raise-cut"
CHEATS = TASK / "cheat"
PARTS = ("mark.py", "item.py", "wait.py", "cyc.py", "txn.py")

WHY = {
    "join-rank": "ranks the five marks and takes the higher one instead of their join",
    "raise-ask-mark": "grants a raise in the mark it asked for rather than the join",
    "self-count": "tests a raise against the asking transaction's own claims as well",
    "raise-ask-order": "serves raises in request order rather than in the order they came to hold",
    "pin-none": "lets first-time claims through while a raise is outstanding",
    "pin-bar": "stops later raises too when one has been passed over",
    "queue-skip": "walks past a first-time claim it cannot grant instead of stopping",
    "edge-conflict": "waits for the holders whose marks exclude the request, the textbook edge",
    "edge-and": "waits for every conflicting holder and everything queued ahead as well",
    "cut-young": "cuts the largest-numbered transaction on the ring",
    "cut-early": "breaks a tie on the earlier request rather than the later one",
    "cut-most": "cuts the transaction holding claims on the most items",
    "cut-one-ring": "cuts out of the first ring it finds instead of comparing across all of them",
    "cut-once": "cuts once and stops looking, leaving a second ring standing",
    "cut-no-cancel": "leaves the victim's request in the queue after cutting it",
    "cut-no-wake": "never sweeps the item the victim was waiting on",
    "drop-all": "gives back every claim on the item instead of the last one",
    "shed-name": "sweeps a leaving transaction's items in name order",
    "resume-now": "runs a granted transaction's backlog on the spot instead of in grant order",
    "settle-block": "looks for a ring only when a claim blocks",
    "per-participant": "right, and answers the removal question one participant at a time",
    "all-live": "right, and takes every live transaction as a candidate for removal",
    "whole-rebuild": "right, and rebuilds the whole relation after every step",
    "candidate-verify": "right, and tries every holder whose mark excludes what a request asked for",
}


def bare(text):
    """The module with its docstrings removed."""
    tree = ast.parse(text)
    drop = []
    for node in ast.walk(tree):
        if isinstance(node, (ast.Module, ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            body = node.body
            if body and isinstance(body[0], ast.Expr) and isinstance(body[0].value, ast.Constant) \
                    and isinstance(body[0].value.value, str):
                drop.append((body[0].lineno, body[0].end_lineno))
    lines = text.splitlines()
    keep = []
    for i, line in enumerate(lines, 1):
        if any(a <= i <= b for a, b in drop):
            continue
        keep.append(line)
    while keep and not keep[0].strip():
        keep.pop(0)
    return "\n".join(keep).rstrip() + "\n"


def script(name, why, where):
    body = ["#!/bin/bash", "# %s" % why, "set -euo pipefail", ""]
    for part in PARTS:
        body.append("cat > /app/hold/%s <<'PYEOF'" % part)
        body.append(bare((where / part).read_text(encoding="utf-8")).rstrip())
        body.append("PYEOF")
        body.append("")
    out = CHEATS / ("cheat-%s.sh" % name)
    out.write_text("\n".join(body), encoding="utf-8", newline="\n")
    out.chmod(out.stat().st_mode | stat.S_IEXEC)
    return out


def main():
    CHEATS.mkdir(exist_ok=True)
    for old in CHEATS.glob("cheat-*.sh"):
        if old.name[6:-3] in WHY:
            old.unlink()
    made = 0
    for where in sorted((HERE / "readings").iterdir()) + sorted((HERE / "naive").iterdir()):
        if not where.is_dir():
            continue
        name = where.name
        if name == "global-cycle":
            continue          # measured inside the limit; it is a correct variant, not a cheat
        if name not in WHY:
            raise SystemExit("no line explaining reading %r" % name)
        script(name, WHY[name], where)
        made += 1
    print("wrote %d reading cheats" % made)
    return 0


if __name__ == "__main__":
    sys.exit(main())
