"""Runs the submitted rebuild engine. Unprivileged, sandboxed, and trusted for nothing.

This is the only stage that executes agent code, so it decides nothing: it stages a pristine
copy of the tree, drops the five submitted files into it, drives every graded program through
the frozen driver and writes down what each one printed. The grader treats this file's output
as hostile input. A crash, a hang or a silent exit loses the record, and a lost record is a
failure, never a pass.

Each program gets a fresh engine through the frozen entry point, so nothing an engine keeps
between programs can help it: two of the enumerated programs differ only in a seed word.

The wall clock the platform puts on this process is also the task's execution limit, so an
engine that is right and cannot get through the set in time is scored exactly like a wrong
one. The two `deep` programs exist for that: each level of their pull graph is reachable two
ways, so an engine that re-walks a record every time the step is pulled does the same work
twice per level.
"""
import hashlib
import json
import os
import pathlib
import shutil
import sys
import tempfile
import traceback

TESTS = os.environ.get("PCS_TESTS", "/tests")
sys.path.insert(0, TESTS)

import cases  # noqa: E402
import gen  # noqa: E402

WORK = pathlib.Path(os.environ.get("PCS_WORK", "/work"))
SENT = pathlib.Path(os.environ.get("PCS_SUB", "/app/eng"))
PRISTINE = pathlib.Path(TESTS) / "pristine"
PARTS = ("keep.py", "mark.py", "hold.py", "step.py", "wake.py")


def sig(text):
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def tree():
    """A fresh copy of the shipped tree with the submitted engine files laid over it."""
    room = pathlib.Path(tempfile.mkdtemp(dir=str(WORK)))
    here = room / "app"
    shutil.copytree(PRISTINE, here)
    for part in PARTS:
        one = SENT / part
        if one.is_file():
            shutil.copy(one, here / "eng" / part)
    return here


def main():
    out = sys.argv[sys.argv.index("--out") + 1]
    seed = (WORK / "nonce").read_text(encoding="utf-8").strip()
    per = int((WORK / "per").read_text(encoding="utf-8").strip())

    here = tree()
    sys.path.insert(0, str(here))
    import run_eng
    from eng import plan

    work = [("hand", name, cases.prog(name)) for name in cases.ORDER]
    work += [(pid.split(".")[0], pid, text) for pid, text in gen.programs(seed, per)]

    recs = []
    for fam, name, text in work:
        got, err = None, None
        try:
            got = run_eng.run(plan.parse(text)).split("\n")
        except Exception:
            err = traceback.format_exc(limit=1).strip().splitlines()[-1:]
        recs.append({"fam": fam, "name": name, "sig": sig(text), "got": got, "err": err})

    pathlib.Path(out).write_text(json.dumps(recs), encoding="utf-8")


if __name__ == "__main__":
    main()
