"""Runs the submitted binder. Unprivileged, sandboxed, and trusted for nothing.

This is the only stage that executes submitted code, so it decides nothing: it lays the four
submitted files over a pristine tree staged by root, runs every program, and writes down what
came out. It cannot read `/tests` - the sealed model, the frozen answers and the generator are
shut to this uid - so the only route to a matching record is to settle the programs correctly.

A crash, a hang or a silent exit loses the results, which the grader reads as a failure and
never as a pass.
"""
import json
import os
import pathlib
import shutil
import sys
import traceback

WORK = pathlib.Path(os.environ.get("UTB_WORK", "/work"))
SUB = pathlib.Path(os.environ.get("UTB_SUB", "/app/res"))
TREE = pathlib.Path(os.environ.get("UTB_TREE", "/work/tree"))
PARTS = ("step.py", "show.py", "pick.py", "turn.py")


def stage():
    """A private copy of the pristine tree with the submitted four laid over `res/`."""
    dst = WORK / "run"
    if dst.exists():
        shutil.rmtree(dst)
    shutil.copytree(TREE, dst)
    for name in PARTS:
        one = SUB / name
        if one.is_file():
            shutil.copy(one, dst / "res" / name)
    return dst


def main():
    out = sys.argv[sys.argv.index("--out") + 1]
    progs = json.loads((WORK / "progs.json").read_text(encoding="utf-8"))

    dst = stage()
    sys.path.insert(0, str(dst))
    from prog.deck import at
    from prog.read import load
    from res.tell import line
    from res.turn import run

    recs = []
    for item in progs:
        lines = item["lines"]
        got, err = None, None
        try:
            prog = load("\n".join(lines) + "\n")
            deck = run(prog)
            got = [line(un, x, at(deck, un, x)) for un, x in prog.asks]
        except Exception:  # noqa: BLE001
            err = traceback.format_exc(limit=1).strip().splitlines()[-1:]
        recs.append({"fam": item["fam"], "name": item["name"], "lines": lines,
                     "got": got, "err": err})

    pathlib.Path(out).write_text(json.dumps(recs), encoding="utf-8", newline="\n")


if __name__ == "__main__":
    main()
