"""The plausible-but-wrong readings a solver actually arrives at, for tools/readingcheck.py.

These are not cheats. A cheat is a deliberate fake; these are honest misreadings that a
competent agent produced from the brief, and every one of them is taken from a real
trajectory or a real probe run rather than invented here.

The point of the file is the question the enumerated set cannot answer by inspection: does
a specific wrong reading survive all of it? On this task the answer was no for two of the
three, and the one that survived - `unmarked-absorbs` - passed all 27 enumerated cases and
failed only 6 of 300 generated programs, which is why the difficulty probe came back 0 of 8
with the agents believing they were finished.
"""

import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(ROOT, "tests"))

import cases
import gen
import harness

REFERENCE = os.path.join(ROOT, "solution")

_WALL = '''def wall(ch):
    out = []
    for g in reversed(ch):
        out.append(g)
        if g.sh:
            break
    return out
'''

READINGS = {
    # From the local probe, 2026-09-01. The agent's stops asked only "is anything visible
    # still marked", never "is this guard itself marked", so an unmarked guard absorbed a
    # cut that should have travelled past it and left with the fiber.
    "unmarked-absorbs": {
        "stop.py": _WALL + '''

def stops(g, ch, gg):
    for h in wall(ch):
        if h.hit:
            return False
    return True


def blend(old, new):
    return new
'''
    },
    # From the failing pipeline trajectory, 2026-09-01. "Errors are not marks" was read as
    # "an error marks nothing", so a child ending on an error did not stop its siblings.
    "error-spares-siblings": {
        "knot.py": '''def reap(bd, fid, t, pay):
    for p in pay:
        bd.errs.append((t, fid, p))
    return False


def wait(bd, g, left):
    return "hold"


def snag(bd, left):
    return True


def shut(bd, ch, g):
    if g is not None and g is not bd.gd:
        return ("cut", g)
    if bd.errs:
        return ("bun", [e[2] for e in sorted(bd.errs, key=lambda e: (e[0], e[1]))])
    return None
'''
    },
    # The retrieved cancellation-token answer: deliver to the innermost marked scope. This
    # is the intended difficulty rather than a defect, and it is here to confirm the
    # enumerated set pins it.
    "innermost-first": {
        "pick.py": _WALL + '''

def pick(f, ch):
    for g in wall(ch):
        if g.hit:
            return g
    return None
'''
    },
}

_TREES = {}


def _tree(policy):
    key = str(policy)
    if key not in _TREES:
        _TREES[key] = harness.tree(str(policy))
    return _TREES[key]


def run(policy, text):
    r = harness.safe(_tree(policy), text)
    return ([tuple(x) for x in r["tr"]], [(a, b, tuple(c)) for a, b, c in r["tk"]])


def enumerated():
    return [(n, cases.PROGS[n]) for n in sorted(cases.PROGS)]


def generated(n):
    return [(name, gen.text(p)) for name, p in gen.batch("readings", n)]


OPEN = {"G": "E", "B": "X", "A": "Z"}


def _match(lines):
    """opener index -> closer index, for the bracketed ops."""
    stack, pair = [], {}
    for i, ln in enumerate(lines):
        head = ln.split()[0] if ln.split() else ""
        if head in OPEN:
            stack.append((i, OPEN[head]))
        elif stack and head == stack[-1][1]:
            j, _ = stack.pop()
            pair[j] = i
    return pair


def reductions(text):
    """Structure-aware candidates, so the shrinker does not plateau on a bracketed language.

    Dropping the line that opens a region leaves its closer dangling and the program stops
    parsing, so a line-only shrinker stalls. Offering the three moves that keep a program
    well formed - unwrap a region, delete it whole, delete a procedure - takes the
    counterexample for `unmarked-absorbs` from 109 lines to 9.
    """
    lines = text.split("\n")
    pair = _match(lines)

    # whole procedures, biggest first
    heads = [i for i, ln in enumerate(lines) if ln.startswith(":")]
    for k in range(len(heads) - 1, -1, -1):
        a = heads[k]
        b = heads[k + 1] if k + 1 < len(heads) else len(lines)
        if len(heads) > 1:
            yield "\n".join(lines[:a] + lines[b:])

    # a region and everything in it
    for a in sorted(pair, reverse=True):
        yield "\n".join(lines[:a] + lines[pair[a] + 1:])

    # a region's brackets, keeping the body
    for a in sorted(pair, reverse=True):
        b = pair[a]
        yield "\n".join(lines[:a] + lines[a + 1:b] + lines[b + 1:])

    # any single unbracketed line
    for i in range(len(lines) - 1, -1, -1):
        head = lines[i].split()[0] if lines[i].split() else ""
        if head not in OPEN and head not in OPEN.values() and not lines[i].startswith(":"):
            yield "\n".join(lines[:i] + lines[i + 1:])
