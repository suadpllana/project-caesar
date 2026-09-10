"""Free space: the runs, and the two orders they have to be found in.

A run is a maximal stretch of free blocks. Allocation wants the smallest run that fits
(and the lowest of those, then the largest run when nothing fits), release wants the
neighbours of an address. Those are two different orders over the same runs, so both are
carried: `spot` maps a start to its length, `atlist` holds the starts in address order for
the backward neighbour, and `szlist` holds (length, start) so best fit is a bisection
rather than a scan. Runs only ever split at an allocation and merge at a release, so both
indexes are edited in place instead of rebuilt.
"""
import bisect


def setup(st):
    st.spot = {}
    st.atlist = []
    st.szlist = []
    st.spare = 0
    if st.blocks:
        _put(st, 0, st.blocks)
        st.spare = st.blocks


def _put(st, at, wide):
    st.spot[at] = wide
    bisect.insort(st.atlist, at)
    bisect.insort(st.szlist, (wide, at))


def _lift(st, at, wide):
    del st.spot[at]
    st.atlist.pop(bisect.bisect_left(st.atlist, at))
    st.szlist.pop(bisect.bisect_left(st.szlist, (wide, at)))


def total(st):
    return st.spare


def give(st, at, wide):
    """Return a span's blocks and merge with a free run on either side."""
    st.spare += wide
    tail = at + wide
    if tail in st.spot:
        w = st.spot[tail]
        _lift(st, tail, w)
        wide += w
    i = bisect.bisect_left(st.atlist, at)
    if i:
        head = st.atlist[i - 1]
        w = st.spot[head]
        if head + w == at:
            _lift(st, head, w)
            at = head
            wide += w
    _put(st, at, wide)


def take(st, want):
    """Best fit, ties to the lowest address; when nothing fits, largest run first."""
    if want > st.spare:
        return None
    st.spare -= want
    out = []
    left = want
    while left:
        i = bisect.bisect_left(st.szlist, (left, -1))
        if i < len(st.szlist):
            wide, at = st.szlist[i]
            _lift(st, at, wide)
            out.append((at, left))
            if wide > left:
                _put(st, at + left, wide - left)
            left = 0
        else:
            big = st.szlist[-1][0]
            wide, at = st.szlist[bisect.bisect_left(st.szlist, (big, -1))]
            _lift(st, at, wide)
            out.append((at, wide))
            left -= wide
    return out


def stat(st):
    if not st.szlist:
        return (0, 0, 0)
    return (st.spare, len(st.szlist), st.szlist[-1][0])
