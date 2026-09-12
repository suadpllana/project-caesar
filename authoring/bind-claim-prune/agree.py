"""Reference against sealed model, over as many generated programs as asked for.

    python authoring/bind-claim-prune/agree.py <seeds> [<per>] [--big]

Runs both engines on every program of every small family for each seed and reports the first
disagreement. The two were written apart; agreement over a large sample is what says the
contract is one thing and not two.
"""
import pathlib
import shutil
import sys

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

import lab  # noqa: E402

TASK = lab.TASK
APP = lab.tree("ref")
sys.path.insert(0, str(APP))
sys.path.insert(0, str(TASK / "tests"))
sys.path.insert(0, str(TASK / "tests" / "seal"))

import ops  # noqa: E402
from bind import book  # noqa: E402
import gen  # noqa: E402
import model  # noqa: E402


def ref(lines):
    job = book.Job()
    for line in lines:
        w = line.split()
        if w:
            ops.ex(job, tuple(w))
    return job.out


def main():
    seeds = int(sys.argv[1]) if len(sys.argv) > 1 else 3
    per = int(sys.argv[2]) if len(sys.argv) > 2 else 20
    big = "--big" in sys.argv
    n = 0
    bad = 0
    tally = {}
    for s in range(seeds):
        for fam, name, lines in gen.programs("agree-%d" % s, per):
            if not big and fam in ("wide", "deep"):
                continue
            a = ref(lines)
            b = model.expect(lines)
            n += 1
            tally[fam] = tally.get(fam, 0) + 1
            if a != b:
                bad += 1
                if bad == 1:
                    print("DISAGREE %s %s seed %d" % (fam, name, s))
                    for i in range(max(len(a), len(b))):
                        x = a[i] if i < len(a) else "-"
                        y = b[i] if i < len(b) else "-"
                        if x != y:
                            print("   ref %-40s model %s" % (x, y))
                    pathlib.Path("/tmp/disagree.txt").write_text("\n".join(lines) + "\n")
                    print("   program written to /tmp/disagree.txt")
    print("%d programs, %d disagreements" % (n, bad))
    print("   " + "  ".join("%s=%d" % (k, v) for k, v in sorted(tally.items())))
    shutil.rmtree(APP.parent, ignore_errors=True)
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
