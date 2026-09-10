"""Judge one staged tree in a process of its own.

The probes fork and call os._exit, so the tree has to be run somewhere its exit cannot
take the report with it. Prints one line: the case that caught it, or NOT CAUGHT.
"""
import json
import pathlib
import sys
import time

HERE = pathlib.Path(__file__).resolve().parent
ROOT = HERE.parent.parent
TASK = ROOT / "tasks" / "span-claim-charge"
sys.path.insert(0, str(TASK / "tests"))
sys.path.insert(0, str(TASK / "tests" / "seal"))

import cases  # noqa: E402
import gen  # noqa: E402
import model  # noqa: E402

GT = json.loads((TASK / "tests" / "seal" / "gt.json").read_text(encoding="utf-8"))


def main():
    tree = sys.argv[1]
    sys.path.insert(0, tree)
    work = [("hand", n, cases.ops(n)) for n in cases.ORDER]
    want = {n: GT[n] for n in cases.ORDER}
    for fam, name, lines in gen.programs("report", 6):
        if fam in ("wide", "churn"):
            continue
        want[name] = model.expect(lines)
        work.append((fam, name, lines))
    try:
        from base import feed
    except Exception as exc:
        print("import raised %s" % type(exc).__name__, flush=True)
        return 0
    t0 = time.time()
    for _fam, name, lines in work:
        try:
            got = feed.run(lines)
        except Exception as exc:
            print("caught by %s (raised %s)" % (name, type(exc).__name__), flush=True)
            return 0
        if got != want[name]:
            print("caught by %s" % name, flush=True)
            return 0
    print("NOT CAUGHT by any trace (%.1fs on the small set)" % (time.time() - t0), flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
