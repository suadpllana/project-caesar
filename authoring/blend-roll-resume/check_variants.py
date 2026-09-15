"""Run every correct variant against the sealed model on the whole generated space."""
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
TASK = HERE.parents[1] / "tasks" / "blend-roll-resume"
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(TASK / "tests"))
sys.path.insert(0, str(TASK / "tests" / "seal"))

import cases  # noqa: E402
import gen  # noqa: E402
import lab  # noqa: E402
import model  # noqa: E402


def main():
    per = int(sys.argv[1]) if len(sys.argv) > 1 else 45
    work = [("hand", n, cases.ops(n)) for n in cases.ORDER] + gen.programs("variants", per)
    dirs = sorted(d for d in (HERE / "variants").iterdir() if d.is_dir())
    dirs.append(TASK / "solution")
    bad = 0
    for d in dirs:
        t = time.perf_counter()
        wrong = []
        for _fam, name, lines in work:
            if lab.inproc(lines, d) != model.expect(lines):
                wrong.append(name)
        print("%-12s %4d scripts, %3d wrong, %.2fs" % (
            d.name, len(work), len(wrong), time.perf_counter() - t))
        if wrong:
            print("   first:", wrong[:4])
            bad += 1
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
