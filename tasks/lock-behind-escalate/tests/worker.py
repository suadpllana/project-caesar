"""Runs the submitted lock manager. Unprivileged, sandboxed, and trusted for nothing.

This is the only stage that executes agent code, so it decides nothing: it stages a pristine
copy of the tree, lays the six submitted files into it, runs every graded script and writes
down what came out. The grader reads this file's output as hostile input. A crash, a hang or
a silent exit loses the record, and a lost record is a failure, never a pass.

The wall clock the platform puts on this process is also the task's execution limit, so a
correct manager that cannot get through the set in time is scored exactly like a wrong one.
"""
import hashlib
import json
import os
import pathlib
import shutil
import sys
import tempfile
import traceback

TESTS = os.environ.get("LBE_TESTS", "/tests")
sys.path.insert(0, TESTS)

import cases  # noqa: E402
import gen  # noqa: E402

WORK = pathlib.Path(os.environ.get("LBE_WORK", "/work"))
SENT = pathlib.Path(os.environ.get("LBE_SUB", "/app/lm"))
PRISTINE = pathlib.Path(TESTS) / "pristine"
PARTS = ("held.py", "wait.py", "grant.py", "esc.py", "dead.py", "settle.py")


def digest(lines):
    return hashlib.sha256("\n".join(lines).encode("utf-8")).hexdigest()


def stage():
    """A fresh copy of the shipped tree with the six submitted files laid over it."""
    room = pathlib.Path(tempfile.mkdtemp(dir=str(WORK)))
    here = room / "app"
    shutil.copytree(PRISTINE, here)
    for part in PARTS:
        sent = SENT / part
        if sent.is_file():
            shutil.copy(sent, here / "lm" / part)
    return here


def main():
    out = sys.argv[sys.argv.index("--out") + 1]
    seed = (WORK / "nonce").read_text(encoding="utf-8").strip()
    per = int((WORK / "per").read_text(encoding="utf-8").strip())

    here = stage()
    sys.path.insert(0, str(here))
    import run_lm

    jobs = [("hand", name, cases.prog(name)) for name in cases.ORDER]
    jobs += gen.programs(seed, per)

    recs = []
    for fam, name, lines in jobs:
        got, err = None, None
        try:
            got = run_lm.run("\n".join(lines) + "\n")
        except Exception:
            err = traceback.format_exc(limit=1).strip().splitlines()[-1:]
        recs.append({"fam": fam, "name": name, "sig": digest(lines), "got": got, "err": err})

    pathlib.Path(out).write_text(json.dumps(recs), encoding="utf-8")


if __name__ == "__main__":
    main()
