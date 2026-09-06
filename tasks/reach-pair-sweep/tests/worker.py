"""Runs the submitted collector. Unprivileged, sandboxed, and trusted for nothing.

Everything this file produces is treated as hostile by the grader: it is the only stage that
executes agent code, so it decides nothing. It stages a pristine tree, drops the submitted
`cyc/keep.py` into it, runs every program, and writes down what came out. A crash, a hang or a
silent exit loses the results, which the grader reads as a failure - never as a pass.
"""
import json
import os
import pathlib
import shutil
import sys
import tempfile
import traceback

TESTS = os.environ.get("RPS_TESTS", "/tests")
sys.path.insert(0, TESTS)

import cases  # noqa: E402
import gen  # noqa: E402

WORK = pathlib.Path(os.environ.get("RPS_WORK", "/work"))
SUBMITTED = pathlib.Path(os.environ.get("RPS_SUB", "/app/col"))
PARTS = ("plan.py", "scan.py", "keep.py", "age.py", "wipe.py")
PRISTINE = pathlib.Path(TESTS) / "pristine"


def build_tree():
    tmp = pathlib.Path(tempfile.mkdtemp(dir=str(WORK)))
    tree = tmp / "tree"
    shutil.copytree(PRISTINE, tree)
    for name in PARTS:
        one = SUBMITTED / name
        if one.is_file():
            shutil.copy(one, tree / "col" / name)
    return tree


def main():
    out = sys.argv[sys.argv.index("--out") + 1]
    nonce = (WORK / "nonce").read_text(encoding="utf-8").strip()
    per = int((WORK / "per").read_text(encoding="utf-8").strip())

    tree = build_tree()
    sys.path.insert(0, str(tree))
    import ops
    from mem import heap

    progs = [("hand", n, cases.CASES[n]) for n in cases.ORDER]
    progs += list(gen.programs(nonce, per))

    recs = []
    for fam, name, lines in progs:
        got, err = None, None
        try:
            h = heap.Heap()
            acc = []
            for ln in lines:
                ops.ex(h, tuple(ln.split()), acc)
            got = acc
        except Exception:
            err = traceback.format_exc(limit=1).strip().splitlines()[-1:]
        recs.append({"fam": fam, "name": name, "lines": list(lines),
                     "got": got, "err": err})

    pathlib.Path(out).write_text(json.dumps(recs), encoding="utf-8")


if __name__ == "__main__":
    main()
