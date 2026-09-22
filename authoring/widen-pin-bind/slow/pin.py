"""Settling the open kind of an entry that has not been pinned yet.

Every open slot contributes the kind its argument stands at, and the entry is settled at the
one kind all of them rise to that rises to every other kind all of them rise to. That is a
stronger demand than picking the nearest common one: where two common kinds sit side by side
with neither rising to the other, there is no answer and the entry drops out of the call.
"""
from res import kind


def settle(prog, sources):
    """The single least kind every source rises to, or None when there is not exactly one."""
    over = [k for k in prog.kinds
            if all(kind.steps(prog, s, k) is not None for s in sources)]
    for k in over:
        if all(kind.steps(prog, k, other) is not None for other in over):
            return k
    return None
