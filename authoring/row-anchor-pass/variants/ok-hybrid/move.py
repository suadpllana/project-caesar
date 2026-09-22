"""Correct variant: the clamp as a pair of min/max, the foot read after the movement."""


def foot(total, vh):
    return max(0, total - vh)


def clamp(off, total, vh):
    return min(max(0, off), foot(total, vh))


def apply(gm, st, ev):
    kind = ev[0]
    if kind == "scroll":
        st.off = st.off + ev[1]
    elif kind == "go":
        st.off = ev[1]
    elif kind == "size":
        st.vh = ev[1]
    st.off = clamp(st.off, gm.total(), st.vh)
    st.foot = st.off == foot(gm.total(), st.vh)
