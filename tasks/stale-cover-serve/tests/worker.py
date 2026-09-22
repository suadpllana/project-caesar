"""Half one of grading: run the submitted cache and write down what it printed.

This is the only stage that executes anything the agent wrote, so it is given no authority at
all. It runs unprivileged, in its own session, under a wall clock, and it decides nothing: it
lays the seven submitted files over a pristine copy of the shipped tree, drives every graded
program through the driver in that copy, and records the output. Half two reads the record as
hostile input and does the deciding.

The wall clock on this process is the task's execution limit. Two of the eleven families are
sized for it: a long history whose reads reach back over the whole of it, and a large key
space whose reads cluster. A cache that is exactly right and searches the allowance one
version at a time does not get through them.

A crash, a hang, a truncated record or a missing program is a failure. Nothing here can turn
into a pass by omission, because half two rebuilds the program list itself and insists on
finding every one of them in the record, with the digest of the text that was actually run.
"""
import hashlib
import json
import os
import pathlib
import shutil
import sys
import tempfile
import traceback

KIT = os.environ.get("SCS_TESTS", "/tests")
sys.path.insert(0, KIT)

import cases  # noqa: E402
import gen  # noqa: E402

DESK = pathlib.Path(os.environ.get("SCS_WORK", "/work"))
SENT = pathlib.Path(os.environ.get("SCS_SUB", "/app/rng"))
CLEAN = pathlib.Path(KIT) / "pristine"
PARTS = ("seg.py", "pick.py", "hole.py", "mend.py", "knit.py", "age.py", "ask.py")


def digest(text):
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def staged():
    """A pristine copy of the shipped tree carrying the seven submitted files."""
    room = pathlib.Path(tempfile.mkdtemp(dir=str(DESK)))
    here = room / "app"
    shutil.copytree(CLEAN, here)
    for part in PARTS:
        sent = SENT / part
        if sent.is_file():
            shutil.copy(sent, here / "rng" / part)
    return here


def main():
    out = sys.argv[sys.argv.index("--out") + 1]
    seed = (DESK / "nonce").read_text(encoding="utf-8").strip()
    per = int((DESK / "per").read_text(encoding="utf-8").strip())

    here = staged()
    sys.path.insert(0, str(here))
    import run_rng

    jobs = [("hand", name, cases.prog(name)) for name in cases.ORDER]
    jobs += gen.programs(seed, per)

    kept = []
    for fam, name, lines in jobs:
        text = "\n".join(lines) + "\n"
        said, blew = None, None
        try:
            said = run_rng.run(text)
        except Exception:
            blew = traceback.format_exc(limit=1).strip().splitlines()[-1:]
        kept.append({"fam": fam, "name": name, "seal": digest(text),
                     "said": said, "blew": blew})

    pathlib.Path(out).write_text(json.dumps(kept), encoding="utf-8")


if __name__ == "__main__":
    main()
