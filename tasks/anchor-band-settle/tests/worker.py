"""Runs the submitted view modules. Unprivileged, sandboxed, and trusted for nothing.

This is the only stage that executes agent code, so it decides nothing: it stages a pristine
copy of the tree, drops the four submitted files into it, runs every program of the graded set
through the frozen frame driver, one after another in this one process, and writes down what
each printed. The grader treats this file's output as hostile input. A crash, a hang or a
silent exit loses the record, and a lost record is a failure, never a pass.

The wall clock the platform puts on this process is also the task's execution limit, so a
correct implementation that cannot get through the set in time is scored exactly like a wrong
one. The two scale families exist for that.
"""
import hashlib
import json
import os
import pathlib
import shutil
import sys
import tempfile
import traceback

TESTS = pathlib.Path(os.environ.get("ABS_TESTS", "/tests"))
WORK = pathlib.Path(os.environ.get("ABS_WORK", "/work"))
SENT = pathlib.Path(os.environ.get("ABS_SUB", "/app/view"))
PRISTINE = TESTS / "pristine"
PARTS = ("lay.py", "stick.py", "pick.py", "hold.py")


def sig(text):
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def tree():
    """A fresh copy of the shipped tree with the submitted view files laid over it."""
    room = pathlib.Path(tempfile.mkdtemp(dir=str(WORK)))
    here = room / "app"
    shutil.copytree(PRISTINE, here)
    for part in PARTS:
        one = SENT / part
        if one.is_file():
            shutil.copy(one, here / "view" / part)
    return here


def main():
    progs_path = sys.argv[sys.argv.index("--progs") + 1]
    out = sys.argv[sys.argv.index("--out") + 1]
    progs = json.loads(pathlib.Path(progs_path).read_text(encoding="utf-8"))

    here = tree()
    sys.path.insert(0, str(here))
    from view import frame

    recs = []
    for item in progs:
        text = item["text"]
        got, err = None, None
        try:
            got = frame.run(text)
        except Exception:
            err = traceback.format_exc(limit=1).strip().splitlines()[-1:]
        recs.append({"fam": item["fam"], "name": item["name"], "sig": sig(text),
                     "got": got, "err": err})

    pathlib.Path(out).write_text(json.dumps(recs), encoding="utf-8")


if __name__ == "__main__":
    main()
