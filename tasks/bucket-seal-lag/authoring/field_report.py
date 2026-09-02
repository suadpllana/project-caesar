"""Which graded row kind separates each cheat, and how many plans each one moves.

A row kind that separates no cheat is pure liability: it cannot catch a wrong
answer and it can fail a right one. And a reading that moves a handful of plans in
a few hundred is a lottery ticket rather than a test of expertise, so every one of
them gets a number here before it is believed.
"""

import glob
import os
import pathlib
import shutil
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "authoring"))
sys.path.insert(0, str(ROOT / "tests"))

import cases
import gen
import harness
import oracle
import readings


def main(argv):
    n = int(argv[1]) if len(argv) > 1 else 200
    plans = [(nm, cases.PLANS[nm]) for nm in sorted(cases.PLANS)]
    plans += [(nm, gen.text(p)) for nm, p in gen.batch("fields", n)]
    want = dict((nm, oracle.play(t)) for nm, t in plans)
    kinds = {}
    for res in want.values():
        for r in res["tr"]:
            kinds[r[0]] = kinds.get(r[0], 0) + 1
    print("row kinds in the truth: %s"
          % ", ".join("%s %d" % (k, kinds[k]) for k in sorted(kinds)))

    seen = dict((k, 0) for k in kinds)
    print("%-22s %5s %6s   %s" % ("reading", "moved", "pct", "first row kind that differs"))
    for name in sorted(readings.READINGS):
        files = readings.READINGS[name]
        d = pathlib.Path(harness.tree(str(ROOT / "solution")))
        try:
            for fn, body in files.items():
                with open(d / "flow" / fn, "w", newline="\n") as fh:
                    fh.write(body)
            moved, first = 0, None
            for nm, text in plans:
                try:
                    got = harness.drive(d, text)
                except Exception:
                    moved += 1
                    if first is None:
                        first = "fault"
                    continue
                if got["tr"] != want[nm]["tr"] or got["sk"] != want[nm]["sk"]:
                    moved += 1
                    if first is None:
                        for a, b in zip(got["tr"], want[nm]["tr"]):
                            if a != b:
                                first = "%s/%s" % (a[0], b[0])
                                seen[b[0]] = seen.get(b[0], 0) + 1
                                break
                        else:
                            first = "length"
        finally:
            shutil.rmtree(d.parent, ignore_errors=True)
        flag = "   <== lottery ticket" if 0 < moved < len(plans) * 0.03 else ""
        print("%-22s %5d %5.1f%%   %s%s"
              % (name, moved, 100.0 * moved / len(plans), first, flag))
    dead = [k for k in sorted(kinds) if not seen.get(k)]
    print("row kinds that separate nothing: %s" % (", ".join(dead) or "none"))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
