"""Correct, and the way it reads: pick the best fit by looking at every run."""
import bisect


def setup(st):
    st.spot = {}
    st.atlist = []
    st.spare = 0
    if st.blocks:
        st.spot[0] = st.blocks
        bisect.insort(st.atlist, 0)
        st.spare = st.blocks


def total(st):
    return st.spare


def _lift(st, at):
    wide = st.spot.pop(at)
    st.atlist.pop(bisect.bisect_left(st.atlist, at))
    return wide


def _put(st, at, wide):
    st.spot[at] = wide
    bisect.insort(st.atlist, at)


def give(st, at, wide):
    st.spare += wide
    tail = at + wide
    if tail in st.spot:
        wide += _lift(st, tail)
    i = bisect.bisect_left(st.atlist, at)
    if i:
        head = st.atlist[i - 1]
        if head + st.spot[head] == at:
            wide += _lift(st, head)
            at = head
    _put(st, at, wide)


def take(st, want):
    if want > st.spare:
        return None
    st.spare -= want
    out = []
    left = want
    while left:
        best = None
        big = None
        for at in st.atlist:
            wide = st.spot[at]
            if wide >= left and (best is None or wide < best[0]):
                best = (wide, at)
            if big is None or wide > big[0]:
                big = (wide, at)
        if best is not None:
            wide, at = best
            _lift(st, at)
            out.append((at, left))
            if wide > left:
                _put(st, at + left, wide - left)
            left = 0
        else:
            wide, at = big
            _lift(st, at)
            out.append((at, wide))
            left -= wide
    return out


def stat(st):
    if not st.atlist:
        return (0, 0, 0)
    big = 0
    for at in st.atlist:
        if st.spot[at] > big:
            big = st.spot[at]
    return (st.spare, len(st.atlist), big)
