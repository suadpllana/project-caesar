import bisect


class Arm:
    def __init__(self):
        self.key = {"b": [], "s": []}
        self.row = {"b": [], "s": []}
        self.by = {}


def box(st):
    if st.arm is None:
        st.arm = Arm()
    return st.arm


def park(st, o, out):
    a = box(st)
    a.by[o.oid] = o
    k = o.trp if o.side == "b" else -o.trp
    i = bisect.bisect_right(a.key[o.side], k)
    a.key[o.side].insert(i, k)
    a.row[o.side].insert(i, o)
    out.row("arm", o.oid)


def drop(st, oid):
    a = box(st)
    o = a.by.pop(oid, None)
    if o is None:
        return False
    side = o.side
    i = a.row[side].index(o)
    del a.row[side][i]
    del a.key[side][i]
    return True


def check(st, out):
    a = box(st)
    hit = []
    for side in ("b", "s"):
        want = st.last if side == "b" else -st.last
        n = bisect.bisect_right(a.key[side], want)
        if n:
            hit.extend(a.row[side][:n])
            del a.row[side][:n]
            del a.key[side][:n]
    hit.sort(key=lambda x: x.oid)
    for o in hit:
        del a.by[o.oid]
        out.row("trp", o.oid)
        st.pend.append(o)
    return hit


def parked(st):
    a = box(st)
    return [a.by[k] for k in sorted(a.by)]
