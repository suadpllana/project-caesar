"""Every alternative correct implementation must reach the same rows and the same sheet.

A variant is the reference with one decision written differently. If one of them disagrees,
either the reference is grading an arrangement of the code instead of a behaviour, which is
the run-audit rejection, or a sentence of the brief was never decided and the variant has
just found it.

    python3 authoring/variant_check.py [generated-count]
"""
import shutil
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
TASK = HERE.parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(TASK / "tests"))

import gen  # noqa: E402
import harness  # noqa: E402
import oracle  # noqa: E402
import scen  # noqa: E402


def _shape(r):
    return (r["err"], oracle.rounds([list(x) for x in r["log"]]), r["sheet"])


def main(argv):
    count = int(argv[1]) if len(argv) > 1 else 150
    streams = list(scen.STREAMS) + gen.batch("va21an75", count)
    ref = harness.stage(None, TASK / "solution")
    want = harness.drive(ref, streams)
    shutil.rmtree(ref, ignore_errors=True)
    bad = 0
    for d in sorted((HERE / "variants").iterdir()):
        if not d.is_dir() or not d.name.startswith("ok-"):
            continue
        t = harness.stage(None, d)
        got = harness.drive(t, streams)
        shutil.rmtree(t, ignore_errors=True)
        off = [n for n, _ in streams if _shape(got[n]) != _shape(want[n])]
        print("%-24s %s" % (d.name, "agrees on all %d" % len(streams) if not off
                            else "DISAGREES on %d, first %s" % (len(off), off[0])))
        bad += bool(off)
    print("%d variants disagree with the reference" % bad)
    return 0 if bad == 0 else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv))
