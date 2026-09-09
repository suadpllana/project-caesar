I'll start by reading the engine and the sessions to see how the pieces fit together.

Bash(ls -R | head -50 && wc -l eng/*.py run_book.py && cat run_book.py && cat eng/*.py)

.:
eng
mkt
run_book.py
sess

./eng:
__init__.py
hand.py
hold.py
shown.py
take.py
trip.py

./mkt:
__init__.py
bk.py
drv.py
ev.py
rd.py

./sess:
book.txt
fill.txt
s1.txt
s2.txt
wide.txt
   0 eng/__init__.py
   2 eng/hand.py
  23 eng/hold.py
   7 eng/shown.py
  35 eng/take.py
  38 eng/trip.py
  27 run_book.py
 132 total
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
def blocks(o, r):
    return o.hand == r.hand
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
def avail(r):
    return r.rem


def refill(side, r):
    r.shn = r.rem if r.shw is None else min(r.shw, r.rem)
    return r.shn
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
.:
eng
mkt
run_book.py
sess

./eng:
__init__.py
hand.py
hold.py
shown.py
take.py
trip.py

./mkt:
__init__.py
bk.py
drv.py
ev.py
rd.py

./sess:
book.txt
fill.txt
s1.txt
s2.txt
wide.txt
   0 eng/__init__.py
   2 eng/hand.py
  23 eng/hold.py
   7 eng/shown.py
  35 eng/take.py
  38 eng/trip.py
  27 run_book.py
 132 total
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
def blocks(o, r):
    return o.hand == r.hand
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
def avail(r):
    return r.rem


def refill(side, r):
    r.shn = r.rem if r.shw is None else min(r.shw, r.rem)
    return r.shn
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
            return T
… [clipped]
collapse
Bash(cat mkt/*.py && cat sess/s1.txt sess/s2.txt sess/fill.txt && head -20 sess/wide.txt && head -5 sess/book.txt &…)

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
class Emit:
    def __init__(self, sink):
        self.sink = sink

    def row(self, *cells):
        self.sink(tuple(cells))
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
cap 6
mark 100
new 1 1 s 100 30 10 day -
new 2 2 s 100 25 - day -
new 3 3 b 100 60 - day -
cap 3
mark 98
new 1 5 s 100 10 - day -
new 2 6 s 103 10 - day -
new 3 7 s 106 10 - day -
new 4 1 b 106 5 - day 104
new 5 8 b - 40 - day -
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
cap 40
mark 1000
new 1 1 b 997 10 - day -
new 2 2 s 1004 60 - day -
new 3 3 b 995 10 - day -
  4136 sess/book.txt
     9 sess/fill.txt
     5 sess/s1.txt
     7 sess/s2.txt
  4297 sess/wide.txt
  8454 total

[stdout]
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
        self.shn = qty if shw is No
… [clipped]
collapse
Thinking…
Found five bugs: `avail` exposing the full remainder instead of the slice, refill not requeueing orders, the walk comparing against the starting price instead of the latest fill, trips being checked/sorted only at the end, and `whole` lacking rollback after its pre-count. I'll rewrite the five files, adding an undo journal for `whole` and buffered output.

Bash({"command":"cat > eng/shown.py <<'EOF'\nfrom eng import hold\n\n\ndef avail(r):\n return r.shn\n\n\ndef refill…)

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
The three small sessions now match the described behaviour. The journal hooks rebinding globals is uglier than needed, so I'll simplify to a module-level frame stack, then time the two big sessions.

Bash(cat > eng/hold.py <<'EOF' import heapq from collections import deque from eng import hand, take # Undo journal…)

514cd80c59ad192eec2c27aafb886e0e  -
6db458a931a6089309367d3d299258bc  -
c91c06e92ddbc5704f8e26469cd32aee  -
== wide
real	0m16.226s
233880 /tmp/wide.out
0
112692
== book
real	0m0.090s
7594 /tmp/book.out
144
648

[stdout]
514cd80c59ad192eec2c27aafb886e0e  -
6db458a931a6089309367d3d299258bc  -
c91c06e92ddbc5704f8e26469cd32aee  -
== wide
real	0m16.226s
233880 /tmp/wide.out
0
112692
== book
real	0m0.090s
7594 /tmp/book.out
144
648
[metadata] {"noOutputExpected": false}
collapse
The correctness looks right on the samples, but wide.txt takes 16 seconds and the graded input is three times larger, so I'll profile before touching anything else.

Bash(python3 -m cProfile -s cumtime run_book.py sess/wide.txt 2>&1 | grep -A25 'Ordered by' | head -40; grep -c '^n…)

Ordered by: cumulative time

   ncalls  tottime  percall  cumtime  percall filename:lineno(function)
     13/1    0.000    0.000   18.440   18.440 {built-in method builtins.exec}
        1    0.008    0.008   18.440   18.440 run_book.py:1(<module>)
        1    0.117    0.117   18.419   18.419 run_book.py:16(main)
        1    0.002    0.002   17.733   17.733 drv.py:40(drive)
       94    0.000    0.000   17.716    0.188 drv.py:32(submit)
       94    0.473    0.005   17.715    0.188 take.py:13(walk)
   112692   16.356    0.000   16.369    0.000 trip.py:24(check)
   234014    0.199    0.000    0.445    0.000 {method 'join' of 'str' objects}
   233880    0.103    0.000    0.386    0.000 ev.py:5(row)
   112663    0.176    0.000    0.290    0.000 shown.py:8(refill)
   233880    0.193    0.000    0.283    0.000 run_book.py:9(put)
  1152732    0.247    0.000    0.247    0.000 run_book.py:22(<genexpr>)
   233880    0.106    0.000    0.106    0.000 {built-in method builtins.print}
   112766    0.065    0.000    0.090    0.000 bk.py:36(top)
   225451    0.078    0.000    0.078    0.000 {built-in method builtins.min}
   242691    0.046    0.000    0.046    0.000 {method 'append' of 'list' objects}
   233880    0.046    0.000    0.046    0.000 {built-in method sys._getframe}
   112686    0.030    0.000    0.030    0.000 {method 'popleft' of 'collections.deque' objects}
   112692    0.027    0.000    0.027    0.000 bk.py:51(front)
   112930    0.025    0.000    0.025    0.000 {method 'get' of 'dict' objects}
   112737    0.022    0.000    0.022    0.000 {method 'append' of 'collections.deque' objects}
   112694    0.018    0.000    0.018    0.000 {built-in method builtins.abs}
        1    0.011    0.011    0.017    0.017 rd.py:8(read)
4200
1
0
4199

[stdout]
   Ordered by: cumulative time

   ncalls  tottime  percall  cumtime  percall filename:lineno(function)
     13/1    0.000    0.000   18.440   18.440 {built-in method builtins.exec}
        1    0.008    0.008   18.440   18.440 run_book.py:1(<module>)
        1    0.117    0.117   18.419   18.419 run_book.py:16(main)
        1    0.002    0.002   17.733   17.733 drv.py:40(drive)
       94    0.000    0.000   17.716    0.188 drv.py:32(submit)
       94    0.473    0.005   17.715    0.188 take.py:13(walk)
   112692   16.356    0.000   16.369    0.000 trip.py:24(check)
   234014    0.199    0.000    0.445    0.000 {method 'join' of 'str' objects}
   233880    0.103    0.000    0.386    0.000 ev.py:5(row)
   112663    0.176    0.000    0.290    0.000 shown.py:8(refill)
   233880    0.193    0.000    0.283    0.000 run_book.py:9(put)
  1152732    0.247    0.000    0.247    0.000 run_book.py:22(<genexpr>)
   233880    0.106    0.000    0.106    0.000 {built-in method builtins.print}
   112766    0.065    0.000    0.090    0.000 bk.py:36(top)
   225451    0.078    0.000    0.078    0.000 {built-in method builtins.min}
   242691    0.046    0.000    0.046    0.000 {method 'append' of 'list' objects}
   233880    0.046    0.000    0.046    0.000 {built-in method sys._getframe}
   112686    0.030    0.000    0.030    0.000 {method 'popleft' of 'collections.deque' objects}
   112692    0.027    0.000    0.027    0.000 bk.py:51(front)
   112930    0.025    0.000    0.025    0.000 {method 'get' of 'dict' objects}
   112737    0.022    0.000    0.022    0.000 {method 'append' of 'collections.deque' objects}
   112694    0.018    0.000    0.018    0.000 {built-in method builtins.abs}
        1    0.011    0.011    0.017    0.017 rd.py:8(read)
4200
1
0
4199
[metadata] {"noOutputExpected": false}
collapse
Thinking…
I'll replace the per-fill scan with two heaps indexed by trigger price, preserving arrival order for batch processing, and update the rollback path to rebuild that index.

Bash(cat > eng/trip.py <<'EOF' import heapq from eng import hold class Ix: """Index over the parked set: heaps by t…)

514cd80c59ad192eec2c27aafb886e0e  -
e37ed70ca9e7f05569c23c063ee6248f  -
c91c06e92ddbc5704f8e26469cd32aee  -
== wide
real	0m0.726s
same
== book
real	0m0.104s
same

[stdout]
514cd80c59ad192eec2c27aafb886e0e  -
e37ed70ca9e7f05569c23c063ee6248f  -
c91c06e92ddbc5704f8e26469cd32aee  -
== wide
real	0m0.726s
same
== book
real	0m0.104s
same
[metadata] {"noOutputExpected": false}
collapse
Bash(python3 run_book.py sess/s2.txt)

rst 1 100 10
rst 2 103 10
rst 3 106 10
arm 4
trd 5 1 100 10
trd 5 2 103 10
trd 5 3 106 10
trp 4
trp 4
pul 5 mkt
rst 4 106 5
rst 4 106 5
bk b 106 4 5 5
bk b 106 4 5 5

[stdout]
rst 1 100 10
rst 2 103 10
rst 3 106 10
arm 4
trd 5 1 100 10
trd 5 2 103 10
trd 5 3 106 10
trp 4
trp 4
pul 5 mkt
rst 4 106 5
rst 4 106 5
bk b 106 4 5 5
bk b 106 4 5 5
[metadata] {"noOutputExpected": false}
collapse
The `arm` index gets built after the order is appended, so the first parked order enters twice. Fix by building the index before appending.

Bash(python3 - <<'EOF' p='eng/trip.py'; s=open(p).read() s=s.replace(""" box(st).append(o) _push(_ix(st), o) """,""…)

514cd80c59ad192eec2c27aafb886e0e  -
6db458a931a6089309367d3d299258bc  -
c91c06e92ddbc5704f8e26469cd32aee  -
same
same

[stdout]
514cd80c59ad192eec2c27aafb886e0e  -
6db458a931a6089309367d3d299258bc  -
c91c06e92ddbc5704f8e26469cd32aee  -
same
same
[metadata] {"noOutputExpected": false}
collapse
Thinking…
All five sessions now match expected behavior. To catch edge cases in the rollback journal for `whole` under nesting/fill pace, I'll build an independent reference engine using deep-copy rollback and fuzz-test it against the current implementation on random sessions.

Bash(mkdir -p /tmp/ref && cat > /tmp/ref/ref.py <<'EOF' """Independent reference: spec re-implemented with deepcopy…)

Exit code 1
Traceback (most recent call last):
  File "/tmp/ref/fuzz.py", line 25, in <module>
    exp=ref.run(t)
        ^^^^^^^^^^
  File "/tmp/ref/ref.py", line 95, in run
    submit(st,o)
  File "/tmp/ref/ref.py", line 62, in submit
    walk(st,o)
  File "/tmp/ref/ref.py", line 42, in walk
    q=d[px]; r=q[0]
               ~^^^
IndexError: list index out of range

[error] tool reported failure
collapse
The reference engine kept a stale reference to the book side across a deep-copy restore. Fixing that in the reference and rerunning the fuzz.

Bash(cd /tmp/ref && python3 - <<'EOF' p='ref.py'; s=open(p).read() s=s.replace(""" px=lv[0] if o.px""",""" px=lv[0]…)

MISMATCH seed 308
MISMATCH seed 534
MISMATCH seed 545
MISMATCH seed 595
done bad= 4
Shell cwd was reset to /app

[stdout]
MISMATCH seed 308
MISMATCH seed 534
MISMATCH seed 545
MISMATCH seed 595
done bad= 4
[stderr]

Shell cwd was reset to /app
[metadata] {"noOutputExpected": false}
collapse
Bash(cd /tmp/ref && cat bad308.txt && diff <(python3 ref.py bad308.txt) <(python3 /app/run_book.py bad308.txt))

cap 3
mark 102
pace order
new 5 4 s 106 26 9 day -
new 25 3 b 98 6 - whole -
new 15 3 b 102 31 2 whole 105
new 21 2 b 103 5 - whole 95
new 18 3 s 98 29 6 whole -
new 16 4 b 104 38 6 whole -
new 7 1 s 104 9 4 whole 98
pull 15
pull 18
new 1 2 b 99 8 - whole -
new 26 4 b 95 37 - day -
pull 18
new 2 3 s 98 35 - day -
new 24 3 b 94 24 4 whole -
new 3 1 s 104 19 - whole -
new 23 2 s 104 30 6 day -
new 11 1 s 95 16 - day 100
new 20 4 s 101 16 - whole -
new 19 4 b 106 8 2 whole -
new 22 4 s 100 11 - day -
new 10 4 s 94 33 - day -
new 14 1 s 100 24 - part -
new 6 4 b 99 7 - day -
pull 10
new 17 2 s 97 8 10 whole 103
new 12 2 s 94 4 1 day -
28,29c28
< trd 21 2 98 5
< trp 7
---
> pul 21 whole
33d31
< pul 7 whole
36c34
< bk s 98 2 30 30
---
> bk s 98 2 35 35
39a38
> am 7

[stdout]
cap 3
mark 102
pace order
new 5 4 s 106 26 9 day -
new 25 3 b 98 6 - whole -
new 15 3 b 102 31 2 whole 105
new 21 2 b 103 5 - whole 95
new 18 3 s 98 29 6 whole -
new 16 4 b 104 38 6 whole -
new 7 1 s 104 9 4 whole 98
pull 15
pull 18
new 1 2 b 99 8 - whole -
new 26 4 b 95 37 - day -
pull 18
new 2 3 s 98 35 - day -
new 24 3 b 94 24 4 whole -
new 3 1 s 104 19 - whole -
new 23 2 s 104 30 6 day -
new 11 1 s 95 16 - day 100
new 20 4 s 101 16 - whole -
new 19 4 b 106 8 2 whole -
new 22 4 s 100 11 - day -
new 10 4 s 94 33 - day -
new 14 1 s 100 24 - part -
new 6 4 b 99 7 - day -
pull 10
new 17 2 s 97 8 10 whole 103
new 12 2 s 94 4 1 day -
28,29c28
< trd 21 2 98 5
< trp 7
---
> pul 21 whole
33d31
< pul 7 whole
36c34
< bk s 98 2 30 30
---
> bk s 98 2 35 35
39a38
> am 7
[metadata] {"returnCodeInterpretation": "Files differ", "noOutputExpected": false}
collapse
Bash(cd /tmp/ref && python3 ref.py bad308.txt | sed -n 20,32p; echo ---; python3 - <<'EOF' import sys; sys.path.ins…)

pul 14 part
rst 6 99 7
pul 10 user
arm 17
trd 12 6 99 4
trp 21
trp 11
trp 17
trd 21 2 98 5
trp 7
trd 11 6 99 3
rst 11 95 13
pul 17 whole
---
last 99 cap 3 rem 5 got 0 {106: [(5, 26, True, 4)], 98: [(2, 35, True, 3)], 104: [(23, 30, True, 2)], 100: [(22, 11, True, 4)], 94: [(10, 33, False, 4)]}
rst 5 106 9
pul 25 whole
arm 15
arm 21
pul 18 whole
pul 16 whole
arm 7
pul 15 user
pul 1 whole
rst 26 95 37
rst 2 98 35
pul 24 whole
pul 3 whole
rst 23 104 6
arm 11
pul 20 whole
pul 19 whole
rst 22 100 11
rst 10 94 33
pul 14 part
rst 6 99 7
pul 10 user
arm 17
trd 12 6 99 4
trp 21
trp 11
trp 17
pul 21 whole
trd 11 6 99 3
rst 11 95 13
pul 17 whole
bk b 95 26 37 37
bk s 95 11 13 13
bk s 98 2 35 35
bk s 100 22 11 11
bk s 104 23 6 30
bk s 106 5 9 26
am 7
Shell cwd was reset to /app

[stdout]
pul 14 part
rst 6 99 7
pul 10 user
arm 17
trd 12 6 99 4
trp 21
trp 11
trp 17
trd 21 2 98 5
trp 7
trd 11 6 99 3
rst 11 95 13
pul 17 whole
---
last 99 cap 3 rem 5 got 0 {106: [(5, 26, True, 4)], 98: [(2, 35, True, 3)], 104: [(23, 30, True, 2)], 100: [(22, 11, True, 4)], 94: [(10, 33, False, 4)]}
rst 5 106 9
pul 25 whole
arm 15
arm 21
pul 18 whole
pul 16 whole
arm 7
pul 15 user
pul 1 whole
rst 26 95 37
rst 2 98 35
pul 24 whole
pul 3 whole
rst 23 104 6
arm 11
pul 20 whole
pul 19 whole
rst 22 100 11
rst 10 94 33
pul 14 part
rst 6 99 7
pul 10 user
arm 17
trd 12 6 99 4
trp 21
trp 11
trp 17
pul 21 whole
trd 11 6 99 3
rst 11 95 13
pul 17 whole
bk b 95 26 37 37
bk s 95 11 13 13
bk s 98 2 35 35
bk s 100 22 11 11
bk s 104 23 6 30
bk s 106 5 9 26
am 7
[stderr]

Shell cwd was reset to /app
[metadata] {"noOutputExpected": false}
collapse
Thinking… (click to expand)
Bash(python3 - <<'EOF' p='eng/hold.py'; s=open(p).read() old=""" for px in sorted(opp.lv, key=lambda p: sign * p): …)

MISMATCH seed 534
MISMATCH seed 595
MISMATCH seed 931
done bad= 3
Shell cwd was reset to /app

[stdout]
MISMATCH seed 534
MISMATCH seed 595
MISMATCH seed 931
done bad= 3
[stderr]

Shell cwd was reset to /app
[metadata] {"noOutputExpected": false}
collapse
Bash(cd /tmp/ref && cat bad534.txt && diff <(python3 ref.py bad534.txt) <(python3 /app/run_book.py bad534.txt); ech…)

cap 4
mark 103
pace fill
new 31 1 b 101 27 - part -
new 22 1 b 101 27 - day 104
new 7 4 s 104 18 7 day -
new 34 4 s 99 38 - part 95
new 25 2 s 98 27 - whole -
new 35 1 s 106 16 - whole -
new 18 1 b 101 22 - day -
new 12 2 s - 3 - whole -
new 26 3 b 101 8 - part -
new 20 4 b 103 8 3 whole -
new 24 2 b 98 1 - whole -
new 15 2 b 98 27 - day -
new 16 1 b 104 14 6 day 103
new 19 2 b 102 5 - day -
new 33 2 s 105 29 - whole -
new 11 3 s - 21 - whole 101
new 4 2 s 95 35 - whole -
pull 24
new 14 1 s 95 2 5 whole 100
new 3 3 b 95 27 - whole 96
pull 11
new 29 3 b 98 9 10 day -
new 37 2 b 98 11 - day -
new 30 2 s 97 15 - day -
new 5 3 s 97 7 - part -
new 13 1 b 99 18 7 whole -
pull 7
new 36 2 s 95 30 - whole -
new 27 3 s 96 39 - day 99
new 6 1 b 103 27 - day 100
new 2 1 s 101 17 - day -
new 9 2 b 94 29 - whole -
new 1 1 s 105 23 - whole -
new 28 1 b 106 16 - whole -
new 23 3 b 105 25 - day 102
new 17 1 s 99 26 5 part -
new 10 3 s 100 19 4 day -
43c43
< bk b 98 15 22 22
---
> bk b 98 15 1 1
====
cap 7
mark 104
pace fill
new 28 4 b 101 22 1 day 103
new 1 4 b 100 32 5 whole -
new 7 2 s 104 36 - whole -
new 19 4 s 95 37 - whole 103
new 5 4 b 98 13 - day -
new 2 1 b 101 27 - day -
new 9 1 s 102 35 - part -
new 16 1 b 100 25 - day -
new 27 2 b 102 37 - day -
new 23 1 b 101 19 8 day 102
new 26 3 s 94 8 - whole 102
new 22 3 b 101 34 - part -
new 25 2 s 106 25 - whole -
new 4 2 s 102 21 - whole -
new 24 4 b 97 37 8 whole -
new 20 1 b 101 40 - day -
new 32 4 s 102 40 1 whole -
new 29 2 b 99 14 7 part -
new 21 4 s 106 15 3 day 102
new 3 2 b 94 24 - whole -
new 14 4 s 100 9 6 day -
new 30 3 s 98 32 9 day -
pull 27
pull 9
new 8 4 s 97 2 - whole -
new 11 4 s 101 31 - day -
new 18 2 s 103 22 4 day -
new 17 3 b 102 1 2 whole 97
new 6 3 b 105 5 - day -
new 13 1 b 105 27 - whole 95
new 10 4 s 104 6 - whole -
new 15 3 b 100 23 - day 97
27c27
< trd 19 2 101 9
---
> trd 19 20 101 9
29c29
< trd 26 2 101 8
---
> trd 26 20 101 8
31,35c31,32
< trd 30 2 101 10
< trd 30 20 101 22
< trd 8 20 101 2
< trd 11 20 101 16
< trd 11 23 101 8
---
> trd 30 20 101 5
> trd 30 23 101 8
37c34,39
< trd 11 23 101 7
---
> trd 30 23 101 8
> shw 23 3
> trd 30 23 101 3
> trd 30 16 100 8
> trd 8 16 100 2
> rst 11 101 31
40,41c42
< trd 6 18 103 4
< trp 28
---
> trd 6 11 101 5
43,46c44
< shw 18 4
< rst 28 101 1
< pul 17 whole
< trd 6 18 103 1
---
> trd 17 11 101 1
50,52c48
< bk b 101 23 1 4
< bk b 101 28 1 22
< bk b 100 16 25 25
---
> bk b 100 16 15 15
54c50,51
< bk s 103 18 3 17
---
> bk s 101 11 25 25
> bk s 103 18 4 22
57a55
> am 28

[stdout]
cap 4
mark 103
pace fill
new 31 1 b 101 27 - part -
new 22 1 b 101 27 - day 104
new 7 4 s 104 18 7 day -
new 34 4 s 99 38 - part 95
new 25 2 s 98 27 - whole -
new 35 1 s 106 16 - whole -
new 18 1 b 101 22 - day -
new 12 2 s - 3 - whole -
new 26 3 b 101 8 - part -
new 20 4 b 103 8 3 whole -
new 24 2 b 98 1 - whole -
new 15 2 b 98 27 - day -
new 16 1 b 104 14 6 day 103
new 19 2 b 102 5 - day -
new 33 2 s 105 29 - whole -
new 11 3 s - 21 - whole 101
new 4 2 s 95 35 - whole -
pull 24
new 14 1 s 95 2 5 whole 100
new 3 3 b 95 27 - whole 96
pull 11
new 29 3 b 98 9 10 day -
new 37 2 b 98 11 - day -
new 30 2 s 97 15 - day -
new 5 3 s 97 7 - part -
new 13 1 b 99 18 7 whole -
pull 7
new 36 2 s 95 30 - whole -
new 27 3 s 96 39 - day 99
new 6 1 b 103 27 - day 100
new 2 1 s 101 17 - day -
new 9 2 b 94 29 - whole -
new 1 1 s 105 23 - whole -
new 28 1 b 106 16 - whole -
new 23 3 b 105 25 - day 102
new 17 1 s 99 26 5 part -
new 10 3 s 100 19 4 day -
43c43
< bk b 98 15 22 22
---
> bk b 98 15 1 1
====
cap 7
mark 104
pace fill
new 28 4 b 101 22 1 day 103
new 1 4 b 100 32 5 whole -
new 7 2 s 104 36 - whole -
new 19 4 s 95 37 - whole 103
new 5 4 b 98 13 - day -
new 2 1 b 101 27 - day -
new 9 1 s 102 35 - part -
new 16 1 b 100 25 - day -
new 27 2 b 102 37 - day -
new 23 1 b 101 19 8 day 102
new 26 3 s 94 8 - whole 102
new 22 3 b 101 34 - part -
new 25 2 s 106 25 - whole -
new 4 2 s 102 21 - whole -
new 24 4 b 97 37 8 whole -
new 20 1 b 101 40 - day -
new 32 4 s 102 40 1 whole -
new 29 2 b 99 14 7 part -
new 21 4 s 106 15 3 day 102
new 3 2 b 94 24 - whole -
new 14 4 s 100 9 6 day -
new 30 3 s 98 32 9 day -
pull 27
pull 9
new 8 4 s 97 2 - whole -
new 11 4 s 101 31 - day -
new 18 2 s 103 22 4 day -
new 17 3 b 102 1 2 whole 97
new 6 3 b 105 5 - day -
new 13 1 b 105 27 - whole 95
new 10 4 s 104 6 - whole -
new 15 3 b 100 23 - day 97
27c27
< trd 19 2 101 9
---
> trd 19 20 101 9
29c29
< trd 26 2 101 8
---
> trd 26 20 101 8
31,35c31,32
< trd 30 2 101 10
< trd 30 20 101 22
< trd 8 20 101 2
< trd 11 20 101 16
< trd 11 23 101 8
---
> trd 30 20 101 5
> trd 30 23 101 8
37c34,39
< trd 11 23 101 7
---
> trd 30 23 101 8
> shw 23 3
> trd 30 23 101 3
> trd 30 16 100 8
> trd 8 16 100 2
> rst 11 101 31
40,41c42
< trd 6 18 103 4
< trp 28
---
> trd 6 11 101 5
43,46c44
< shw 18 4
< rst 28 101 1
< pul 17 whole
< trd 6 18 103 1
---
> trd 17 11 101 1
50,52c48
< bk b 101 23 1 4
< bk b 101 28 1 22
< bk b 100 16 25 25
---
> bk b 100 16 15 15
54c50,51
< bk s 103 18 3 17
---
> bk s 101 11 25 25
> bk s 103 18 4 22
57a55
> am 28
[metadata] {"returnCodeInterpretation": "Files differ", "noOutputExpected": false}
collapse
Bash(cd /tmp/ref && python3 ref.py bad931.txt | sed -n 15,40p; echo ---; python3 /app/run_book.py bad931.txt | sed …)

pul 24 whole
rst 20 101 40
pul 32 whole
pul 29 part
arm 21
pul 3 whole
trd 14 27 102 9
trp 19
trp 23
trp 26
trp 21
trd 19 27 102 28
trd 19 2 101 9
rst 23 101 8
trd 26 2 101 8
rst 21 106 3
trd 30 2 101 10
trd 30 20 101 22
trd 8 20 101 2
trd 11 20 101 16
trd 11 23 101 8
shw 23 8
trd 11 23 101 7
rst 18 103 4
arm 17
trd 6 18 103 4
---
pul 24 whole
rst 20 101 40
pul 32 whole
pul 29 part
arm 21
pul 3 whole
trd 14 27 102 9
trp 19
trp 23
trp 26
trp 21
trd 19 27 102 28
trd 19 20 101 9
rst 23 101 8
trd 26 20 101 8
rst 21 106 3
trd 30 20 101 5
trd 30 23 101 8
shw 23 8
trd 30 23 101 8
shw 23 3
trd 30 23 101 3
trd 30 16 100 8
trd 8 16 100 2
rst 11 101 31
rst 18 103 4
Shell cwd was reset to /app

[stdout]
pul 24 whole
rst 20 101 40
pul 32 whole
pul 29 part
arm 21
pul 3 whole
trd 14 27 102 9
trp 19
trp 23
trp 26
trp 21
trd 19 27 102 28
trd 19 2 101 9
rst 23 101 8
trd 26 2 101 8
rst 21 106 3
trd 30 2 101 10
trd 30 20 101 22
trd 8 20 101 2
trd 11 20 101 16
trd 11 23 101 8
shw 23 8
trd 11 23 101 7
rst 18 103 4
arm 17
trd 6 18 103 4
---
pul 24 whole
rst 20 101 40
pul 32 whole
pul 29 part
arm 21
pul 3 whole
trd 14 27 102 9
trp 19
trp 23
trp 26
trp 21
trd 19 27 102 28
trd 19 20 101 9
rst 23 101 8
trd 26 20 101 8
rst 21 106 3
trd 30 20 101 5
trd 30 23 101 8
shw 23 8
trd 30 23 101 8
shw 23 3
trd 30 23 101 3
trd 30 16 100 8
trd 8 16 100 2
rst 11 101 31
rst 18 103 4
[stderr]

Shell cwd was reset to /app
[metadata] {"noOutputExpected": false}
collapse
Bash(cd /tmp/ref && python3 /app/run_book.py bad931.txt | sed -n 1,14p; python3 - <<'EOF' import sys; sys.path.inse…)

arm 28
pul 1 whole
pul 7 whole
… +202 lines (click to expand)
Thinking…
Found the bug: successful nested `whole` blocks discarded their journal frame, so the enclosing rollback couldn't see those mutations. I'll fix this by merging the inner frame into the outer one on success.

Bash(python3 - <<'EOF' p='eng/hold.py'; s=open(p).read() old=""" for r in buf.rows: out.row(*r) """ new=""" if JRN:…)

Command did not complete within its 120s timeout and was moved to the background (ID: biiaaw59n). Output is being written to: /tmp/claude-0/-app/6b4afa06-8cd5-433a-8f98-7051ebf92995/tasks/biiaaw59n.output. You will be notified when it completes. To check interim output, use Read on that file path.
Session cwd remains /app; directory changes made by the backgrounded command do not apply to subsequent commands.

[metadata] {"noOutputExpected": false, "backgroundTaskId": "biiaaw59n", "timedOutAfterMs": 120000, "backgroundCwdHint": "Session cwd remains /app; directory changes made by the backgrounded command do not apply to subsequent commands."}
collapse
Bash(sleep 100; cat /tmp/claude-0/-app/6b4afa06-8cd5-433a-8f98-7051ebf92995/tasks/biiaaw59n.output)

done bad= 0

[exited with code 0]

[stdout]
done bad= 0

[exited with code 0]
[metadata] {"noOutputExpected": false}
collapse
All 3000 random sessions match the independent reference. Next I'll run a larger-shaped fuzz batch and build a synthetic fill-pace session at the graded scale to check timing.

Bash(cd /tmp/ref && sed -i 's/ids=list(range(1,R.randint(5,40)))/ids=list(range(1,R.randint(5,int(sys.argv[3]))))/'…)

done bad= 0
python3: can't open file '/tmp/ref/run_book.py': [Errno 2] No such file or directory

real	0m0.028s
user	0m0.013s
sys	0m0.014s
Shell cwd was reset to /app

[stdout]
done bad= 0
python3: can't open file '/tmp/ref/run_book.py': [Errno 2] No such file or directory

real	0m0.028s
user	0m0.013s
sys	0m0.014s
[stderr]

Shell cwd was reset to /app
[metadata] {"noOutputExpected": false}
collapse
Bash(time python3 run_book.py /tmp/ref/bigfill.txt | awk '{c[$1]++} END{for(k in c) print k,c[k]}'; grep -c whole /…)

trp 20
bk 8514
shw 14203
rst 10866
trd 17617
pul 2929
arm 20

real	0m0.246s
user	0m0.231s
sys	0m0.021s
1828

[stdout]
trp 20
bk 8514
shw 14203
rst 10866
trd 17617
pul 2929
arm 20

real	0m0.246s
user	0m0.231s
sys	0m0.021s
1828
[metadata] {"noOutputExpected": false}
collapse
Timing is comfortable at graded scale. Let me review the final source of the five files once for leftovers.

Bash(cat eng/hold.py eng/take.py eng/shown.py; ls /tmp/ref/bad*.txt | wc -l)

import heapq
from collections import deque

from eng import hand, take, trip

# Undo journal: one frame per whole order currently executing.  Empty when
# nothing is executing under whole, so the note_* hooks cost one test.
JRN = []


class Buf:
    __slots__ = ("rows",)

    def __init__(self):
        self.rows = []

    def row(self, *cells):
        self.rows.append(cells)


def note_o(o):
    if JRN:
        JRN[-1].append((0, o, o.rem, o.shn, o.live))


def note_q(side, px):
    if JRN:
        q = side.lv.get(px)
        JRN[-1].append((1, side, px, None if q is None else list(q)))


def note_arm(st):
    if JRN:
        JRN[-1].append((2, list(st.arm)))


def _undo(st, frame):
    for e in reversed(frame):
        k = e[0]
        if k == 0:
            _, o, rem, shn, live = e
            o.rem = rem
            o.shn = shn
            o.live = live
        elif k == 1:
            _, side, px, saved = e
            if saved is None:
                side.lv.pop(px, None)
            else:
                q = side.lv.get(px)
                if q is None:
                    side.lv[px] = deque(saved)
                    heapq.heappush(side.pq, side.sign * px)
                else:
                    q.clear()
                    q.extend(saved)
        else:
            trip.reset(st, e[1])


def room(st, o):
    opp = st.bk.opp(o.side)
    sign = 1 if o.side == "b" else -1
    last = st.last
    got = 0
    for px in sorted(opp.lv, key=lambda p: sign * p):
        live = [r for r in opp.lv[px] if r.live]
        if not live:
            continue
        if o.px is not None and sign * (px - o.px) > 0:
            break
        if abs(px - last) > st.cap:
            break
        took = False
        for r in live:
            if not hand.blocks(o, r):
                got += r.rem
                took = True
        if took:
            last = px
        if got >= o.rem:
            break
    return got


def admit(st, o, out):
    if st.pace != "fill" and room(st, o) < o.rem:
        out.row("pul", o.oid, "whole")
        return
    frame = []
    last = st.last
    pend = list(st.pend)
    if st.arm is not None:
        frame.append((2, list(st.arm)))
    JRN.append(frame)
    buf = Buf()
    try:
        take.walk(st, o, buf)
    finally:
        JRN.pop()
    if o.rem > 0:
        _undo(st, frame)
        st.last = last
        st.pend.clear()
        st.pend.extend(pend)
        out.row("pul", o.oid, "whole")
        return
    if JRN:
        JRN[-1].extend(frame)
    for r in buf.rows:
        out.row(*r)
from eng import hand, hold, shown, trip


def run_batch(st, hit, out):
    from mkt.drv import submit
    for f in hit:
        hold.note_o(f)
        if f.px is not None:
            hold.note_q(st.bk.own(f.side), f.px)
        submit(st, f, out)


def walk(st, o, out):
    opp = st.bk.opp(o.side)
    sign = 1 if o.side == "b" else -1
    cap = st.cap
    bound = o.px
    hold.note_o(o)
    while o.rem > 0:
        px = opp.top()
        if px is None:
            break
        if bound is not None and sign * (px - bound) > 0:
            break
        if abs(px - st.last) > cap:
            break
        r = opp.front(px)
        if r is None:
            continue
        hold.note_o(r)
        if hand.blocks(o, r):
            hold.note_q(opp, px)
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
            hold.note_q(opp, px)
            r.live = False
            opp.take(px)
            hit = trip.check(st, out)
        else:
            hit = trip.check(st, out)
            if r.shn <= 0:
                out.row("shw", r.oid, shown.refill(opp, r))
        if hit and st.pace == "fill":
            run_batch(st, hit, out)
from eng import hold


def avail(r):
    return r.shn


def refill(side, r):
    hold.note_q(side, r.px)
    q = side.lv[r.px]
    if q and q[0] is r:
        q.popleft()
        q.append(r)
    else:
        try:
            q.remove(r)
        except ValueError:
            pass
        q.append(r)
    r.shn = r.rem if r.shw is None else min(r.shw, r.rem)
    return r.shn
5

[stdout]
import heapq
from collections import deque

from eng import hand, take, trip

# Undo journal: one frame per whole order currently executing.  Empty when
# nothing is executing under whole, so the note_* hooks cost one test.
JRN = []


class Buf:
    __slots__ = ("rows",)

    def __init__(self):
        self.rows = []

    def row(self, *cells):
        self.rows.append(cells)


def note_o(o):
    if JRN:
        JRN[-1].append((0, o, o.rem, o.shn, o.live))


def note_q(side, px):
    if JRN:
        q = side.lv.get(px)
        JRN[-1].append((1, side, px, None if q is None else list(q)))


def note_arm(st):
    if JRN:
        JRN[-1].append((2, list(st.arm)))


def _undo(st, frame):
    for e in reversed(frame):
        k = e[0]
        if k == 0:
            _, o, rem, shn, live = e
            o.rem = rem
            o.shn = shn
            o.live = live
        elif k == 1:
            _, side, px, saved = e
            if saved is None:
                side.lv.pop(px, None)
            else:
                q = side.lv.get(px)
                if q is None:
                    side.lv[px] = deque(saved)
                    heapq.heappush(side.pq, side.sign * px)
                else:
                    q.clear()
                    q.extend(saved)
        else:
            trip.reset(st, e[1])


def room(st, o):
    opp = st.bk.opp(o.side)
    sign = 1 if o.side == "b" else -1
    last = st.last
    got = 0
    for px in sorted(opp.lv, key=lambda p: sign * p):
        live = [r for r in opp.lv[px] if r.live]
        if not live:
            continue
        if o.px is not None and sign * (px - o.px) > 0:
          
… [clipped]
collapse
The engine is restored. All five sample sessions behave as specified, 3,400 random sessions match an independent deep-copy reference engine, and the large inputs run in under a second each.

**What was wrong**

- `shown.avail` offered the full remainder instead of the shown slice, and `refill` never moved the order to the back of its price queue. That produced the single 30-lot fill in s1.
- `take.walk` measured `cap` against the price at the start of the walk instead of the latest fill, so the s2 walk gave up after one level.
- `trip.check` ran once per walk, not once per fill, and re-sorted the batch by trip price and id. Sells that fire only at an intermediate price were missed, and batch order was wrong.
- `hold.admit` decided `whole` orders from a pre-count and never rolled anything back.
- `hand.blocks` was already correct and is unchanged.

**What I changed, in the five permitted files only**

- `take.py`: dynamic cap check, trip check after every fill with `trp` lines before `shw`, and under fill pace it executes the fired batch immediately by calling the driver's `submit`, so nested batches run depth first.
- `shown.py`: shown-slice availability, and disclosure moves the order to the back of its level.
- `trip.py`: parked orders are indexed in two heaps by trip price with arrival sequence, so a fill costs a heap peek rather than a scan of every parked order. This cut wide.txt from 16 seconds to 0.7. Batches keep arrival order.
- `hold.py`: `whole` runs inside an undo journal. Every order or queue mutation during its execution is logged before it happens, output is held in a buffer, and on a shortfall the book, last price, parked set and waiting queue are restored and only the `pul` line goes out through the emitter. A nested successful `whole` merges its journal into the enclosing frame so an outer failure still unwinds it. The pre-count remains as a fast path under order pace, now skipping dead levels and same-participant orders.

**Timing**

| session | time |
|---|---|
| wide.txt | 0.7 s |
| book.txt | 0.1 s |
| synthetic fill-pace, 9,200 resting plus 1,800 whole orders | 0.25 s |


The reference engine and fuzzer‘ are in ‘ltnp/ref' if you want to rerun them.