"""Reference, sealed model and brute force, on the same scripts.

Usage: three.py [seed] [per] [--big]
"""
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
TASK = ROOT / "tasks" / "blend-roll-resume"
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(TASK / "tests"))
sys.path.insert(0, str(TASK / "tests" / "seal"))

import gen  # noqa: E402
import lab  # noqa: E402
import model  # noqa: E402
import naive  # noqa: E402

REF = TASK / "solution"


def main():
    seed = sys.argv[1] if len(sys.argv) > 1 else "three"
    per = int(sys.argv[2]) if len(sys.argv) > 2 else 20
    big = "--big" in sys.argv
    work = gen.programs(seed, per)
    if not big:
        work = [w for w in work if w[0] != "big"]
    print("checking %d scripts (big=%s)" % (len(work), big), flush=True)
    bad = 0
    t0 = time.perf_counter()
    for fam, name, lines in work:
        want = model.expect(lines)
        got = lab.inproc(lines, REF)
        rows = [("model", want), ("ref", got)]
        if fam != "big":
            rows.append(("naive", naive.expect(lines)))
        base = rows[0][1]
        for tag, row in rows[1:]:
            if row != base:
                bad += 1
                if bad <= 3:
                    print("MISMATCH", fam, name, tag)
                    print("\n".join("   " + x for x in lines))
                    for i in range(max(len(row), len(base))):
                        a = row[i] if i < len(row) else "-"
                        b = base[i] if i < len(base) else "-"
                        print(("   ok " if a == b else "   XX "), a, "|", b)
                break
    print("mismatches: %d of %d in %.1fs" % (bad, len(work), time.perf_counter() - t0))
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
