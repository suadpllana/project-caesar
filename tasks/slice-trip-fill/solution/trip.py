import heapq


class Arm:
    def __init__(self):
        self.bq = []
        self.sq = []
        self.by = {}


def box(st):
    if st.arm is None:
        st.arm = Arm()
    return st.arm


def park(st, o, out):
    a = box(st)
    a.by[o.oid] = o
    if o.side == "b":
        heapq.heappush(a.bq, (o.trp, o.oid, o))
    else:
        heapq.heappush(a.sq, (-o.trp, o.oid, o))
    out.row("arm", o.oid)


def drop(st, oid):
    a = box(st)
    return a.by.pop(oid, None) is not None


def check(st, out):
    a = box(st)
    hit = []
    while a.bq and a.bq[0][0] <= st.last:
        o = heapq.heappop(a.bq)[2]
        if a.by.pop(o.oid, None) is not None:
            hit.append(o)
    while a.sq and -a.sq[0][0] >= st.last:
        o = heapq.heappop(a.sq)[2]
        if a.by.pop(o.oid, None) is not None:
            hit.append(o)
    hit.sort(key=lambda x: x.oid)
    for o in hit:
        out.row("trp", o.oid)
        st.pend.append(o)
    return hit


def parked(st):
    a = box(st)
    return [a.by[k] for k in sorted(a.by)]
