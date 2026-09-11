#!/usr/bin/env python3
"""Time one set of opt/ files against a program, in process, outside the bundle."""
import pathlib
import shutil
import sys
import tempfile
import time

ROOT = pathlib.Path(__file__).resolve().parent.parent.parent
TASK = ROOT / "tasks" / "shard-spend-carry"
PARTS = ("cell.py", "lay.py", "cut.py", "walk.py", "tick.py", "keep.py")


def tree(over):
    room = pathlib.Path(tempfile.mkdtemp(prefix="ssc-"))
    here = room / "app"
    shutil.copytree(TASK / "environment" / "app_src", here)
    if over:
        for part in PARTS:
            one = pathlib.Path(over) / part
            if one.is_file():
                shutil.copy(one, here / "opt" / part)
    return here


def main():
    over, prog = sys.argv[1], sys.argv[2]
    here = tree(None if over in ("", "shipped") else over)
    sys.path.insert(0, str(here))
    import ops
    from opt import reg
    lines = [tuple(x.split()) for x in open(prog, encoding="utf-8").read().splitlines() if x.strip()]
    r = reg.Reg()
    t0 = time.time()
    for t in lines:
        ops.ex(r, t)
    took = time.time() - t0
    print("%-28s %-14s %8.2f s  %d lines out" % (over, pathlib.Path(prog).name, took, len(r.out)),
          flush=True)
    if len(sys.argv) > 3:
        pathlib.Path(sys.argv[3]).write_text("\n".join(r.out) + "\n", encoding="utf-8", newline="\n")
    shutil.rmtree(here.parent, ignore_errors=True)


if __name__ == "__main__":
    main()
