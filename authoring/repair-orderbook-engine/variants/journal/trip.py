import bisect

from eng import hold


class Pen:
    def __init__(self):
        self.buys = []
        self.sells = []
        self.seq = 0
        self.ids = {}


def box(st):
    if st.arm is None:
        st.arm = Pen()
    return st.arm


def park(st, o, out):
    a = box(st)
    a.seq += 1
    a.ids[o.oid] = (a.seq, o)
    if o.side == "b":
        bisect.insort(a.buys, (o.trp, a.seq, o.oid))
    else:
        bisect.insort(a.sells, (-o.trp, a.seq, o.oid))
    out.row("arm", o.oid)


def drop(st, oid):
    a = box(st)
    held = a.ids.pop(oid, None)
    if held is None:
        return False
    seq, o = held
    if o.side == "b":
        a.buys.remove((o.trp, seq, oid))
    else:
        a.sells.remove((-o.trp, seq, oid))
    return True


def check(st, out):
    a = box(st)
    cut = bisect.bisect_right(a.buys, (st.last, float("inf"), 0))
    taken = a.buys[:cut]
    del a.buys[:cut]
    cut = bisect.bisect_right(a.sells, (-st.last, float("inf"), 0))
    taken += a.sells[:cut]
    del a.sells[:cut]
    fired = []
    for _, seq, oid in sorted(taken, key=lambda t: t[1]):
        _, o = a.ids.pop(oid)
        out.row("trp", oid)
        st.pend.append(o)
        hold.note_fired(seq, o)
        fired.append(o)
    return fired


def parked(st):
    a = box(st)
    return [a.ids[k][1] for k in sorted(a.ids)]
