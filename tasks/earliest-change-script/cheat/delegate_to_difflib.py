"""Deliberate cheating attempt. NEVER executed by the pipeline.

Strategy: the shortest route a cold reading of the instruction suggests. The
standard library already ships a sequence matcher, the task is obviously a
diff, so hand the whole thing over and reshape the opcodes into the pairs the
instruction asks for. It costs eight lines and no thought at all, and on the
kind of input a person types out to check -- a file of distinct lines with a
couple of edits -- it returns exactly what the rule demands.

The verifier rejects it for three separate reasons. The matcher is not obliged
to produce a shortest script and frequently does not; where it does, it makes
no attempt to keep the moves in as few hunks as possible; and where it happens
to do that too, it resolves what is left by its own longest-block-first habit
rather than by the reading order stated here. Against a distribution built
from two to six distinct lines those disagreements are not rare, they are the
norm.
"""

import difflib


def changes(before, after):
    matcher = difflib.SequenceMatcher(a=before, b=after, autojunk=False)
    ops = []
    for tag, i1, i2, j1, j2 in matcher.get_opcodes():
        if tag in ("delete", "replace"):
            ops.extend(("-", i) for i in range(i1, i2))
        if tag in ("insert", "replace"):
            ops.extend(("+", j) for j in range(j1, j2))
    return ops
