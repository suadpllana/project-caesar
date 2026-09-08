"""Whole-solver readings of the contract, for tools/readingcheck.py.

Each reading is the reference with one decision settled the other way - the same wrong readings
the cheat suite ships, minus the ones that are correct and merely too slow, which no comparison
of printouts can separate. The question this answers is not "is every rule covered" but "does
the enumerated set fail this specific plausible reading", and the only way to know is to run it.

The reading sources come from emit.py, so a reading here cannot drift from the cheat that
stands for it.
"""
import os
import sys

import emit
import harness

sys.path.insert(0, harness.TESTS)
import cases  # noqa: E402
import gen  # noqa: E402

REFERENCE = os.path.join(harness.TASK, "solution")

# Correct implementations that only fail the clock; a printed line never separates them.
TIMING = ("recompute", "subtree-walk", "big-shortcut")

_base = dict((p, open(os.path.join(REFERENCE, p)).read()) for p in emit.PARTS)

READINGS = {}
for _name, (_note, _pat) in emit.READINGS.items():
    if _name in TIMING:
        continue
    _files = {}
    for _part, _pairs in _pat.items():
        if isinstance(_pairs, str):
            _files[_part] = emit.whole(_pairs)
        else:
            _files[_part] = emit.patched(_base[_part], _pairs, "%s/%s" % (_name, _part))
    READINGS[_name] = _files

_trees = {}


def run(policy, text):
    tree = _trees.get(str(policy))
    if tree is None:
        tree = _trees[str(policy)] = harness.tree(policy=str(policy))
    script = [tuple(ln.split()) for ln in text.splitlines() if ln.strip()]
    try:
        return tuple(harness.run(tree, script))
    except Exception as exc:
        return ("raised", type(exc).__name__, str(exc)[:80])


def enumerated():
    return [(nm, "\n".join(cases.CASES[nm])) for nm in cases.ORDER]


def generated(n):
    per = max(1, n // 20)
    out = []
    for fam, nm, lines in gen.programs("readingprobe", per):
        if fam == "wide":
            continue
        out.append((nm, "\n".join(lines)))
    return out[:n]


def reductions(text):
    """Structure-aware shrinking: drop an operation, and drop a declaration nothing uses."""
    lines = [ln for ln in text.split("\n") if ln.strip()]
    for i in range(len(lines) - 1, -1, -1):
        if lines[i].split()[0] in ("space", "blob"):
            continue
        yield "\n".join(lines[:i] + lines[i + 1:])
    for i, ln in enumerate(lines):
        bits = ln.split()
        if bits[0] == "blob" and not any(bits[1] in x.split()[2:] for x in lines[i + 1:]):
            yield "\n".join(lines[:i] + lines[i + 1:])
