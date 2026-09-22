"""Runs the submitted rebuild. Unprivileged, sandboxed, and trusted for nothing.

This is the only stage that executes agent code, so it decides nothing: it stages a pristine
copy of the tree, drops the six submitted files into it, runs every graded program and writes
down what came out. The grader treats this file's output as hostile input. A crash, a hang or
a silent exit loses the record, and a lost record is a failure, never a pass.

The wall clock the harness puts on this process is also the task's stated execution limit, so
a rebuild whose answers are right but which cannot get through the set in time is scored
exactly like a wrong one. Two of the eleven families exist for that: one program whose source
grows under a long walk, and one whose journal runs far longer than its source.
"""
import hashlib
import json
import os
import pathlib
import shutil
import sys
import tempfile
import traceback

TESTS = os.environ.get("RCR_TESTS", "/tests")
sys.path.insert(0, TESTS)

import cases  # noqa: E402
import gen  # noqa: E402

WORK = pathlib.Path(os.environ.get("RCR_WORK", "/work"))
SENT = pathlib.Path(os.environ.get("RCR_SUB", "/app/reb"))
PRISTINE = pathlib.Path(TESTS) / "pristine"
PARTS = ("walk.py", "mark.py", "sift.py", "place.py", "wait.py", "tally.py")


def sig(lines):
    return hashlib.sha256("\n".join(lines).encode("utf-8")).hexdigest()


def tree():
    """A fresh copy of the shipped tree with the submitted reb files laid over it."""
    room = pathlib.Path(tempfile.mkdtemp(dir=str(WORK)))
    here = room / "app"
    shutil.copytree(PRISTINE, here)
    for part in PARTS:
        one = SENT / part
        if one.is_file():
            shutil.copy(one, here / "reb" / part)
    return here


def main():
    out = sys.argv[sys.argv.index("--out") + 1]
    seed = (WORK / "nonce").read_text(encoding="utf-8").strip()
    per = int((WORK / "per").read_text(encoding="utf-8").strip())

    here = tree()
    sys.path.insert(0, str(here))
    import run_reb

    work = [("hand", name, cases.prog(name)) for name in cases.ORDER]
    work += gen.programs(seed, per)

    recs = []
    for fam, name, lines in work:
        got, err = None, None
        try:
            got = run_reb.run("\n".join(lines) + "\n")
        except Exception:
            err = traceback.format_exc(limit=1).strip().splitlines()[-1:]
        recs.append({"fam": fam, "name": name, "sig": sig(lines), "got": got, "err": err})

    pathlib.Path(out).write_text(json.dumps(recs), encoding="utf-8")


if __name__ == "__main__":
    main()
