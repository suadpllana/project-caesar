from collections import deque

from eng import hold, take, trip
from mkt.bk import Bk
from mkt.ev import Emit


class St:
    def __init__(self, cap, mark):
        self.cap = cap
        self.last = mark
        self.bk = Bk()
        self.pend = deque()
        self.arm = None
        self.pace = "order"


def rest(st, o, out):
    if o.rem <= 0:
        return
    if o.px is None:
        out.row("pul", o.oid, "mkt")
        return
    if o.tif == "part":
        out.row("pul", o.oid, "part")
        return
    o.shn = o.rem if o.shw is None else min(o.shw, o.rem)
    st.bk.own(o.side).put(o)
    out.row("rst", o.oid, o.px, o.shn)


def submit(st, o, out):
    if o.tif == "whole":
        hold.admit(st, o, out)
    else:
        take.walk(st, o, out)
        rest(st, o, out)


def drive(cap, mark, msgs, sink):
    out = Emit(sink)
    st = St(cap, mark)
    live = {}
    for kind, body in msgs:
        if kind == "pace":
            st.pace = body
            continue
        if kind == "pull":
            if trip.drop(st, body):
                out.row("pul", body, "user")
            else:
                o = live.get(body)
                if o is not None and o.live:
                    o.live = False
                    out.row("pul", body, "user")
            continue
        o = body
        live[o.oid] = o
        if o.trp is not None:
            trip.park(st, o, out)
            continue
        submit(st, o, out)
        while st.pend:
            submit(st, st.pend.popleft(), out)
    dump(st, out)
    return st


def dump(st, out):
    for side in ("b", "s"):
        for o in st.bk.own(side).rows():
            out.row("bk", side, o.px, o.oid, o.shn, o.rem)
    for o in trip.parked(st):
        out.row("am", o.oid)
