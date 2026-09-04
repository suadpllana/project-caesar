"""The plausible-but-wrong readings, written down so they can be run.

Per-rule coverage is not coverage. The question is whether a SPECIFIC wrong
reading survives the whole enumerated set, and the only way to know is to write
that reading as the file it would replace and drive it. Three of these are the
readings this task exists to punish - the reach search that treats a difference
as if it constrained nothing, the readiness test that never notices a cell has
left the desk, and the one that lets everything which would be ready if the
others went leave together. All three produce a machine that behaves impeccably
on a straight set.
"""

import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
TASK = os.path.dirname(HERE)
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(TASK, "tests"))

import cases
import emit
import gen
import harness

REFERENCE = os.path.join(TASK, "solution")

_RIGS = {}


def _read(name):
    with open(os.path.join(REFERENCE, name)) as fh:
        return fh.read()


# The wrong readings ARE the single-mistake cheats, so there is one definition of
# them and it lives in emit.py. Keeping a second copy here is the same source in
# two places with nothing holding them equal, which is the defect the solution
# quality review objects to; it also drifts silently the moment an anchor moves.
READINGS = dict((name, dict((f, make()) for f, make in over.items()))
                for name, over in emit.MISTAKES.items())


def run(policy, text):
    key = str(policy)
    if key not in _RIGS:
        _RIGS[key] = harness.Rig(key)
    return _RIGS[key].run(text)


def enumerated():
    return [(name, cases.SETS[name]) for name in sorted(cases.SETS)]


def generated(n):
    return [("g%04d" % i, gen.one("reading:%d" % i)) for i in range(n)]


def reductions(text):
    """Structure-aware candidates: drop a script line, or a whole declaration.

    Dropping a run or a tag declaration means dropping every line that mentions
    it too, or the set stops parsing into anything the machine can drive.
    """
    lines = [ln for ln in text.split("\n") if ln.strip()]
    head = [ln for ln in lines if not _in_body(lines, ln)]
    for i, line in enumerate(lines):
        word = line.split()
        if not word:
            continue
        if word[0] in ("post", "tie", "bar", "shut"):
            yield "\n".join(lines[:i] + lines[i + 1:])
    for line in head:
        word = line.split()
        if word and word[0] in ("run", "tag"):
            who = word[1]
            keep = [ln for ln in lines if who not in ln.split()]
            if keep != lines:
                yield "\n".join(keep)
        if word and word[0] == "watch" and len(word) > 2:
            yield "\n".join([" ".join(word[:-1])] + lines[1:])


def _in_body(lines, line):
    at = lines.index(line)
    for i in range(at):
        if lines[i].strip() == "go":
            return True
    return False
