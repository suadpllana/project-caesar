"""Runs the submitted trainer. Unprivileged, sandboxed, and trusted for nothing.

This is the only stage that executes agent code, so it decides nothing and is told
nothing. It is handed a list of run scripts chosen by a root-only stage before it
started; the sealed model, the frozen answers, the generator and the nonce they
came from all live in a directory this process cannot read. It stages a pristine
copy of the tree, drops the six submitted policy files into it, runs each script,
and writes down what came out. A crash, a hang or a silent exit loses the results,
which the grader reads as a failure and never as a pass.
"""
import importlib
import json
import os
import pathlib
import shutil
import sys
import tempfile
import traceback

TESTS = pathlib.Path(os.environ.get("PDS_TESTS", "/tests"))
WORK = pathlib.Path(os.environ.get("PDS_WORK", "/work"))
SUBMITTED = pathlib.Path(os.environ.get("PDS_SUB", "/app/train"))
PARTS = ("pick.py", "fold.py", "norm.py", "turn.py", "again.py", "keep.py")
PRISTINE = TESTS / "pristine"


def build_tree():
    tmp = pathlib.Path(tempfile.mkdtemp(dir=str(WORK)))
    tree = tmp / "tree"
    shutil.copytree(PRISTINE, tree)
    for name in PARTS:
        one = SUBMITTED / name
        if one.is_file():
            shutil.copy(one, tree / "train" / name)
    return tree


def main():
    out = sys.argv[sys.argv.index("--out") + 1]
    plan = json.loads(
        pathlib.Path(sys.argv[sys.argv.index("--scripts") + 1]).read_text(encoding="utf-8"))

    tree = build_tree()
    sys.path.insert(0, str(tree))
    box = importlib.import_module("train.box")
    ops = importlib.import_module("train.ops")

    recs = []
    for item in plan:
        got, err = None, None
        lines = item["lines"]
        try:
            run = box.Run()
            acc = []
            for ln in lines:
                ops.ex(run, tuple(ln.split()), acc)
            got = acc
        except Exception:
            err = traceback.format_exc(limit=1).strip().splitlines()[-1:]
        recs.append({"fam": item["fam"], "name": item["name"], "lines": list(lines),
                     "got": got, "err": err})

    pathlib.Path(out).write_text(json.dumps(recs), encoding="utf-8")


if __name__ == "__main__":
    main()
