"""Settling an open entry by taking the common kinds and throwing away the ones above others.

Every kind the sources all rise to is a candidate; a candidate with another candidate below it
is not the least one. Exactly one survivor is the settled kind, and anything else - none at
all, or two sitting side by side - leaves the entry unsettled.
"""
from res import kind


def settle(prog, sources):
    over = [k for k in prog.kinds
            if all(kind.steps(prog, s, k) is not None for s in sources)]
    least = [k for k in over
             if not any(o != k and kind.steps(prog, o, k) is not None for o in over)]
    return least[0] if len(least) == 1 else None
