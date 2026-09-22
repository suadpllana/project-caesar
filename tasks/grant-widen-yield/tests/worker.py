"""Runs the submitted lock service. Unprivileged, sandboxed, and trusted for nothing.

This is the only stage that executes agent code, so it decides nothing: it stages a pristine
copy of the tree, drops the six submitted files into it, runs every graded program and writes
down what came out. The grader treats this file's output as hostile input. A crash, a hang or a
silent exit loses the record, and a lost record is a failure, never a pass.

The wall clock the runner puts on this process is also the task's execution limit, so a correct
service that cannot get through the set in time is scored exactly like a wrong one. Two of the
eleven families exist for that: five programs of around twenty thousand lines in which one
transaction holds nine thousand keys under a single block, and five of around twenty-five
thousand lines across nearly four hundred transactions with eleven thousand standing claims.
"""
import hashlib
import json
import os
import pathlib
import shutil
import sys
import tempfile
import traceback

TESTS = os.environ.get("GWY_TESTS", "/tests")
sys.path.insert(0, TESTS)

import cases  # noqa: E402
import gen  # noqa: E402

WORK = pathlib.Path(os.environ.get("GWY_WORK", "/work"))
SENT = pathlib.Path(os.environ.get("GWY_SUB", "/app/lk"))
PRISTINE = pathlib.Path(TESTS) / "pristine"
PARTS = ("mode.py", "hold.py", "give.py", "keep.py", "wide.py", "step.py")


def sig(rows):
    return hashlib.sha256("\n".join(rows).encode("utf-8")).hexdigest()


def tree():
    """A fresh copy of the shipped tree with the submitted lk files laid over it."""
    room = pathlib.Path(tempfile.mkdtemp(dir=str(WORK)))
    here = room / "app"
    shutil.copytree(PRISTINE, here)
    for part in PARTS:
        one = SENT / part
        if one.is_file():
            shutil.copy(one, here / "lk" / part)
    return here


def main():
    out = sys.argv[sys.argv.index("--out") + 1]
    seed = (WORK / "nonce").read_text(encoding="utf-8").strip()
    per = int((WORK / "per").read_text(encoding="utf-8").strip())

    here = tree()
    sys.path.insert(0, str(here))
    import run_lk

    work = [("hand", name, cases.prog(name)) for name in cases.ORDER]
    work += gen.programs(seed, per)

    recs = []
    for fam, name, rows in work:
        got, err = None, None
        try:
            got = run_lk.run("\n".join(rows) + "\n")
        except Exception:
            err = traceback.format_exc(limit=1).strip().splitlines()[-1:]
        recs.append({"fam": fam, "name": name, "sig": sig(rows), "got": got, "err": err})

    pathlib.Path(out).write_text(json.dumps(recs), encoding="utf-8")


if __name__ == "__main__":
    main()
