"""A correct variant, one entry per block: the free map indexed by run length."""
import bisect


def setup(st):
    st.at2w = {}
    st.starts = []
    st.w2at = {}
    st.widths = []
    st.spare = 0
    if st.blocks:
        park(st, 0, st.blocks)
        st.spare = st.blocks


def park(st, at, wide):
    st.at2w[at] = wide
    bisect.insort(st.starts, at)
    seat = st.w2at.get(wide)
    if seat is None:
        st.w2at[wide] = [at]
        bisect.insort(st.widths, wide)
    else:
        bisect.insort(seat, at)


def unpark(st, at):
    wide = st.at2w.pop(at)
    st.starts.pop(bisect.bisect_left(st.starts, at))
    seat = st.w2at[wide]
    seat.pop(bisect.bisect_left(seat, at))
    if not seat:
        del st.w2at[wide]
        st.widths.pop(bisect.bisect_left(st.widths, wide))
    return wide


def give(st, at, wide):
    st.spare += wide
    tail = at + wide
    if tail in st.at2w:
        wide += unpark(st, tail)
    i = bisect.bisect_left(st.starts, at)
    if i:
        head = st.starts[i - 1]
        if head + st.at2w[head] == at:
            wide += unpark(st, head)
            at = head
    park(st, at, wide)


def take(st, want):
    if want > st.spare:
        return None
    st.spare -= want
    out = []
    left = want
    while left:
        i = bisect.bisect_left(st.widths, left)
        if i < len(st.widths):
            wide = st.widths[i]
            at = st.w2at[wide][0]
            unpark(st, at)
            out.append((at, left))
            if wide > left:
                park(st, at + left, wide - left)
            left = 0
        else:
            wide = st.widths[-1]
            at = st.w2at[wide][0]
            unpark(st, at)
            out.append((at, wide))
            left -= wide
    return out


def stat(st):
    if not st.widths:
        return (0, 0, 0)
    return (st.spare, len(st.starts), st.widths[-1])
