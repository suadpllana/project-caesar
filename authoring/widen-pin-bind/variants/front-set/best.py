"""The survivors reduced by elimination rather than each being checked against all the others.

A candidate is struck out the moment something is found that is no worse than it everywhere
and better somewhere. One candidate left standing is the winner; none, or more than one, and
the call is ambiguous. That is the same rule read from the other end.
"""


def beats(a, b):
    better = False
    for x, y in zip(a, b):
        if x > y:
            return False
        if x < y:
            better = True
    return better


def winner(vecs):
    live = []
    for i, a in enumerate(vecs):
        if not any(beats(b, a) for j, b in enumerate(vecs) if j != i):
            live.append(i)
    if len(live) != 1:
        return None
    one = live[0]
    if any(not beats(vecs[one], b) for j, b in enumerate(vecs) if j != one):
        return None
    return one
