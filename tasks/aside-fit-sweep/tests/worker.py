"""Runs the submitted allocator. Unprivileged, sandboxed, and trusted for nothing.

This is the only stage that executes agent code, so it decides nothing: it stages a pristine copy
of the tree, drops the five submitted files into it, runs every graded program, and writes down
what came out. The grader treats this file's output as hostile input. A crash, a hang, or a silent
exit loses the record, and a lost record is a failure, never a pass.

The wall clock the platform puts on this process is also the task's execution limit, so an
allocator that answers every request correctly and cannot get through the set in time is scored
exactly as a wrong one is. Two of the twelve families exist for that: one where the leftmost
address a request fits at sits past thousands of parts of small holes, and one where the aside
list is driven past its bound tens of thousands of times.
"""
import hashlib
import json
import os
import pathlib
import shutil
import sys
import tempfile
import traceback

TESTS = os.environ.get("AFS_TESTS", "/tests")
sys.path.insert(0, TESTS)

import cases  # noqa: E402
import gen  # noqa: E402

WORK = pathlib.Path(os.environ.get("AFS_WORK", "/work"))
SENT = pathlib.Path(os.environ.get("AFS_SUB", "/app/pool"))
PRISTINE = pathlib.Path(TESTS) / "pristine"
PARTS = ("find.py", "cut.py", "side.py", "back.py", "edge.py")


def sig(lines):
    return hashlib.sha256("\n".join(lines).encode("utf-8")).hexdigest()


def tree():
    """A fresh copy of the shipped tree with the submitted pool files laid over it."""
    room = pathlib.Path(tempfile.mkdtemp(dir=str(WORK)))
    here = room / "app"
    shutil.copytree(PRISTINE, here)
    for part in PARTS:
        one = SENT / part
        if one.is_file():
            shutil.copy(one, here / "pool" / part)
    return here


def main():
    out = sys.argv[sys.argv.index("--out") + 1]
    seed = (WORK / "nonce").read_text(encoding="utf-8").strip()
    per = int((WORK / "per").read_text(encoding="utf-8").strip())

    here = tree()
    sys.path.insert(0, str(here))
    import ops
    from reg import live, text

    work = [("hand", name, cases.ops(name)) for name in cases.ORDER]
    work += gen.programs(seed, per)

    recs = []
    for fam, name, lines in work:
        got, err = None, None
        try:
            span, part, body = text.parse(lines)
            h = live.Pool(span, part)
            acc = []
            for line in body:
                ops.ex(h, tuple(line.split()), acc)
            got = acc
        except Exception:
            err = traceback.format_exc(limit=1).strip().splitlines()[-1:]
        recs.append({"fam": fam, "name": name, "sig": sig(lines), "got": got, "err": err})

    pathlib.Path(out).write_text(json.dumps(recs), encoding="utf-8")


if __name__ == "__main__":
    main()
