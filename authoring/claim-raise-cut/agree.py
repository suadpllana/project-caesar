"""Reference against the sealed model over the generated population."""

import sys
from collections import Counter
from pathlib import Path

HERE = Path(__file__).resolve().parent
TASK = HERE.parent.parent / "tasks" / "claim-raise-cut"
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(TASK / "tests"))
sys.path.insert(0, str(TASK / "tests" / "seal"))

import gen  # noqa: E402
import lab  # noqa: E402
import model  # noqa: E402


def main():
    seed = int(sys.argv[1]) if len(sys.argv) > 1 else 1
    per = int(sys.argv[2]) if len(sys.argv) > 2 else 20
    heavy = int(sys.argv[3]) if len(sys.argv) > 3 else 2
    go = lab.runner(TASK / "solution", "ref")
    bad = 0
    stat = Counter()
    for name, steps in gen.programs(seed, per, heavy):
        fam = name.rsplit("-", 1)[0]
        got = go(steps)
        want = model.trace(steps)
        stat[fam + ".n"] += 1
        stat[fam + ".lines"] += len(want)
        stat[fam + ".cut"] += sum(1 for line in want if line.startswith("cut"))
        stat[fam + ".wait"] += sum(1 for line in want if line.startswith("wait"))
        if got != want:
            bad += 1
            if bad <= 3:
                print("MISMATCH %s" % name, flush=True)
                for i, (a, b) in enumerate(zip(got + [""] * 9, want + [""] * 9)):
                    if a != b:
                        print("  line %d: ref %r  model %r" % (i, a, b))
                        print("  program:", " | ".join(" ".join(s) for s in steps[:40]))
                        break
    fams = sorted({k.split(".")[0] for k in stat})
    print("%-9s %4s %8s %6s %6s" % ("family", "n", "lines", "cut", "wait"))
    for f in fams:
        print("%-9s %4d %8d %6d %6d"
              % (f, stat[f + ".n"], stat[f + ".lines"], stat[f + ".cut"], stat[f + ".wait"]))
    print("mismatches:", bad)
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
