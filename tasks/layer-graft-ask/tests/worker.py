"""Runs the submitted service. Unprivileged, sandboxed, and trusted for nothing.

This is the only stage that executes agent code, so it decides nothing: it stages a pristine
copy of the tree, drops the six submitted files into it, runs every graded plan through the
shipped driver, and writes down what came out. The grader treats this file's output as hostile
input. A crash, a hang, or a silent exit loses the record, and a lost record is a failure,
never a pass.

The wall clock the platform puts on this process is also the task's execution limit, so a
service that answers correctly but cannot get through the set in time is scored exactly like a
wrong one. Two of the ten families exist for that: one that puts twenty thousand paths under
two prefixes and then asks how many are there at forty different stops, and one where a copy
sits beside its own source and is taken again and again.
"""
import contextlib
import hashlib
import io
import json
import os
import pathlib
import shutil
import sys
import tempfile
import traceback

TESTS = os.environ.get("LGA_TESTS", "/tests")
sys.path.insert(0, TESTS)

import cases  # noqa: E402
import gen  # noqa: E402

WORK = pathlib.Path(os.environ.get("LGA_WORK", "/work"))
SENT = pathlib.Path(os.environ.get("LGA_SUB", "/app/cfg"))
PRISTINE = pathlib.Path(TESTS) / "pristine"
PARTS = ("pile.py", "past.py", "made.py", "roll.py", "work.py", "ans.py")


def sig(text):
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def tree():
    """A fresh copy of the shipped tree with the submitted cfg files laid over it."""
    room = pathlib.Path(tempfile.mkdtemp(dir=str(WORK)))
    here = room / "app"
    shutil.copytree(PRISTINE, here)
    for part in PARTS:
        one = SENT / part
        if one.is_file():
            shutil.copy(one, here / "cfg" / part)
    return here


def main():
    out = sys.argv[sys.argv.index("--out") + 1]
    seed = (WORK / "nonce").read_text(encoding="utf-8").strip()
    per = int((WORK / "per").read_text(encoding="utf-8").strip())
    scale = int((WORK / "scale").read_text(encoding="utf-8").strip())

    here = tree()
    sys.path.insert(0, str(here))
    import run_plan

    plans = [(name, cases.PLANS[name]) for name in sorted(cases.PLANS)]
    plans += gen.programs(seed, per, scale=scale)

    room = pathlib.Path(tempfile.mkdtemp(dir=str(WORK)))
    recs = []
    for name, text in plans:
        path = room / (name + ".txt")
        with open(path, "w", encoding="utf-8", newline="\n") as fh:
            fh.write(text)
        got, err, code = None, None, None
        buf = io.StringIO()
        try:
            with contextlib.redirect_stdout(buf):
                code = run_plan.main(["run_plan.py", str(path)])
            got = buf.getvalue().split("\n")
            if got and got[-1] == "":
                got.pop()
        except BaseException:
            err = traceback.format_exc(limit=1).strip().splitlines()[-1:]
        os.unlink(path)
        recs.append({"name": name, "sig": sig(text), "code": code, "got": got, "err": err})

    pathlib.Path(out).write_text(json.dumps(recs), encoding="utf-8")


if __name__ == "__main__":
    main()
