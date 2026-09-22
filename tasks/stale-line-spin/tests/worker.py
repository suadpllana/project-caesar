"""Runs the submitted model files. Unprivileged, sandboxed, and trusted for nothing.

This is the only stage that executes agent code, so it decides nothing: it stages a pristine
copy of the tree, drops the six submitted files into it, runs every graded launch and writes
down what came out. The grader treats this file's output as hostile input. A crash, a hang or
a silent exit loses the record, and a lost record is a failure, never a pass.

The wall clock the platform puts on this process is also the task's execution limit, so a
correct model that cannot get through the set in time is scored exactly like a wrong one. Two
of the families exist for that: launches of thousands of blocks where long work overlaps
blocks that spin, which a model that steps every cycle cannot finish.
"""
import hashlib
import json
import os
import pathlib
import shutil
import sys
import tempfile
import traceback

TESTS = os.environ.get("SLS_TESTS", "/tests")
sys.path.insert(0, TESTS)

import cases  # noqa: E402
import gen  # noqa: E402

WORK = pathlib.Path(os.environ.get("SLS_WORK", "/work"))
SENT = pathlib.Path(os.environ.get("SLS_SUB", "/app/sim"))
PRISTINE = pathlib.Path(TESTS) / "pristine"
PARTS = ("line.py", "mem.py", "place.py", "turn.py", "step.py", "clock.py")


def sig(lines):
    return hashlib.sha256("\n".join(lines).encode("utf-8")).hexdigest()


def tree():
    """A fresh copy of the shipped tree with the six submitted files laid over it."""
    room = pathlib.Path(tempfile.mkdtemp(dir=str(WORK)))
    here = room / "app"
    shutil.copytree(PRISTINE, here)
    for part in PARTS:
        one = SENT / part
        if one.is_file():
            shutil.copy(one, here / "sim" / part)
    return here


def main():
    out = sys.argv[sys.argv.index("--out") + 1]
    seed = (WORK / "nonce").read_text(encoding="utf-8").strip()
    per = int((WORK / "per").read_text(encoding="utf-8").strip())

    here = tree()
    sys.path.insert(0, str(here))
    import run_launch

    work = [("hand", name, cases.prog(name)) for name in cases.ORDER]
    work += gen.programs(seed, per)

    recs = []
    for fam, name, lines in work:
        got, err = None, None
        try:
            got = run_launch.run("\n".join(lines) + "\n")
        except Exception:
            err = traceback.format_exc(limit=1).strip().splitlines()[-1:]
        recs.append({"fam": fam, "name": name, "sig": sig(lines), "got": got, "err": err})

    pathlib.Path(out).write_text(json.dumps(recs), encoding="utf-8")


if __name__ == "__main__":
    main()
