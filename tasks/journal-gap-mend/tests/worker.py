"""Runs the submitted recovery tool. Unprivileged, sandboxed, and trusted for nothing.

This is the only stage that executes agent code, so it decides nothing: it stages a fresh
copy of the shipped tree, drops the five submitted files into it, runs the pristine driver's
`run(text)` on every journal it was handed and writes down what came back. The grader treats
this file's output as hostile. A crash, a hang or a silent exit loses the record, and a lost
record is a failure, never a pass.

The wall clock the platform puts on this process (test.sh) is also the task's execution
limit, so a correct tool that cannot get through the set in time is scored exactly like a
wrong one.
"""
import hashlib
import json
import os
import pathlib
import shutil
import sys
import tempfile
import traceback

TESTS = pathlib.Path(os.environ.get("JGM_TESTS", "/tests"))
WORK = pathlib.Path(os.environ.get("JGM_WORK", "/work"))
SENT = pathlib.Path(os.environ.get("JGM_SUB", "/app/jl"))
PARTS = ("table.py", "tally.py", "span.py", "seek.py", "walk.py")


def sig(text):
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def tree():
    """A fresh copy of the shipped tree with the submitted files laid over it."""
    room = pathlib.Path(tempfile.mkdtemp(dir=str(WORK)))
    here = room / "app"
    shutil.copytree(TESTS / "pristine", here)
    for part in PARTS:
        one = SENT / part
        if one.is_file():
            shutil.copy(one, here / "jl" / part)
    return here


def main():
    out = sys.argv[sys.argv.index("--out") + 1]
    journals = json.loads((WORK / "journals.json").read_text(encoding="utf-8"))

    here = tree()
    sys.path.insert(0, str(here))
    os.chdir(str(here))
    import mend

    recs = []
    for item in journals:
        got, err = None, None
        try:
            got = mend.run(item["text"])
        except Exception:
            err = traceback.format_exc(limit=1).strip().splitlines()[-1:]
        recs.append({"name": item["name"], "sig": sig(item["text"]), "got": got, "err": err})

    pathlib.Path(out).write_text(json.dumps(recs), encoding="utf-8")


if __name__ == "__main__":
    main()
