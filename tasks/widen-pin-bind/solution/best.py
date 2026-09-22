"""Choosing between the trials that survived.

The rule is a comparison and not a total: an entry wins by being no worse than each other
survivor at every number of the vector and better at one of them. Two vectors that cross -
cheaper at one slot, dearer at another - leave neither able to beat the other, and the call is
ambiguous however the two totals compare. A single survivor wins with nothing to beat.
"""


def beats(a, b):
    """True when vector `a` is no worse than `b` everywhere and better somewhere."""
    return all(x <= y for x, y in zip(a, b)) and any(x < y for x, y in zip(a, b))


def winner(vecs):
    """The index of the vector that beats every other, or None when no vector does."""
    for i, a in enumerate(vecs):
        if all(beats(a, b) for j, b in enumerate(vecs) if j != i):
            return i
    return None
