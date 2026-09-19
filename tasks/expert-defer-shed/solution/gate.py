"""Ranking, and the want list that placement rewrites.

The ranking of a token never changes during a step, so it is computed once and kept. The want
list does change: every expert that refuses the token is struck out, and the shortest prefix
reaching the threshold is taken again over what is left, which is generally longer than before
because the scores that used to carry the prefix over the line are gone.
"""


def rank(weight):
    """Experts by score descending, ties to the smaller index."""
    return sorted(range(len(weight)), key=lambda e: (-weight[e], e))


def want(order, weight, w, out_of):
    """The shortest prefix of `order` minus `out_of` whose scores reach `w`.

    When what is left sums to less than the threshold the whole of it is wanted, which is the
    same rule read at its end rather than a separate case.
    """
    wl = []
    tot = 0
    for e in order:
        if e in out_of:
            continue
        wl.append(e)
        tot += weight[e]
        if tot >= w:
            break
    return wl
