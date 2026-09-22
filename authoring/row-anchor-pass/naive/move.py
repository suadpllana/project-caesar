"""The event's own movement, the clamp, and whether the pane is resting at the foot.

The foot is read after the movement, not before it. A scroll upward out of the foot must not
snap back, and a jump onto the foot must follow it, and only the offset the event actually
left behind says which of those happened.
"""


def foot(total, vh):
    f = total - vh
    return f if f > 0 else 0


def clamp(off, total, vh):
    f = foot(total, vh)
    if off < 0:
        return 0
    if off > f:
        return f
    return off


def apply(gm, st, ev):
    kind = ev[0]
    if kind == "scroll":
        st.off += ev[1]
    elif kind == "go":
        st.off = ev[1]
    elif kind == "size":
        st.vh = ev[1]
    st.off = clamp(st.off, gm.total(), st.vh)
    st.foot = st.off == foot(gm.total(), st.vh)
