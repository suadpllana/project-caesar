"""Runs the submitted accounting layer. Unprivileged, sandboxed, and trusted for nothing.

Everything this file produces is treated as hostile by the grader: it is the only stage that
executes agent code, so it decides nothing. It stages a pristine store, drops the four submitted
files into it, runs the scripts it was handed, and writes down what came out. A crash, a hang or
a silent exit loses the results, which the grader reads as a failure - never as a pass.

It reads no answers, because there are none within reach: the scripts arrive as data and the
model, the ground truth and the generator are root-only by the time this runs.
"""
import hashlib
import json
import os
import pathlib
import shutil
import sys
import tempfile
import traceback

WORK = pathlib.Path(os.environ.get("SCS_WORK", "/work"))
FEED = pathlib.Path(os.environ.get("SCS_FEED", "/feed/scripts.json"))
SUBMITTED = pathlib.Path(os.environ.get("SCS_SUB", "/app/bil"))
PRISTINE = pathlib.Path(os.environ.get("SCS_TESTS", "/tests")) / "pristine"
PARTS = ("own.py", "agg.py", "gate.py", "edit.py")


def sig(lines):
    return hashlib.sha256("\n".join(lines).encode("utf-8")).hexdigest()


def build_tree():
    tmp = pathlib.Path(tempfile.mkdtemp(dir=str(WORK)))
    tree = tmp / "tree"
    shutil.copytree(PRISTINE, tree)
    for name in PARTS:
        one = SUBMITTED / name
        if one.is_file():
            shutil.copy(one, tree / "bil" / name)
    return tree


def main():
    out = sys.argv[sys.argv.index("--out") + 1]
    jobs = json.loads(FEED.read_text(encoding="utf-8"))

    tree = build_tree()
    sys.path.insert(0, str(tree))
    import ops
    from st import tree as store

    recs = []
    for job in jobs:
        lines = job["lines"]
        got, err = None, None
        try:
            got = ops.run(store.St(), [tuple(ln.split()) for ln in lines])
        except Exception:
            err = traceback.format_exc(limit=1).strip().splitlines()[-1:]
        recs.append({"fam": job["fam"], "name": job["name"], "sig": sig(lines),
                     "got": got, "err": err})

    pathlib.Path(out).write_text(json.dumps(recs), encoding="utf-8")


if __name__ == "__main__":
    main()
