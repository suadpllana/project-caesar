from . import grid, val


class State:
    def __init__(self, sheet):
        self.sheet = sheet
        self.vals = {}
        self.lays = {}
        self.busy = []
        self.mark = set()


def value(st, a):
    hit = st.vals.get(a)
    if hit is not None:
        return hit
    if a in st.mark:
        cut = st.busy.index(a)
        for b in st.busy[cut:]:
            st.vals[b] = grid.CYC
        return grid.CYC
    if not st.sheet.held(a):
        return grid.EMPTY
    st.busy.append(a)
    st.mark.add(a)
    try:
        out = val.run(st, st.sheet.node(a))
    finally:
        st.busy.pop()
        st.mark.discard(a)
    if a not in st.vals:
        st.vals[a] = out
    return st.vals[a]
