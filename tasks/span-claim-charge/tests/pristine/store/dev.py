def setup(st):
    st.spot = {}
    st.atlist = []
    st.spare = 0
    if st.blocks:
        st.spot[0] = st.blocks
        st.atlist.append(0)
        st.spare = st.blocks


def give(st, at, wide):
    st.spare += wide
    tail = at + wide
    if tail in st.spot:
        wide += st.spot.pop(tail)
        st.atlist.remove(tail)
    st.spot[at] = wide
    i = 0
    while i < len(st.atlist) and st.atlist[i] < at:
        i += 1
    st.atlist.insert(i, at)


def take(st, want):
    for at in st.atlist:
        wide = st.spot[at]
        if wide >= want:
            del st.spot[at]
            st.atlist.remove(at)
            if wide > want:
                st.spot[at + want] = wide - want
                i = 0
                while i < len(st.atlist) and st.atlist[i] < at + want:
                    i += 1
                st.atlist.insert(i, at + want)
            st.spare -= want
            return [(at, want)]
    return None


def stat(st):
    if not st.atlist:
        return (0, 0, 0)
    big = 0
    for at in st.atlist:
        if st.spot[at] > big:
            big = st.spot[at]
    return (st.spare, len(st.atlist), big)
