"""What each graded field is worth, and how rare each cheat's disagreement is.

A field that separates no cheat cannot catch a wrong answer and can still fail a right one,
so it is pure liability. And a cheat that differs from the reference on one stream in four
hundred is a lottery ticket rather than a test of expertise: under all-or-nothing grading it
is indistinguishable from bad luck, and it wants finding at contract time.

    python3 authoring/field_report.py [generated-count]
"""
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
TASK = HERE.parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(TASK / "tests"))

import gen  # noqa: E402
import harness  # noqa: E402
import scen  # noqa: E402


def split(a, b):
    rows = a["log"] != b["log"]
    sheet = a["sheet"] != b["sheet"]
    return rows, sheet


def main(argv):
    count = int(argv[1]) if len(argv) > 1 else 200
    streams = list(scen.STREAMS) + gen.batch("f1e1d5", count)
    ref = harness.stage(None, TASK / "solution")
    want = harness.drive(ref, streams)
    shutil.rmtree(ref, ignore_errors=True)

    print("%-30s %8s %8s %8s" % ("cheat", "streams", "rows", "sheet"))
    for s in sorted((TASK / "cheat").glob("cheat-*.sh")):
        t = harness.stage(None, None)
        r = subprocess.run(["/bin/bash", str(s)],
                           env={"APP": str(Path(t) / "app"), "APPDIR": str(Path(t) / "app"),
                                "PATH": "/usr/bin:/bin"}, capture_output=True, text=True)
        if r.returncode != 0:
            print("%-30s could not be applied" % s.stem)
            shutil.rmtree(t, ignore_errors=True)
            continue
        got = harness.drive(t, streams)
        shutil.rmtree(t, ignore_errors=True)
        nrow = nsheet = nany = 0
        for n, _ in streams:
            a, b = got[n], want[n]
            if a["err"]:
                nany += 1
                nrow += 1
                continue
            x, y = split(a, b)
            nrow += x
            nsheet += y
            nany += x or y
        print("%-30s %8d %8d %8d" % (s.stem.replace("cheat-", ""), nany, nrow, nsheet))
    print("of %d streams; a cheat in single digits is a lottery ticket, not a test" % len(streams))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
