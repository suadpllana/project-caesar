"""Free space, indexed by run length instead of by a sorted list of pairs.

`bysize` maps a run length to the starts that have it and `sizes` keeps the distinct
lengths in order, so best fit is a bisection over the lengths and the lowest address of the
winning length is the head of its list. Release still needs the address order, which
`atlist` carries. Same contract as the reference, a different index for it.
"""
import bisect


def setup(st):
    st.spot = {}
    st.atlist = []
    st.bysize = {}
    st.sizes = []
    st.spare = 0
    if st.blocks:
        _put(st, 0, st.blocks)
        st.spare = st.blocks


def _put(st, at, wide):
    st.spot[at] = wide
    bisect.insort(st.atlist, at)
    seat = st.bysize.get(wide)
    if seat is None:
        st.bysize[wide] = [at]
        bisect.insort(st.sizes, wide)
    else:
        bisect.insort(seat, at)


def _lift(st, at):
    wide = st.spot.pop(at)
    st.atlist.pop(bisect.bisect_left(st.atlist, at))
    seat = st.bysize[wide]
    seat.pop(bisect.bisect_left(seat, at))
    if not seat:
        del st.bysize[wide]
        st.sizes.pop(bisect.bisect_left(st.sizes, wide))
    return wide


def total(st):
    return st.spare


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
        i = bisect.bisect_left(st.sizes, left)
        if i < len(st.sizes):
            wide = st.sizes[i]
            at = st.bysize[wide][0]
            _lift(st, at)
            out.append((at, left))
            if wide > left:
                _put(st, at + left, wide - left)
            left = 0
        else:
            wide = st.sizes[-1]
            at = st.bysize[wide][0]
            _lift(st, at)
            out.append((at, wide))
            left -= wide
    return out


def stat(st):
    if not st.sizes:
        return (0, 0, 0)
    return (st.spare, len(st.spot), st.sizes[-1])
