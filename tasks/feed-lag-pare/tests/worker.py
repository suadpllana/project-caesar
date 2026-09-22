"""Stage one: run the submitted retention half. Unprivileged, sandboxed, trusted for nothing.

This is the only place agent code executes, so it is allowed to decide nothing. It stages a
fresh copy of the shipped tree, drops the six submitted files into it, walks every graded
program through the driver and writes down what came back. The grader downstream treats this
file's output as hostile input, and a crash, a hang or a quiet exit loses the record - which
is a failure, never a pass.

The wall clock the harness puts on this process is the execution limit the brief states, so a
service that is right and cannot get through the set in time is scored exactly like one that
is wrong. Two of the twelve families are here for that rather than for a rule: one with many
keys, a large standing log and a pare after every few entries, and one with few keys, long
chains and pares that collapse a great deal at once.
"""
import hashlib
import json
import os
import pathlib
import shutil
import sys
import tempfile
import traceback

TESTS = os.environ.get("FLP_TESTS", "/tests")
sys.path.insert(0, TESTS)

import cases  # noqa: E402
import gen  # noqa: E402

WORK = pathlib.Path(os.environ.get("FLP_WORK", "/work"))
GIVEN = pathlib.Path(os.environ.get("FLP_SUB", "/app/lg"))
SHIPPED = pathlib.Path(TESTS) / "pristine"
TAKEN = ("store.py", "pin.py", "fold.py", "span.py", "pare.py", "tell.py")


def fingerprint(lines):
    """What the grader checks the program against, so an altered program cannot pass."""
    return hashlib.sha256("\n".join(lines).encode("utf-8")).hexdigest()


def staged():
    """The shipped tree, fresh, with the six submitted files laid over it."""
    room = pathlib.Path(tempfile.mkdtemp(dir=str(WORK)))
    here = room / "app"
    shutil.copytree(SHIPPED, here)
    for part in TAKEN:
        one = GIVEN / part
        if one.is_file():
            shutil.copy(one, here / "lg" / part)
    return here


def main():
    out = sys.argv[sys.argv.index("--out") + 1]
    seed = (WORK / "nonce").read_text(encoding="utf-8").strip()
    per = int((WORK / "per").read_text(encoding="utf-8").strip())

    here = staged()
    sys.path.insert(0, str(here))
    import run_log

    todo = [("hand", name, cases.prog(name)) for name in cases.ORDER]
    todo += gen.programs(seed, per)

    written = []
    for fam, name, lines in todo:
        printed, blew = None, None
        try:
            printed = run_log.run("\n".join(lines) + "\n")
        except Exception:
            blew = traceback.format_exc(limit=1).strip().splitlines()[-1:]
        written.append({"fam": fam, "name": name, "sig": fingerprint(lines),
                        "got": printed, "err": blew})

    pathlib.Path(out).write_text(json.dumps(written), encoding="utf-8")


if __name__ == "__main__":
    main()
