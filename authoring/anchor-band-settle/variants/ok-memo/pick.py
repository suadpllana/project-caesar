"""The pick for the ok-memo variant, written as an explicit stack instead of recursion."""
from view import lay, stick


def first(v, s, band):
    u, w = s + band, s + v.vh
    if u >= w:
        return None
    # Each entry is (owner, index of the next child to look at, the partly showing box whose
    # children these are). Coming back up to a partly showing box with nothing taken inside it
    # takes that box.
    i, _base = lay.first_reaching(v, None, u)
    stack = [(None, i, None)]
    while stack:
        owner, i, partial = stack.pop()
        kids = v.kids if owner is None else owner.kids
        at, _index, _run = lay.offsets(v, owner)
        base = lay.begin(v, owner)
        took = None
        while i < len(kids):
            k = kids[i]
            y = base + at[i]
            if y >= w:
                break
            i += 1
            if lay.contribution(v, k) == 0 or k.live:
                continue
            if stick.where(v, k, s) is not None:
                continue
            if y >= u and y + lay.height(v, k) <= w:
                return k
            if k.shut:
                return k
            stack.append((owner, i, partial))
            j, _b = lay.first_reaching(v, k, u)
            stack.append((k, j, k))
            took = "descended"
            break
        if took is None and partial is not None:
            return partial
    return None
