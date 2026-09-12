"""Differential: the reference against the sealed model, over generated programs.

Where they disagree the contract is ambiguous, and the contract is what gets fixed.
"""
import random
import sys
import pathlib

HERE = pathlib.Path(__file__).resolve().parent
ROOT = HERE.parent.parent
TASK = ROOT / "tasks" / "claim-line-stall"

sys.path.insert(0, str(TASK / "tests" / "seal"))
import model  # noqa: E402

import lab  # noqa: E402


def load(over):
    here = lab.stage(over)
    sys.path.insert(0, str(here))
    for name in ("ops", "hold", "hold.name", "hold.say", "hold.book",
                 "hold.line", "hold.lift", "hold.knot", "hold.turn", "hold.act"):
        sys.modules.pop(name, None)
    import ops as mod
    from hold import book as bk
    return mod, bk


def run(mod, bk, lines):
    h = bk.Hold()
    for line in lines:
        mod.ex(h, tuple(line.split()))
    return h.out


def draw(rng, jobs, units, cells, n, heat=0.5):
    out = []
    for _ in range(n):
        pick = rng.random()
        job = "j%d" % rng.randrange(1, jobs + 1)
        unit = "u%d" % rng.randrange(1, units + 1)
        if pick < heat:
            scope = unit if rng.random() < 0.2 else "%s/c%d" % (unit, rng.randrange(1, cells + 1))
            out.append("take %s %s %s" % (job, scope, "w" if rng.random() < 0.45 else "r"))
        elif pick < heat + 0.2:
            scope = unit if rng.random() < 0.2 else "%s/c%d" % (unit, rng.randrange(1, cells + 1))
            out.append("drop %s %s" % (job, scope))
        elif pick < heat + 0.32:
            out.append("end %s" % job)
        else:
            out.append("show %s" % unit)
    return out


def main():
    rounds = int(sys.argv[1]) if len(sys.argv) > 1 else 500
    mod, bk = load(str(TASK / "solution"))
    rng = random.Random(20260912)
    bad = 0
    for i in range(rounds):
        jobs = rng.choice([2, 3, 4, 5, 6])
        units = rng.choice([1, 1, 2, 3])
        cells = rng.choice([2, 3, 4, 6])
        n = rng.choice([12, 20, 30, 45])
        lines = draw(rng, jobs, units, cells, n, heat=rng.choice([0.4, 0.55, 0.7]))
        a = run(mod, bk, lines)
        b = model.expect(lines)
        if a != b:
            bad += 1
            if bad <= 3:
                print("=== disagree %d" % i)
                print("\n".join(lines))
                for x, y in zip(a + [""] * len(b), b + [""] * len(a)):
                    print("%-46s %s" % (x, y), "  <<<" if x != y else "")
                print("ref %d lines, model %d lines" % (len(a), len(b)))
    print("%d of %d disagreed" % (bad, rounds))
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
