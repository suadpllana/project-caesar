from . import form, grid, lay, val


class State:
    def __init__(self, sheet):
        self.sheet = sheet
        self.vals = {}
        self.cover = {}
        self.busy = set()
        self.done = False


def prime(st):
    if st.done:
        return
    st.done = True
    st.vals = sweep(st)
    st.cover = lay.spread(st)
    st.vals = sweep(st)


def sweep(st):
    st.vals = {}
    st.busy = set()
    for a in st.sheet.owners():
        need(st, a)
    return st.vals


def need(st, a):
    if a in st.vals:
        return st.vals[a]
    if a in st.busy:
        st.vals[a] = grid.CYC
        return grid.CYC
    if not st.sheet.held(a):
        return grid.EMPTY
    st.busy.add(a)
    node = st.sheet.node(a)
    for b in form.refs(node):
        if st.sheet.held(b) and b != a:
            need(st, b)
    out = val.run(st, node)
    st.busy.discard(a)
    if a not in st.vals:
        st.vals[a] = out
    return st.vals[a]


def reach(st, a):
    if a in st.cover:
        o, k = st.cover[a]
        v = st.vals.get(o)
        if grid.is_blk(v):
            return v[3][k]
    if not st.sheet.held(a):
        return grid.EMPTY
    v = need(st, a)
    if grid.is_blk(v):
        return grid.BLK
    if grid.is_set(v):
        return grid.REF
    return v


def frame(st, lo, hi):
    r0, r1 = min(lo[0], hi[0]), max(lo[0], hi[0])
    c0, c1 = min(lo[1], hi[1]), max(lo[1], hi[1])
    out = []
    for r in range(r0, r1 + 1):
        for c in range(c0, c1 + 1):
            out.append(reach(st, (r, c)))
    return grid.bag(r1 - r0 + 1, c1 - c0 + 1, out)
