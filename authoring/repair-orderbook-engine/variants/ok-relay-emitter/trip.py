import heapq


class Arm:
    def __init__(self):
        self.bq = []
        self.sq = []
        self.by = {}
        self.seq = 0


def box(st):
    if st.arm is None:
        st.arm = Arm()
    return st.arm


def park(st, o, out):
    a = box(st)
    a.seq += 1
    a.by[o.oid] = o
    if o.side == "b":
        heapq.heappush(a.bq, (o.trp, a.seq, o))
    else:
        heapq.heappush(a.sq, (-o.trp, a.seq, o))
    out.row("arm", o.oid)


def drop(st, oid):
    a = box(st)
    return a.by.pop(oid, None) is not None


def check(st, out):
    a = box(st)
    hit = []
    while a.bq and a.bq[0][0] <= st.last:
        _, seq, o = heapq.heappop(a.bq)
        if a.by.pop(o.oid, None) is not None:
            hit.append((seq, o))
    while a.sq and -a.sq[0][0] >= st.last:
        _, seq, o = heapq.heappop(a.sq)
        if a.by.pop(o.oid, None) is not None:
            hit.append((seq, o))
    hit.sort(key=lambda x: x[0])
    fired = [o for _, o in hit]
    for o in fired:
        out.row("trp", o.oid)
        st.pend.append(o)
    return fired


def parked(st):
    a = box(st)
    return [a.by[k] for k in sorted(a.by)]
