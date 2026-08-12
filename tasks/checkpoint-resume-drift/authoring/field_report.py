#!/usr/bin/env python3
"""Per-variant, which graded field diverges from the ground truth.

A graded field that separates no wrong answer is pure liability: it cannot catch a
mistake and it can still fail a correct solution.  This prints the failure signature of
every script in cheat/ (and of any directory of editable files passed on the command
line), field by field, so the graded set can be checked against what it actually does.

Usage:
    python3 authoring/field_report.py
    python3 authoring/field_report.py authoring/variants/ok-flat
"""

from __future__ import annotations

import json
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

TASK = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(TASK / "authoring"))
sys.path.insert(0, str(TASK / "tests"))

import harness  # noqa: E402
import scen  # noqa: E402

GRADED = ("p", "ema", "step", "reads", "pos", "upd", "trace")
NAMES = [s["name"] for s in scen.SCENARIOS]


def gt():
    return json.loads((TASK / "tests" / "gt.json").read_text())["scenarios"]


def from_script(path: Path, dest: Path) -> None:
    """Replay a cheat script's heredocs into a directory of editable files."""
    text = path.read_text()
    dest.mkdir(parents=True, exist_ok=True)
    for m in re.finditer(r"cat > /app/\S*?/?(\w+\.py) <<'PYEOF'\n(.*?)\nPYEOF", text, re.S):
        (dest / m.group(1)).write_text(m.group(2) + "\n")


def signature(variant: str) -> dict:
    data = harness.run(variant)
    want = gt()
    out = {}
    for name in NAMES:
        rep = (data.get("reports") or {}).get(name)
        if not isinstance(rep, dict):
            out[name] = ["RAISED"]
            continue
        out[name] = [f for f in GRADED if rep.get(f) != want[name]["report"][f]]
    return out


def show(label: str, sig: dict) -> None:
    hit = {f for v in sig.values() for f in v}
    print("%-34s %s" % (label, ("clean" if not hit else " ".join(sorted(hit)))))
    for name in NAMES:
        if sig[name]:
            print("      %-13s %s" % (name, " ".join(sig[name])))


def main(argv: list[str]) -> int:
    if len(argv) > 1:
        for v in argv[1:]:
            show(v, signature(v))
        return 0
    tmp = Path(tempfile.mkdtemp())
    seen = {}
    try:
        for sh in sorted((TASK / "cheat").glob("*.sh")):
            d = tmp / sh.stem
            from_script(sh, d)
            sig = signature(str(d))
            seen[sh.stem] = sig
            show(sh.stem, sig)
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
    used = {f for sig in seen.values() for v in sig.values() for f in v if f != "RAISED"}
    dead = [f for f in GRADED if f not in used]
    print("\nfields that separate nothing: %s" % (", ".join(dead) if dead else "none"))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
