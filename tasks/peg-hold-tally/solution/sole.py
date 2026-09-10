"""The tally.

Carried, not counted: a block joins one peg's tally when it comes to have one run whose ends
coincide and no volume holding it, and leaves again when either changes.
"""


def count(a, p):
    return a.sole.get(p, 0)
