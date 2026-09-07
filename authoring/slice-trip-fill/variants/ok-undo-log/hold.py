from eng import take, trip


class Hold:
    def __init__(self):
        self.rows = []

    def row(self, *cells):
        self.rows.append(cells)


class Void:
    def row(self, *cells):
        pass


def revive(side, px, r):
    r.live = True
    q = side.lv.get(px)
    if q is None:
        side.put(r)
    else:
        q.appendleft(r)


def undo(st, trail, o):
    for item in reversed(trail):
        kind = item[0]
        if kind == "fill":
            r, q = item[1], item[2]
            r.rem += q
            r.shn += q
            o.rem += q
        elif kind == "gone":
            revive(item[1], item[2], item[3])
        elif kind == "rot":
            side, px, r, was = item[1], item[2], item[3], item[4]
            r.shn = was
            q = side.lv[px]
            q.pop()
            q.appendleft(r)
        elif kind == "last":
            st.last = item[1]
        elif kind == "trip":
            for a in item[1]:
                trip.park(st, a, Void())


def admit(st, o, out):
    held = Hold()
    st.trail = []
    mark = len(st.pend)
    take.walk(st, o, held)
    trail, st.trail = st.trail, None
    if o.rem <= 0:
        for cells in held.rows:
            out.row(*cells)
        return
    while len(st.pend) > mark:
        st.pend.pop()
    undo(st, trail, o)
    out.row("pul", o.oid, "whole")
