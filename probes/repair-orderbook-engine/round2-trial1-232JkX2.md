I'll start by reading the engine code and the sessions.

Bash(find . -type f | grep -v __pycache__ | sort && echo ---- && cat run_book.py && echo ---- && for f in eng/*.py;…)

./eng/__init__.py
./eng/hand.py
./eng/hold.py
./eng/shown.py
./eng/take.py
./eng/trip.py
./mkt/__init__.py
./mkt/bk.py
./mkt/drv.py
./mkt/ev.py
./mkt/rd.py
./run_book.py
./sess/book.txt
./sess/fill.txt
./sess/s1.txt
./sess/s2.txt
./sess/wide.txt
----
import sys

from mkt.drv import drive
from mkt.ev import Emit
from mkt.rd import read


def sink_for(rows):
    def put(row):
        if sys._getframe(1).f_code is not Emit.row.__code__:
            raise RuntimeError("sink")
        rows.append(row)
    return put


def main(argv):
    with open(argv[1]) as fh:
        cap, mark, msgs = read(fh.read())
    rows = []
    drive(cap, mark, msgs, sink_for(rows))
    for r in rows:
        print(" ".join(str(c) for c in r))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
----
=== eng/__init__.py
=== eng/hand.py
def blocks(o, r):
    return o.hand == r.hand
=== eng/hold.py
from eng import take


def room(st, o):
    opp = st.bk.opp(o.side)
    sign = 1 if o.side == "b" else -1
    got = 0
    for px in sorted(opp.lv, key=lambda p: sign * p):
        if o.px is not None and sign * (px - o.px) > 0:
            break
        if abs(px - st.last) > st.cap:
            break
        for r in opp.lv[px]:
            if r.live:
                got += r.rem
    return got


def admit(st, o, out):
    if room(st, o) >= o.rem:
        take.walk(st, o, out)
    if o.rem > 0:
        out.row("pul", o.oid, "whole")
=== eng/shown.py
def avail(r):
    return r.rem


def refill(side, r):
    r.shn = r.rem if r.shw is None else min(r.shw, r.rem)
    return r.shn
=== eng/take.py
from eng import hand, shown, trip


def walk(st, o, out):
    opp = st.bk.opp(o.side)
    sign = 1 if o.side == "b" else -1
    ref = st.last
    while o.rem > 0:
        px = opp.top()
        if px is None:
            break
        if o.px is not None and sign * (px - o.px) > 0:
            break
        if abs(px - ref) > st.cap:
            break
        r = opp.front(px)
        if r is None:
            continue
        if hand.blocks(o, r):
            r.live = False
            opp.take(px)
            out.row("pul", r.oid, "same")
            continue
        q = min(o.rem, shown.avail(r))
        out.row("trd", o.oid, r.oid, px, q)
        o.rem -= q
        r.rem -= q
        r.shn -= q
        st.last = px
        if r.rem <= 0:
            r.live = False
            opp.take(px)
        elif r.shn <= 0:
            out.row("shw", r.oid, shown.refill(opp, r))
    trip.check(st, out)
=== eng/trip.py
def box(st):
    if st.arm is None:
        st.arm = []
    return st.arm


def park(st, o, out):
    box(st).append(o)
    out.row("arm", o.oid)


def drop(st, oid):
    a = box(st)
    for i, o in enumerate(a):
        if o.oid == oid:
            del a[i]
            return True
    return False


def check(st, out):
    a = box(st)
    hit = []
    for o in a:
        if o.side == "b" and st.last >= o.trp:
            hit.append(o)
        elif o.side == "s" and st.last <= o.trp:
            hit.append(o)
    hit.sort(key=lambda x: (x.trp, x.oid))
    for o in hit:
        a.remove(o)
        out.row("trp", o.oid)
        st.pend.append(o)
    return hit


def parked(st):
    return sorted(box(st), key=lambda o: o.oid)

[stdout]
./eng/__init__.py
./eng/hand.py
./eng/hold.py
./eng/shown.py
./eng/take.py
./eng/trip.py
./mkt/__init__.py
./mkt/bk.py
./mkt/drv.py
./mkt/ev.py
./mkt/rd.py
./run_book.py
./sess/book.txt
./sess/fill.txt
./sess/s1.txt
./sess/s2.txt
./sess/wide.txt
----
import sys

from mkt.drv import drive
from mkt.ev import Emit
from mkt.rd import read


def sink_for(rows):
    def put(row):
        if sys._getframe(1).f_code is not Emit.row.__code__:
            raise RuntimeError("sink")
        rows.append(row)
    return put


def main(argv):
    with open(argv[1]) as fh:
        cap, mark, msgs = read(fh.read())
    rows = []
    drive(cap, mark, msgs, sink_for(rows))
    for r in rows:
        print(" ".join(str(c) for c in r))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
----
=== eng/__init__.py
=== eng/hand.py
def blocks(o, r):
    return o.hand == r.hand
=== eng/hold.py
from eng import take


def room(st, o):
    opp = st.bk.opp(o.side)
    sign = 1 if o.side == "b" else -1
    got = 0
    for px in sorted(opp.lv, key=lambda p: sign * p):
        if o.px is not None and sign * (px - o.px) > 0:
            break
        if abs(px - st.last) > st.cap:
            break
        for r in opp.lv[px]:
            if r.live:
                got += r.rem
    return got


def admit(st, o, out):
    if room(st, o) >= o.rem:
        take.walk(st, o, out)
    if o.rem > 0:
        out.row("pul", o.oid, "whole")
=== eng/shown.py
def avail(r):
    return r.rem


def refill(side, r):
    r.shn = r.rem if r.shw is None else min(r.shw, r.rem)
    return r.shn
=== eng/take.py
from eng import hand, shown, trip


def walk(st, o, out):
    opp = st.bk.opp(o.side)
    sign = 1 if o.side == "b" else -1
    ref = st.last
    while o.rem > 0:
        px = opp.top()
        if px is None:
            break
        if o.px is not None and sign * (px - o.px) > 0:
            break
        if abs(px - ref) > st.cap:
            break
        r = opp.front(px)
        if r is None:
            continue
        if hand.blocks(o, r):
            r.live = False
            opp.take(px)
            out.row("pul", r.oid, "same")
            continue
        q = min(o.rem, shown.avail(r))
        out.row("trd", o.oid, r.oid, px, q)
        o.rem -= q
        r.rem -= q
        r.shn -= q
        st.last = px
        if r.rem <= 0:
            r.live = False
            opp.take(px)
        elif r.shn <= 0:
            out.row("shw", r.oid, shown.refill(opp, r))
    trip.check(st, out)
=== eng/trip.py
def box(st):
    if st.arm is None:
        st.arm = []
    return st.arm


def park(st, o, out):
    box(st).append(o)
    out.row("arm", o.oid)


def drop(st, oid):
    a = box(st)
    for i, o in enum
… [clipped]
collapse
Bash(for f in mkt/*.py; do echo "=== $f"; cat $f; done; echo; for f in sess/s1.txt sess/s2.txt sess/fill.txt; do ec…)

=== mkt/__init__.py
=== mkt/bk.py
import heapq
from collections import deque


class Ord:
    __slots__ = ("oid", "hand", "side", "px", "rem", "shn", "shw",
                 "tif", "trp", "live")

    def __init__(self, oid, hand, side, px, qty, shw, tif, trp):
        self.oid = oid
        self.hand = hand
        self.side = side
        self.px = px
        self.rem = qty
        self.shw = shw
        self.shn = qty if shw is None else min(shw, qty)
        self.tif = tif
        self.trp = trp
        self.live = False


class Side:
    def __init__(self, sign):
        self.sign = sign
        self.lv = {}
        self.pq = []

    def put(self, o):
        q = self.lv.get(o.px)
        if q is None:
            q = self.lv[o.px] = deque()
            heapq.heappush(self.pq, self.sign * o.px)
        q.append(o)
        o.live = True

    def top(self):
        while self.pq:
            px = self.sign * self.pq[0]
            q = self.lv.get(px)
            if q is None:
                heapq.heappop(self.pq)
                continue
            while q and not q[0].live:
                q.popleft()
            if q:
                return px
            del self.lv[px]
            heapq.heappop(self.pq)
        return None

    def front(self, px):
        q = self.lv[px]
        while q and not q[0].live:
            q.popleft()
        return q[0] if q else None

    def take(self, px):
        self.lv[px].popleft()

    def rows(self):
        out = []
        for px in sorted(self.lv, key=lambda p: self.sign * p):
            for o in self.lv[px]:
                if o.live:
                    out.append(o)
        return out


class Bk:
    def __init__(self):
        self.b = Side(-1)
        self.s = Side(1)

    def own(self, side):
        return self.b if side == "b" else self.s

    def opp(self, side):
        return self.s if side == "b" else self.b
=== mkt/drv.py
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
=== mkt/ev.py
class Emit:
    def __init__(self, sink):
        self.sink = sink

    def row(self, *cells):
        self.sink(tuple(cells))
=== mkt/rd.py
from mkt.bk import Ord


def num(tok):
    return None if tok == "-" else int(tok)


def read(text):
    cap = 0
    mark = 0
    msgs = []
    for raw in text.splitlines():
        f = raw.split()
        if not f:
            continue
        if f[0] == "cap":
            cap = int(f[1])
        elif f[0] == "mark":
            mark = int(f[1])
        elif f[0] == "pace":
            msgs.append(("pace", f[1]))
        elif f[0] == "pull":
            msgs.append(("pull", int(f[1])))
        elif f[0] == "new":
            o = Ord(int(f[1]), int(f[2]), f[3], num(f[4]), int(f[5]),
                    num(f[6]), f[7], num(f[8]))
            msgs.append(("new", o))
        else:
            raise ValueError(raw)
    return cap, mark, msgs

=== sess/s1.txt
cap 6
mark 100
new 1 1 s 100 30 10 day -
new 2 2 s 100 25 - day -
new 3 3 b 100 60 - day -
=== sess/s2.txt
cap 3
mark 98
new 1 5 s 100 10 - day -
new 2 6 s 103 10 - day -
new 3 7 s 106 10 - day -
new 4 1 b 106 5 - day 104
new 5 8 b - 40 - day -
=== sess/fill.txt
pace fill
cap 4
mark 100
new 1 1 s 101 7 2 day -
new 2 2 s 103 5 2 day -
new 3 3 b 104 3 - whole 102
new 4 4 s 101 4 - day 101
new 5 5 b 104 9 - whole -
pull 2
cap 40
mark 1000
new 1 1 b 999 60 5 day -
new 2 2 s 1002 20 - day -
new 3 3 b 997 40 - day -
new 4 4 s 1004 60 8 day -
new 5 5 b 995 60 - day -
new 6 1 s 1006 40 5 day -
new 7 2 b 993 20 - day -
new 8 3 s 1008 60 - day -
new 9 4 b 991 20 8 day -
new 10 5 s 1001 60 8 day -
new 11 1 b 998 20 - day -
new 12 2 s 1003 40 - day -
new 13 3 b 996 60 - day -
new 14 4 s 1005 40 8 day -
new 15 5 b 994 20 5 day -
new 16 1 s 1007 20 - day -
new 17 2 b 992 40 - day -
new 18 3 s 1009 60 - day -
new 19 4 b 999 60 - day -
new 20 5 s 1002 40 - day -
new 21 1 b 997 40 5 day -
new 22 2 s 1004 20 5 day -
new 23 3 b 995 60 8 day -
new 24 4 s 1006 60 - day -
new 25 5 b 993 40 - day -
new 26 1 s 1008 60 - day -
new 27 2 b 991 20 - day -
new 28 3 s 1001 20 - day -
cap 40
mark 1000
new 1 1 b 997 10 - day -
new 2 2 s 1004 60 - day -
new 3 3 b 995 10 - day -
new 4 4 s 1006 20 - day -
new 5 5 b 993 30 4 day -
new 6 6 s 1008 60 7 day -
new 7 1 b 991 30 7 day -
new 8 2 s 1010 10 - day -
new 9 
… [clipped]
collapse
Thinking…
I now have the full picture of the frozen driver/book and the five engine files handling walk, shown-size, participant, whole-order and trip logic. I'll rewrite them with journal-based rollback for `whole` orders, per-fill trip checks, and heap-based parked sets.

Bash(cat > eng/hand.py <<'EOF' def blocks(o, r): return o.hand == r.hand EOF cat > eng/shown.py <<'EOF' from eng im…)

done

[stdout]
done
[metadata] {"noOutputExpected": false}
collapse
Fixing the `refill` signature mismatch: `shown.refill(side, r)` has no `st`, so I'll hang the frame stack on the book sides as well and let the side ops journal through it.

Bash(cat > eng/shown.py <<'EOF' from eng import hold def avail(r): return r.shn def refill(side, r): # r is the liv…)

== s1
rst 1 100 10
rst 2 100 25
trd 3 1 100 10
shw 1 10
trd 3 2 100 25
trd 3 1 100 10
shw 1 10
trd 3 1 100 10
rst 3 100 5
bk b 100 3 5 5
== s2
rst 1 100 10
rst 2 103 10
rst 3 106 10
arm 4
trd 5 1 100 10
trd 5 2 103 10
trd 5 3 106 10
trp 4
pul 5 mkt
rst 4 106 5
bk b 106 4 5 5
== fill
rst 1 101 2
rst 2 103 2
arm 3
arm 4
trd 5 1 101 2
trp 4
shw 1 2
rst 4 101 4
trd 5 1 101 2
shw 1 2
trd 5 4 101 4
trd 5 1 101 1
pul 2 user
bk s 101 1 1 2
am 3

[stdout]
== s1
rst 1 100 10
rst 2 100 25
trd 3 1 100 10
shw 1 10
trd 3 2 100 25
trd 3 1 100 10
shw 1 10
trd 3 1 100 10
rst 3 100 5
bk b 100 3 5 5
== s2
rst 1 100 10
rst 2 103 10
rst 3 106 10
arm 4
trd 5 1 100 10
trd 5 2 103 10
trd 5 3 106 10
trp 4
pul 5 mkt
rst 4 106 5
bk b 106 4 5 5
== fill
rst 1 101 2
rst 2 103 2
arm 3
arm 4
trd 5 1 101 2
trp 4
shw 1 2
rst 4 101 4
trd 5 1 101 2
shw 1 2
trd 5 4 101 4
trd 5 1 101 1
pul 2 user
bk s 101 1 1 2
am 3
[metadata] {"noOutputExpected": false}
collapse
s1, s2 and fill.txt now match the expected behaviour. Next: timing on the big sessions, plus hand-built sessions exercising whole-order failure and nesting.

Bash(for f in wide book; do /usr/bin/time -f "$f %es" python run_book.py sess/$f.txt | tail -3; done cat > /tmp/w1.…)

/bin/bash: line 26: /usr/bin/time: No such file or directory
/bin/bash: line 26: /usr/bin/time: No such file or directory
== w1 (pace order, whole fails then whole succeeds)
rst 1 100 2
rst 2 101 5
rst 3 102 3
arm 4
arm 5
pul 6 whole
trp 4
trp 5
rst 4 90 5
rst 5 110 4
trd 7 1 100 2
shw 1 2
trd 7 1 100 2
shw 1 1
trd 7 1 100 1
trd 7 2 101 2
bk b 90 4 5 5
bk s 101 2 3 3
bk s 102 3 3 3
bk s 110 5 4 4
== w2 (pace fill, nested)
rst 1 100 2
rst 2 101 5
rst 3 102 3
arm 4
arm 5
pul 6 whole
trp 4
trp 5
trd 4 1 100 2
shw 1 2
trd 4 1 100 2
shw 1 1
trd 4 1 100 1
trd 4 2 101 1
rst 5 99 4
trd 7 5 99 4
trd 7 2 101 3
bk s 101 2 1 1
bk s 102 3 3 3

[stdout]
/bin/bash: line 26: /usr/bin/time: No such file or directory
/bin/bash: line 26: /usr/bin/time: No such file or directory
== w1 (pace order, whole fails then whole succeeds)
rst 1 100 2
rst 2 101 5
rst 3 102 3
arm 4
arm 5
pul 6 whole
trp 4
trp 5
rst 4 90 5
rst 5 110 4
trd 7 1 100 2
shw 1 2
trd 7 1 100 2
shw 1 1
trd 7 1 100 1
trd 7 2 101 2
bk b 90 4 5 5
bk s 101 2 3 3
bk s 102 3 3 3
bk s 110 5 4 4
== w2 (pace fill, nested)
rst 1 100 2
rst 2 101 5
rst 3 102 3
arm 4
arm 5
pul 6 whole
trp 4
trp 5
trd 4 1 100 2
shw 1 2
trd 4 1 100 2
shw 1 1
trd 4 1 100 1
trd 4 2 101 1
rst 5 99 4
trd 7 5 99 4
trd 7 2 101 3
bk s 101 2 1 1
bk s 102 3 3 3
[metadata] {"noOutputExpected": false}
collapse
Both scenarios check out by hand. Now timing with bash's `time`, plus a nested-failure test where an inner `whole` fails inside an outer one that also fails.

Bash(cd /app; for f in wide book; do echo "== $f"; ( time python run_book.py sess/$f.txt | wc -l ) 2>&1 | grep -E "…)

== wide
233880
real	0m0.725s
== book
7594
real	0m0.088s
== w3
rst 1 100 2
rst 2 101 5
rst 3 102 3
arm 4
arm 5
rst 8 95 2
pul 6 whole
trp 4
trp 5
pul 4 whole
rst 5 99 4
bk b 95 8 2 2
bk s 99 5 4 4
bk s 100 1 2 5
bk s 101 2 5 5
bk s 102 3 3 3

[stdout]
== wide
233880
real	0m0.725s
== book
7594
real	0m0.088s
== w3
rst 1 100 2
rst 2 101 5
rst 3 102 3
arm 4
arm 5
rst 8 95 2
pul 6 whole
trp 4
trp 5
pul 4 whole
rst 5 99 4
bk b 95 8 2 2
bk s 99 5 4 4
bk s 100 1 2 5
bk s 101 2 5 5
bk s 102 3 3 3
[metadata] {"noOutputExpected": false}
collapse
Thinking…
All three big-scenario runs complete in under a second and the nested-failure trace matches the hand-derived result. Now I'll verify that a same-participant pull inside a failed `whole` gets reverted, and that pulling a parked order works correctly.

Bash(cd /app; cat > /tmp/w4.txt <<'EOF' cap 10 mark 100 new 1 6 s 100 5 2 day - new 2 2 s 101 5 - day - new 4 4 b 9…)

rst 1 100 2
rst 2 101 5
arm 4
pul 6 whole
trp 4
rst 4 90 5
pul 1 same
trd 7 2 101 3
pul 4 user
bk s 101 2 2 2

[stdout]
rst 1 100 2
rst 2 101 5
arm 4
pul 6 whole
trp 4
rst 4 90 5
pul 1 same
trd 7 2 101 3
pul 4 user
bk s 101 2 2 2
[metadata] {"noOutputExpected": false}
collapse
The engine is back. All of s1, s2 and fill.txt now produce the expected output, and the hand-built failure, nesting and same-participant sessions trace correctly.

**What was wrong**

- `shown.avail` returned the full remainder instead of the shown slice, so sliced orders handed over everything on one fill and never disclosed or moved to the back.
- `take.walk` measured the cap from the last price at the start of the walk instead of the live last price, so a walk stopped one level in.
- Trip checks ran once at the end of a walk, sorted by trip price and id instead of arrival order.
- `hold.admit` pre-computed room instead of walking, and had no rollback.

**What I changed, in the five allowed files only**

- `eng/take.py`: cap measured against the current last price. After every fill it sets the last price, calls `trip.check`, then removes or re-discloses the resting order, then under `pace fill` runs that fill's batch inline before resuming.
- `eng/shown.py`: `avail` returns the shown size. `refill` discloses the next slice and moves the order to the back of its level.
- `eng/hold.py`: `admit` pushes a frame that buffers rows and journals every book, order and last-price mutation. On success it flushes rows and merges the journal upward. On failure it undoes the journal, prints the cancellation, prints `trp` for every order fired at any depth in arrival order, and then queues them (`pace order`) or runs them inline (`pace fill`). Also holds `rest` and `run` for nested executions, since the driver's `rest` only runs at top level.
- `eng/trip.py`: parked orders kept in a dict plus two heaps keyed by trip price, so each fill's check costs only the orders that actually fire. Firings are never journaled, so they stay permanent across a rollback.
- `eng/hand.py`: unchanged, it was already right.

**Timing** on the shipped big sessions:

| session | time |
|---|---|
| wide.txt | 0.7 s |
| book.txt | 0.1 s |

Everything prints through `out.row`, and `run_book.py`'s sink check passes on all sessions.