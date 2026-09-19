"""Runs the submitted feeder. Unprivileged, sandboxed, and trusted for nothing.

This is the only stage that executes agent code, so it decides nothing: it stages a pristine
copy of the shipped tree, drops the six submitted files into it, runs every graded plan through
the shipped driver's own op table, and writes down what came out. The grader treats this file's
output as hostile input. A crash, a hang or a silent exit loses the record, and a lost record is
a failure, never a pass.

The wall clock the caller puts on this process is also the task's execution limit, so a feeder
that is right in every rule and walks the stream one slot at a time is scored exactly like a
wrong one. Two of the eleven families exist for that: the wide plans take 780000 steps of 256
slots, which is 200 million samples, and the deep plans do the same with a source that retires
two thirds of the way in.
"""
import hashlib
import json
import os
import pathlib
import shutil
import sys
import tempfile
import traceback

TESTS = os.environ.get("MRR_TESTS", "/tests")
sys.path.insert(0, TESTS)

import cases  # noqa: E402
import gen  # noqa: E402

WORK = pathlib.Path(os.environ.get("MRR_WORK", "/work"))
SENT = pathlib.Path(os.environ.get("MRR_SUB", "/app/feed"))
PRISTINE = pathlib.Path(TESTS) / "pristine"
PARTS = ("mix.py", "deck.py", "draw.py", "spot.py", "deal.py", "keep.py")


def sig(lines):
    return hashlib.sha256("\n".join(lines).encode("utf-8")).hexdigest()


def tree():
    """A fresh copy of the shipped tree with the submitted feed files laid over it."""
    room = pathlib.Path(tempfile.mkdtemp(dir=str(WORK)))
    here = room / "app"
    shutil.copytree(PRISTINE, here)
    for part in PARTS:
        one = SENT / part
        if one.is_file():
            shutil.copy(one, here / "feed" / part)
    return here


def main():
    out = sys.argv[sys.argv.index("--out") + 1]
    seed = (WORK / "nonce").read_text(encoding="utf-8").strip()
    per = int((WORK / "per").read_text(encoding="utf-8").strip())

    here = tree()
    sys.path.insert(0, str(here))
    import ops
    import plan

    work = [("hand", name, cases.ops(name)) for name in cases.ORDER]
    work += gen.programs(seed, per)

    recs = []
    for fam, name, lines in work:
        got, err = None, None
        try:
            box = plan.Box()
            for line in lines:
                line = line.strip()
                if line:
                    ops.ex(box, tuple(line.split()))
            got = box.out
        except Exception:
            err = traceback.format_exc(limit=1).strip().splitlines()[-1:]
        recs.append({"fam": fam, "name": name, "sig": sig(lines), "got": got, "err": err})

    pathlib.Path(out).write_text(json.dumps(recs), encoding="utf-8")


if __name__ == "__main__":
    main()
