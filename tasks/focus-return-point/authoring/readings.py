"""The wrong readings, for tools/readingcheck.py: each is the reference with one rule
read the way a solver who missed it would read it. They are the same swaps emit.py turns
into cheats, so the two cannot drift."""

import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
TASK = os.path.dirname(HERE)
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(TASK, "tests"))

import emit  # noqa: E402
import harness  # noqa: E402

REFERENCE = os.path.join(TASK, "solution")


def _readings():
    out = {}
    for name, fn, old, new, _why in emit.SWAPS:
        files = emit.refset()
        emit.swap(files, name, fn, old, new)
        if name in emit.ANCHOR_FIX:
            emit.swap(files, name, fn, *emit.ANCHOR_FIX[name])
        out[name] = {fn: files[fn]}
    return out


READINGS = _readings()


def run(policy, text):
    return harness.run_inproc(str(policy), text)


def enumerated():
    import cases
    return sorted(cases.CASES.items())


def generated(n):
    import gen
    return gen.batch("readings", n)


def reductions(text):
    """Drop one event line at a time (never a declaration), last first."""
    lines = text.rstrip("\n").split("\n")
    for i in range(len(lines) - 1, -1, -1):
        if lines[i].startswith(("screen ", "w ")):
            continue
        yield "\n".join(lines[:i] + lines[i + 1:]) + "\n"
