"""Every alternative correct implementation must reach the same determination.

The cheat suite is a claim about wrong answers. This is the mirror image and it is the one
the run audit applies: a graded quantity that two correct implementations disagree on is
not a hard test, it is a coin flip on an implementation choice.

The variant that matters most here is ok-latekey, which is the reference with the combined
hand named so that it sorts after every party id rather than before one. It disagreed with
the reference the first time it ran, on registers where a seat came down to a tied average,
which is how the tie-free requirement in tests/gen.py came to exist.

This runs on the host and does not exercise the container. Use
tools/docker_trial2.py <slug> --variants for the version that grades them for real.
"""

from __future__ import annotations

import sys
from pathlib import Path

TASK = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(TASK / "tests"))
sys.path.insert(0, str(TASK / "authoring"))

import cases  # noqa: E402
import gen  # noqa: E402
import harness  # noqa: E402
import oracle  # noqa: E402


def main(argv):
    rounds = int(argv[1]) if len(argv) > 1 else 600
    texts = [t for _, t in cases.CASES] + [t for _, t in gen.batch("variants", rounds)]
    texts += [p.read_text(encoding="utf-8")
              for p in sorted((harness.SRC / "regs").glob("*.txt"))]
    want = [oracle.determine(t) for t in texts]

    ref = harness.drive_text(harness.stage(harness.REF), texts)
    bad = sum(1 for a, b in zip(ref, want) if a != b)
    print("%-16s %s (%d registers)" % ("reference", "agrees" if not bad else "DISAGREES",
                                       len(texts)))
    worst = bad
    for d in sorted((TASK / "authoring" / "variants").iterdir()):
        if not (d.is_dir() and d.name.startswith("ok-")):
            continue
        got = harness.drive_text(harness.stage(d), texts)
        off = [i for i, (a, b) in enumerate(zip(got, want)) if a != b]
        worst = max(worst, len(off))
        print("%-16s %s" % (d.name, "agrees" if not off
                            else "DISAGREES on %d, first:\n%s" % (len(off), texts[off[0]])))
    return 1 if worst else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
