"""How much of the graded set each wrong reading moves, and whether the
enumerated set separates it."""

import os
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(ROOT, "tests"))

import build_tree
import cases
import gen
import harness
import readings


def main():
    count = int(sys.argv[1]) if len(sys.argv) > 1 else 400
    streams = gen.batch(31337, count)
    fixed = [cases.SETS[k] for k in sorted(cases.SETS)]
    base_g = harness.drive(streams, os.path.join(ROOT, "solution"))
    base_f = harness.drive(fixed, os.path.join(ROOT, "solution"))
    print("%-22s %8s  %s" % ("reading", "gen", "separated by"))
    weak = 0
    for name in sorted(readings.READINGS):
        tmp = tempfile.mkdtemp(prefix="rd-")
        build_tree.build(tmp, readings.READINGS[name])
        g = harness.drive(streams, tmp)
        f = harness.drive(fixed, tmp)
        moved = sum(1 for p in streams if g.get(p["name"]) != base_g.get(p["name"]))
        sep = [p["name"] for p in fixed if f.get(p["name"]) != base_f.get(p["name"])]
        share = 100.0 * moved / max(1, len(streams))
        flag = "" if share >= 10.0 else "   (rare, but separated)"
        if not sep:
            weak += 1
            flag = "   <-- NOT SEPARATED"
        print("%-22s %6.1f%%  %s%s"
              % (name, share, ", ".join(sep[:3]) if sep else "NOTHING", flag))
    print("%d reading(s) not separated by the enumerated set" % weak)
    return 1 if weak else 0


if __name__ == "__main__":
    sys.exit(main())
