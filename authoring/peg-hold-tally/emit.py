"""Write cheat/cheat-<reading>.sh, one per wrong reading.

The sources come from readings.py, which is the module tools/readingcheck.py measures, so a cheat
can never be emitted from a stale copy of a reading that has since been repaired (CLAUDE.md,
2026-09-09). emit.py and readings.py must agree on the set of readings or this refuses to run.
"""
import pathlib
import sys

import readings as book

HERE = pathlib.Path(__file__).resolve().parent
REF = HERE.parent.parent / "tasks" / "peg-hold-tally" / "solution"
CHEATS = HERE.parent.parent / "tasks" / "peg-hold-tally" / "cheat"
PARTS = book.PARTS

WHY = {
    "hull": "reads a volume's hold on a block as one stretch from first taken to last let go",
    "own-volume": "lets only pegs of the volume that first held a block keep it",
    "first-slot-out": "ends the hold at the first slot that lets go instead of the last",
    "by-id": "gives blocks back in allocation order instead of the order they stopped being kept",
    "at-release": "orders the reclaim list by when the volume let each block go",
    "tally-held": "counts a block for its peg while a volume is still holding it",
    "tally-all": "counts every block a peg keeps instead of the ones it alone keeps",
    "print-again": "prints a block that has already been given back at every later trim",
    "shed-quiet": "takes a shed peg away without releasing what it alone kept",
    "no-volume-key": "counts the hold on a block per block instead of per volume",
}


def one(name):
    lines = ["#!/bin/bash", "# %s" % WHY[name], "set -euo pipefail", ""]
    swap = book.READINGS[name]
    for part in PARTS:
        body = swap.get(part, (REF / part).read_text(encoding="utf-8")).rstrip("\n")
        lines.append("cat > /app/keep/%s <<'PYEOF'" % part)
        lines.append(body)
        lines.append("PYEOF")
        lines.append("")
    return "\n".join(lines)


def main():
    CHEATS.mkdir(exist_ok=True)
    missing = sorted(set(WHY) ^ set(book.READINGS))
    if missing:
        raise SystemExit("emit and readings disagree about which readings exist: %s" % missing)
    for name in sorted(WHY):
        path = CHEATS / ("cheat-%s.sh" % name)
        text = one(name)
        assert "\r" not in text
        path.write_text(text, encoding="utf-8", newline="\n")
        path.chmod(0o755)
    print("wrote %d reading cheats" % len(WHY))
    return 0


if __name__ == "__main__":
    sys.exit(main())
