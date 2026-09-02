"""Which part of the record each cheat gets wrong, and on how many registers.

Two things come out of this. A graded field that separates no cheat is dead weight: it
cannot catch a wrong answer and it can fail a right one. And a cheat that differs from the
reference on a handful of registers out of hundreds is a lottery ticket rather than a test
of expertise, which under all-or-nothing grading is how a well-designed task scores 0 of 8.

Usage:
    python3 authoring/field_report.py [rounds]
"""

from __future__ import annotations

import re
import sys
import tempfile
from pathlib import Path

TASK = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(TASK / "tests"))
sys.path.insert(0, str(TASK / "authoring"))

import cases  # noqa: E402
import gen  # noqa: E402
import harness  # noqa: E402

PART = ("company", "on the list", "seats taken", "seats", "who took each seat")

# The company is the row key the frozen driver hands the record writer, one row per
# company in incorporation order. No implementation, right or wrong, can move it without
# returning something that is not a record at all, so it is not dead weight when no cheat
# shifts it: it is the identity the rest of the row hangs on and what makes a failure
# message name a company instead of a position.
DRIVER_SUPPLIED = ("company",)
BLOCK = re.compile(r"cat > /app/pol/(\S+) <<'SRSEOF'\n(.*?)\nSRSEOF", re.S)


def policy_of(sh):
    d = Path(tempfile.mkdtemp(prefix="fr-"))
    for m in BLOCK.finditer(sh.read_text(encoding="utf-8")):
        (d / m.group(1)).write_text(m.group(2) + "\n", encoding="utf-8", newline="\n")
    return d


def main(argv):
    rounds = int(argv[1]) if len(argv) > 1 else 300
    texts = [t for _, t in cases.CASES] + [t for _, t in gen.batch("fields", rounds)]
    ref = harness.drive_text(harness.stage(harness.REF), texts)

    seen = {p: 0 for p in PART}
    for sh in sorted((TASK / "cheat").glob("cheat-*.sh")):
        try:
            got = harness.drive_text(harness.stage(policy_of(sh)), texts)
        except RuntimeError as exc:
            print("%-38s did not run: %s" % (sh.name, str(exc).splitlines()[-1][:70]))
            continue
        hits = {p: 0 for p in PART}
        regs = 0
        for a, b in zip(ref, got):
            if a == b:
                continue
            regs += 1
            for ra, rb in zip(a, b):
                for i, part in enumerate(PART):
                    if ra[i] != rb[i]:
                        hits[part] += 1
        for p in PART:
            seen[p] += hits[p]
        which = ", ".join(p for p in PART if hits[p])
        print("%-38s %4d of %d registers   %s"
              % (sh.name, regs, len(texts), which or "identical to the reference"))

    print()
    dead = [p for p in PART if not seen[p] and p not in DRIVER_SUPPLIED]
    if dead:
        print("   graded parts no cheat moves: %s" % ", ".join(dead))
    else:
        print("   every graded part of the record separates at least one cheat")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
