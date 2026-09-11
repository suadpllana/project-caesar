"""Runs the submitted service. Unprivileged, sandboxed, and trusted for nothing.

This is the only stage that executes agent code, so it decides nothing: it stages a pristine
copy of the tree, drops the five submitted modules into it, runs every graded program, and
writes down what came out. The grader treats this file's output as hostile input; a crash, a
hang or a silent exit loses the record, and a lost record is a failure, never a pass.

The service is imported fresh for each program, exactly as `run.py` gets it, so nothing a
program leaves behind in a module can reach the next one.

The wall clock the harness puts on this process is also the task's execution limit, so a
service that settles every program correctly and cannot get through the set in time is scored
exactly like a wrong one. Two families exist for that: one item carried by a crowd of holders
with a queue of claims behind a stuck raise, and many items each holding a request that never
goes through while the work happens elsewhere.
"""
import hashlib
import importlib
import json
import os
import pathlib
import shutil
import sys
import tempfile
import traceback

TESTS = os.environ.get("CRC_TESTS", "/tests")
sys.path.insert(0, TESTS)

import cases  # noqa: E402
import gen  # noqa: E402

WORK = pathlib.Path(os.environ.get("CRC_WORK", "/work"))
SENT = pathlib.Path(os.environ.get("CRC_SUB", "/app/hold"))
PRISTINE = pathlib.Path(TESTS) / "pristine"
PARTS = ("mark.py", "item.py", "wait.py", "cyc.py", "txn.py")


def sig(steps):
    return hashlib.sha256("\n".join(" ".join(s) for s in steps).encode("utf-8")).hexdigest()


def tree():
    """A fresh copy of the shipped tree with the submitted modules laid over it."""
    room = pathlib.Path(tempfile.mkdtemp(dir=str(WORK)))
    here = room / "app"
    shutil.copytree(PRISTINE, here)
    for part in PARTS:
        one = SENT / part
        if one.is_file():
            shutil.copy(one, here / "hold" / part)
    return here


def fresh():
    for name in [n for n in sys.modules if n == "hold" or n.startswith("hold.")]:
        del sys.modules[name]
    return importlib.import_module("hold.out"), importlib.import_module("hold.txn")


def main():
    out = sys.argv[sys.argv.index("--out") + 1]
    seed = (WORK / "nonce").read_text(encoding="utf-8").strip()
    per = int((WORK / "per").read_text(encoding="utf-8").strip())
    heavy = int((WORK / "heavy").read_text(encoding="utf-8").strip())

    here = tree()
    sys.path.insert(0, str(here))

    work = [("hand", name, steps) for name, steps in cases.programs()]
    work += [(name.rsplit("-", 1)[0], name, steps)
             for name, steps in gen.programs(seed, per, heavy)]

    recs = []
    for fam, name, steps in work:
        got, err = None, None
        try:
            trace, txn = fresh()
            tr = trace.Trace()
            svc = txn.Svc(tr)
            for st in steps:
                svc.step(st)
            got = tr.lines
        except Exception:
            err = traceback.format_exc(limit=1).strip().splitlines()[-1:]
        recs.append({"fam": fam, "name": name, "sig": sig(steps), "got": got, "err": err})

    pathlib.Path(out).write_text(json.dumps(recs), encoding="utf-8")


if __name__ == "__main__":
    main()
