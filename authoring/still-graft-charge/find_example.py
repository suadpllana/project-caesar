"""Search for the program the brief shows, rather than choosing one.

The worked example has to do two jobs at once and the second is the one an author gets wrong:
it must show the shipped ledger is wrong, by naming one line of one trace that should read
differently, and it must decide none of the wrong readings in `readings.py`. An example whose
correct output separates a reading is an oracle for that rule, published in the brief.

    python3 -u find_example.py [rounds]
"""
import random
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent.parent
TASK = ROOT / "tasks" / "still-graft-charge"
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(TASK / "tests"))

import readings  # noqa: E402

SHIP = TASK / "environment" / "app_src" / "led"
REF = Path(readings.REFERENCE)


def candidate(seed):
    r = random.Random(seed)
    out = ["line p"]
    lines = ["p"]
    stills = []
    cells = r.choice((2, 3, 4))
    for _ in range(r.randint(4, 9)):
        pick = r.random()
        if pick < 0.30:
            lo = r.randrange(cells)
            out.append("put %s %d %d %d" % (r.choice(lines), lo,
                                            min(cells - 1, lo + r.randrange(2)),
                                            r.randrange(2, 9)))
        elif pick < 0.42:
            lo = r.randrange(cells)
            out.append("cut %s %d %d" % (r.choice(lines), lo, min(cells - 1, lo + 1)))
        elif pick < 0.58:
            name = "n%d" % (len(stills) + 1)
            stills.append(name)
            out.append("still %s %s" % (r.choice(lines), name))
        elif pick < 0.70 and stills:
            name = "q%d" % len(lines)
            lines.append(name)
            out.append("graft %s %s" % (r.choice(stills), name))
        elif pick < 0.76 and stills:
            out.append("drop %s" % r.choice(stills))
        elif pick < 0.82:
            out.append("lift %s" % r.choice(lines))
        elif pick < 0.90:
            out.append("ask %s" % r.choice(lines))
        else:
            out.append("at %s %d" % (r.choice(lines), r.randrange(cells)))
    out.append("ask %s" % r.choice(lines))
    return out


def main():
    rounds = int(sys.argv[1]) if len(sys.argv) > 1 else 4000
    alts = {name: readings.policy(files) for name, files in readings.READINGS.items()} \
        if hasattr(readings, "policy") else None
    if alts is None:
        import importlib.util
        spec = importlib.util.spec_from_file_location(
            "rc", ROOT / "tools" / "readingcheck.py")
        rc = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(rc)
        alts = {name: rc.policy_dir(readings, files)
                for name, files in readings.READINGS.items()}

    best = None
    kinds = None
    for i in range(rounds):
        lines = candidate("ex/%d" % i)
        text = "\n".join(lines)
        try:
            want = readings.run(REF, text)
            ship = readings.run(SHIP, text)
        except Exception:
            continue
        if len(want) != len(ship) or len(want) < 2:
            continue
        off = [j for j in range(len(want)) if want[j] != ship[j]]
        if len(off) != 1:
            continue
        decides = sorted(name for name, alt in alts.items()
                         if readings.run(alt, text) != want)
        seen = len({one.split()[0] for one in lines})
        score = (-len(decides), seen, -len(lines))
        if best is None or score > kinds:
            best, kinds = lines, score
            print("== %d ops, %d op kinds, differs at output line %d, decides %d readings: %s"
                  % (len(lines), seen, off[0] + 1, len(decides), ", ".join(decides)))
            print("\n".join(lines))
            print("want:", want)
            print("ship:", ship)
            print()
    if best is None:
        print("nothing found in %d candidates" % rounds)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
