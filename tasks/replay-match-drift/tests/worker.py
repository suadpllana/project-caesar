"""Stage one of grading: run the submitted replay engine and write down what it printed.

This is the only process that executes anything the agent wrote, so it is given no
authority at all. It runs as an unprivileged uid, inside a directory it owns, under the
wall clock that is also the task's execution limit, and it reaches no verdict: it produces
a record, and stage two reads that record as hostile input. A crash, a hang, a truncated
file or a silent exit costs the record, and a missing record is a failure.

What it stages is the verifier's own copy of the tree with the seven submitted files dropped
into it, so the run-file grammar, the body machine, the trace writer and the driver are
the ones the task shipped whatever the submission did to them, and a seventh file left
beside the seven is never picked up.

The two scale families are here for the clock. An engine that looks a branch up by walking
every branch for the one whose turn is next, or a command up by walking the recorded
history, is exactly correct and cannot finish them.
"""
import hashlib
import json
import os
import pathlib
import shutil
import sys
import tempfile
import traceback

TESTS = os.environ.get("RMD_TESTS", "/tests")
sys.path.insert(0, TESTS)

import cases  # noqa: E402
import gen  # noqa: E402

WORK = pathlib.Path(os.environ.get("RMD_WORK", "/work"))
SENT = pathlib.Path(os.environ.get("RMD_SENT", "/app/dur"))
CLEAN = pathlib.Path(TESTS) / "pristine"
PARTS = ("tab.py", "edge.py", "pair.py", "hold.py", "sched.py", "wake.py",
         "ver.py")


def stamp(lines):
    """A fingerprint of the run file, so stage two can see it was graded unaltered."""
    return hashlib.sha256("\n".join(lines).encode("utf-8")).hexdigest()


def laid_over():
    room = pathlib.Path(tempfile.mkdtemp(dir=str(WORK)))
    tree = room / "app"
    shutil.copytree(CLEAN, tree)
    for part in PARTS:
        sent = SENT / part
        if sent.is_file():
            shutil.copy(sent, tree / "dur" / part)
    return tree


def main():
    out = sys.argv[sys.argv.index("--out") + 1]
    seed = (WORK / "seed").read_text(encoding="utf-8").strip()
    per = int((WORK / "per").read_text(encoding="utf-8").strip())

    tree = laid_over()
    sys.path.insert(0, str(tree))
    import run_dur

    work = [("hand", name, cases.prog(name)) for name in cases.ORDER]
    work.extend(gen.programs(seed, per))

    rows = []
    for fam, name, lines in work:
        printed = None
        blew = None
        try:
            printed = run_dur.run("\n".join(lines) + "\n")
        except Exception:
            blew = traceback.format_exc(limit=1).strip().splitlines()[-1:]
        rows.append({
            "fam": fam,
            "name": name,
            "stamp": stamp(lines),
            "printed": printed,
            "blew": blew,
        })

    pathlib.Path(out).write_text(json.dumps(rows), encoding="utf-8")


if __name__ == "__main__":
    main()
