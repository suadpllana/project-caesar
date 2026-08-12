#!/usr/bin/env python3
"""The resume-point tests that calibrate the character meter.

The verifier does not compare the character count against a single number, because there
is no single number to compare it against. "Resume at the last position the merge table
protects" is a family of answers, not one answer: asking which characters never sit
anywhere but at the front of a symbol, asking which never sit anywhere but at the end of
one, taking either, and asking the finer question of which adjacent pairs no symbol
carries at all - every one of those is a correct reading, they protect nested sets of
positions, and they hand the tokenizer different numbers of characters on the same
scenarios. Grading equality against one of them would fail a solver who reasoned better
than the reference did, which is grading a choice rather than the work.

So the meter is a window. The floor comes from the sealed oracle - what the cheapest legal
resume of each render costs, searched for rather than derived, so the finest reading of the
table cannot come in under it. The ceiling comes from here: the most expensive of the
one-sided tests, which are the answers a solver settles on when they see one half of the
condition and not the other. Everything between the two is accepted.

The pair-level reading below sits on the floor on eleven of the twelve scenarios and three
characters above it on the twelfth, which is the measurement that says the floor is tight
rather than notional: reading the table as finely as it can be read is worth three
characters out of 2298 against knowing the answers in advance.

`REJECT` is what the ceiling has to stay clear of. Asking which characters take part in
no merge at all is the cheaper question and a strictly smaller set, and a loop built on it
walks back past resume points that were there; build_gt.py refuses to write a ground truth
whose ceiling has drifted up far enough to admit it.

Each entry is a replacement for the anchored block of the same name in
solution/ref/inc.py, applied by emit.py.
"""

from __future__ import annotations

# The block in solution/ref/inc.py these replace.
POINTS = """def _points():
    inner = set()
    mid = set()
    for a, b in core.MG:
        s = a + b
        inner.update(s[1:])
        mid.update(s[:-1])
    front = frozenset(c for c in core.BASE if c not in inner)
    back = frozenset(c for c in core.BASE if c not in mid)
    return front, back
"""

SAFE = """def safe(text, j):
    if j <= 0:
        return True
    if j < len(text) and text[j] in FRONT:
        return True
    return text[j - 1] in BACK
"""

FRONT_ONLY = """def _points():
    inner = set()
    for a, b in core.MG:
        inner.update((a + b)[1:])
    return frozenset(c for c in core.BASE if c not in inner), frozenset()
"""

BACK_ONLY = """def _points():
    mid = set()
    for a, b in core.MG:
        mid.update((a + b)[:-1])
    return frozenset(), frozenset(c for c in core.BASE if c not in mid)
"""

PAIR_POINTS = """def _points():
    pairs = set()
    for a, b in core.MG:
        s = a + b
        for i in range(len(s) - 1):
            pairs.add((s[i], s[i + 1]))
    return frozenset(pairs), frozenset()
"""

PAIR_SAFE = """def safe(text, j):
    if j <= 0:
        return True
    if j >= len(text):
        return True
    return (text[j - 1], text[j]) not in FRONT
"""

MERGE_FREE = """def _points():
    used = set()
    for a, b in core.MG:
        used.update(a + b)
    free = frozenset(c for c in core.BASE if c not in used)
    return free, free
"""

# The one-sided readings. The ceiling is the worst of these on each scenario, so a solver
# who found either half of the condition and stopped there is inside the window.
CEILING = {"front-only": {POINTS: FRONT_ONLY}, "back-only": {POINTS: BACK_ONLY}}

# The answer the ceiling has to stay clear of.
REJECT = {"merge-free": {POINTS: MERGE_FREE}}
