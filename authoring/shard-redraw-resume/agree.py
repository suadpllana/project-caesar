"""Do the reference and the sealed model settle every program the same way?

The two were written apart and on purpose do not share a shape. Agreement over a shaped
population is what makes the sealed model evidence about the contract rather than a second copy
of one implementation's habits.

    python3 authoring/shard-redraw-resume/agree.py [per] [--fam name]
"""
import os
import pathlib
import subprocess
import sys
import tempfile
import time

ROOT = pathlib.Path(__file__).resolve().parent.parent.parent
TASK = ROOT / "tasks" / "shard-redraw-resume"
sys.path.insert(0, str(TASK / "tests"))
os.environ["SRR_PRISTINE"] = str(TASK / "tests" / "pristine")
sys.path.insert(0, str(TASK / "tests" / "seal"))

import gen  # noqa: E402
import model  # noqa: E402
sys.path.insert(0, str(ROOT / "authoring" / "shard-redraw-resume"))
import lab  # noqa: E402


def main():
    per = int(sys.argv[1]) if len(sys.argv) > 1 and sys.argv[1].isdigit() else 6
    want = None
    if "--fam" in sys.argv:
        want = sys.argv[sys.argv.index("--fam") + 1]
    here = lab.tree(TASK / "solution")
    room = pathlib.Path(tempfile.mkdtemp(prefix="srr-agree-"))
    bad = 0
    seen = 0
    for fam, name, lines in gen.programs("agree-nonce", per):
        if want and fam != want:
            continue
        path = room / (name + ".txt")
        path.write_text("\n".join(lines) + "\n", newline="\n")
        t = time.time()
        got = lab.run(here, path)
        cost = time.time() - t
        wish = model.expect(lines)
        seen += 1
        if got != wish:
            bad += 1
            first = next((i for i, (a, b) in enumerate(zip(got, wish)) if a != b),
                         min(len(got), len(wish)))
            print("DIFF %s at line %d\n  ref   %s\n  model %s"
                  % (name, first, got[first:first + 2], wish[first:first + 2]))
            if bad > 3:
                break
        elif cost > 1.0:
            print("slow %-12s %6.2fs  %d lines" % (name, cost, len(got)))
    print("%d programs, %d disagreements" % (seen, bad))
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
