"""Stage one: run the submitted page layer. Unprivileged, and trusted for nothing.

This is the only stage that executes agent code, so it settles nothing. It stages a copy of
the pristine tree, drops the five submitted files into it, runs every graded program and
writes down what each one printed, with a digest of the program text it actually ran. Stage
two treats this file as hostile input: a crash, a hang, a truncated file or a digest that
does not match its own copy of the program is a failure and never a pass.

The wall clock the runner puts on this process is the task's execution limit as well. Two of
the graded programs are large on purpose, so an implementation that is correct but rederives
work it could have located stays exactly correct and runs out of time.
"""
import hashlib
import json
import os
import pathlib
import shutil
import sys
import tempfile
import traceback

KIT = os.environ.get("PBC_KIT", "/tests")
sys.path.insert(0, KIT)

import cases  # noqa: E402
import gen  # noqa: E402

YARD = pathlib.Path(os.environ.get("PBC_YARD", "/work"))
SENT = pathlib.Path(os.environ.get("PBC_SENT", "/app/pg"))
CLEAN = pathlib.Path(KIT) / "pristine"
PARTS = ("fit.py", "bound.py", "cut.py", "join.py", "step.py")


def stamp(body):
    return hashlib.sha256(body.encode("utf-8")).hexdigest()


def staged():
    """A copy of the shipped tree with the submitted policy files laid over it."""
    room = pathlib.Path(tempfile.mkdtemp(dir=str(YARD)))
    here = room / "app"
    shutil.copytree(CLEAN, here)
    for part in PARTS:
        one = SENT / part
        if one.is_file():
            shutil.copy(one, here / "pg" / part)
    return here


def main():
    into = sys.argv[sys.argv.index("--into") + 1]
    seed = int((YARD / "seed").read_text(encoding="utf-8").strip(), 16)
    each = int((YARD / "each").read_text(encoding="utf-8").strip())

    here = staged()
    sys.path.insert(0, str(here))
    import run_idx

    work = [("hand", name, "\n".join(cases.prog(name)) + "\n") for name in cases.ORDER]
    work += [("made", name, body) for name, body in gen.population(seed, each)]

    rows = []
    for kind, name, body in work:
        got = None
        err = None
        try:
            got = run_idx.run(body)
        except Exception:
            err = traceback.format_exc(limit=1).strip().splitlines()[-1:]
        rows.append({"kind": kind, "name": name, "stamp": stamp(body),
                     "got": got, "err": err})

    pathlib.Path(into).write_text(json.dumps(rows), encoding="utf-8")


if __name__ == "__main__":
    main()
