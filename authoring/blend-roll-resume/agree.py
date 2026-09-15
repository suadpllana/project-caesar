"""Cross-check the reference against the brute-force engine on generated scripts.

Usage: agree.py [seed] [per]        the big family is left out, the naive cannot finish it.
"""
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(ROOT / "tasks" / "blend-roll-resume" / "tests"))

import gen  # noqa: E402
import lab  # noqa: E402
import naive  # noqa: E402

REF = ROOT / "tasks" / "blend-roll-resume" / "solution"


def main():
    seed = sys.argv[1] if len(sys.argv) > 1 else "cross"
    per = int(sys.argv[2]) if len(sys.argv) > 2 else 30
    work = [(f, n, l) for f, n, l in gen.programs(seed, per) if f != "big"]
    print("checking %d scripts" % len(work), flush=True)
    bad = 0
    for fam, name, lines in work:
        want = naive.expect(lines)
        got = lab.inproc(lines, REF)
        if got != want:
            bad += 1
            if bad <= 3:
                print("MISMATCH", fam, name)
                print("\n".join("   " + x for x in lines))
                for i in range(max(len(got), len(want))):
                    a = got[i] if i < len(got) else "-"
                    b = want[i] if i < len(want) else "-"
                    print(("   ok " if a == b else "   XX "), a, "|", b)
    print("mismatches:", bad, "of", len(work))
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
