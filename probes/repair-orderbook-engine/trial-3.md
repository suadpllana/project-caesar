I'll start by reading the engine source and the sessions.

Bash(find . -type f | grep -v sess/ | head -50 && wc -l eng/*.py run_book.py && ls -la sess && cat run_book.py)

./run_book.py
./eng/take.py
./eng/shown.py
./eng/hand.py
./eng/hold.py
./eng/trip.py
./eng/__init__.py
./mkt/ev.py
./mkt/rd.py
./mkt/bk.py
./mkt/drv.py
./mkt/__init__.py
   0 eng/__init__.py
   2 eng/hand.py
  23 eng/hold.py
   7 eng/shown.py
  35 eng/take.py
  38 eng/trip.py
  27 run_book.py
 132 total
total 268
drwxr-xr-x 2 root root   4096 Sep  9 09:49 .
drwxr-xr-x 5 root root   4096 Sep  9 09:49 ..
-rw-r--r-- 1 root root 117723 Jan  1  1980 book.txt
-rw-r--r-- 1 root root    160 Jan  1  1980 fill.txt
-rw-r--r-- 1 root root     91 Jan  1  1980 s1.txt
-rw-r--r-- 1 root root    138 Jan  1  1980 s2.txt
-rw-r--r-- 1 root root 134029 Jan  1  1980 wide.txt
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

[stdout]
./run_book.py
./eng/take.py
./eng/shown.py
./eng/hand.py
./eng/hold.py
./eng/trip.py
./eng/__init__.py
./mkt/ev.py
./mkt/rd.py
./mkt/bk.py
./mkt/drv.py
./mkt/__init__.py
   0 eng/__init__.py
   2 eng/hand.py
  23 eng/hold.py
   7 eng/shown.py
  35 eng/take.py
  38 eng/trip.py
  27 run_book.py
 132 total
total 268
drwxr-xr-x 2 root root   4096 Sep  9 09:49 .
drwxr-xr-x 5 root root   4096 Sep  9 09:49 ..
-rw-r--r-- 1 root root 117723 Jan  1  1980 book.txt
-rw-r--r-- 1 root root    160 Jan  1  1980 fill.txt
-rw-r--r-- 1 root root     91 Jan  1  1980 s1.txt
-rw-r--r-- 1 root root    138 Jan  1  1980 s2.txt
-rw-r--r-- 1 root root 134029 Jan  1  1980 wide.txt
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
[metadata] {"noOutputExpected": false}
collapse
Bash(for f in eng/take.py eng/shown.py eng/hand.py eng/hold.py eng/trip.py mkt/ev.py mkt/rd.py mkt/bk.py mkt/drv.py…)

=== eng/take.py
from eng import hand, shown, trip
… +262 lines (click to expand)
Thinking…
Got the full picture: since the driver in mkt/drv.py is fixed, I need to implement fills, disclosure, trip firing, fill-pace batches, and all-or-nothing rollback across the five eng files. Writing those now.

Bash(cat > eng/shown.py <<'EOF' def avail(r): return r.shn def refill(side, r): r.shn = r.rem if r.shw is None else…)

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
All three small sessions now produce the expected sequences. Next, timing on the two large sessions and a consistency check of their output.

Bash(for s in wide book; do echo "== $s"; /usr/bin/time -f "%es %MKB" python3 run_book.py sess/$s.txt > /tmp/$s.out…)

== wide
/bin/bash: line 1: /usr/bin/time: No such file or directory
0
== book
/bin/bash: line 1: /usr/bin/time: No such file or directory
0
sess/book.txt:560
sess/wide.txt:2
sess/s1.txt:0
sess/wide.txt:0
sess/s2.txt:0
sess/fill.txt:1
sess/book.txt:0

[stdout]
== wide
/bin/bash: line 1: /usr/bin/time: No such file or directory
0
== book
/bin/bash: line 1: /usr/bin/time: No such file or directory
0
sess/book.txt:560
sess/wide.txt:2
sess/s1.txt:0
sess/wide.txt:0
sess/s2.txt:0
sess/fill.txt:1
sess/book.txt:0
[metadata] {"noOutputExpected": false}
collapse
Bash(for s in wide book; do echo "== $s"; ( time python3 run_book.py sess/$s.txt > /tmp/$s.out ) 2>&1 | grep real; …)

== wide
real	0m0.717s
233880
   4199 am    4200 arm      51 bk       1 pul      74 rst  112663 shw  112692 trd 
== book
real	0m0.089s
7594
   2994 bk     392 pul    3560 rst     648 trd

[stdout]
== wide
real	0m0.717s
233880
   4199 am    4200 arm      51 bk       1 pul      74 rst  112663 shw  112692 trd 
== book
real	0m0.089s
7594
   2994 bk     392 pul    3560 rst     648 trd
[metadata] {"noOutputExpected": false}
collapse
Both large sessions run in under a second. The wide session fired only one of 4,200 parked orders, which I want to verify against the trip prices in the input before trusting it.

Bash(cd /app; grep -v arm /tmp/wide.out | grep -v '^shw\|^trd\|^am' | head -20; echo; grep trp /tmp/wide.out; echo;…)

rst 1 999 5
rst 2 1002 20
rst 3 997 40
rst 4 1004 8
rst 5 995 60
rst 6 1006 5
rst 7 993 20
rst 8 1008 60
rst 9 991 8
rst 10 1001 8
rst 11 998 20
rst 12 1003 40
rst 13 996 60
rst 14 1005 8
rst 15 994 5
rst 16 1007 20
rst 17 992 40
rst 18 1009 60
rst 19 999 60
rst 20 1002 40


  59241 999
  53451 1001

min buy trip 1061 max sell trip 940

[stdout]
rst 1 999 5
rst 2 1002 20
rst 3 997 40
rst 4 1004 8
rst 5 995 60
rst 6 1006 5
rst 7 993 20
rst 8 1008 60
rst 9 991 8
rst 10 1001 8
rst 11 998 20
rst 12 1003 40
rst 13 996 60
rst 14 1005 8
rst 15 994 5
rst 16 1007 20
rst 17 992 40
rst 18 1009 60
rst 19 999 60
rst 20 1002 40


  59241 999
  53451 1001

min buy trip 1061 max sell trip 940
[metadata] {"noOutputExpected": false}
collapse
Thinking… (click to expand)
Bash(cd /app; mkdir -p /tmp/t # fill pace: whole 5 fires 4 (a whole that fails -> stays fired) and 6 (day sell that…)

== a
rst 1 101 5
rst 2 102 5
rst 3 99 4
arm 4
arm 6
trd 5 1 101 5
trp 4
trp 6
pul 4 whole
trd 6 3 99 3
trd 5 2 102 5
rst 7 102 10
bk b 102 7 10 10
bk b 99 3 1 1
== b
rst 1 100 5
rst 2 100 3
pul 3 whole
pul 4 whole
arm 5
trd 6 1 100 1
trp 5
trd 5 1 100 4
trd 5 2 100 3
shw 2 2
trd 5 2 100 2
pul 5 part

[stdout]
== a
rst 1 101 5
rst 2 102 5
rst 3 99 4
arm 4
arm 6
trd 5 1 101 5
trp 4
trp 6
pul 4 whole
trd 6 3 99 3
trd 5 2 102 5
rst 7 102 10
bk b 102 7 10 10
bk b 99 3 1 1
== b
rst 1 100 5
rst 2 100 3
pul 3 whole
pul 4 whole
arm 5
trd 6 1 100 1
trp 5
trd 5 1 100 4
trd 5 2 100 3
shw 2 2
trd 5 2 100 2
pul 5 part
[metadata] {"noOutputExpected": false}
collapse
Thinking… (click to expand)
Bash(cd /app; cat > /tmp/t/c.txt <<'EOF' pace fill cap 10 mark 100 new 1 1 s 101 6 2 day - new 2 2 s 101 4 - day - …)

rst 1 101 2
rst 2 101 4
rst 3 99 4
arm 4
arm 8
pul 5 whole
trd 6 1 101 2
trp 4
trp 8
shw 1 2
trd 4 3 99 3
trd 8 2 101 2
trd 6 2 101 1
bk b 99 3 1 1
bk s 101 2 1 1
bk s 101 1 2 4

[stdout]
rst 1 101 2
rst 2 101 4
rst 3 99 4
arm 4
arm 8
pul 5 whole
trd 6 1 101 2
trp 4
trp 8
shw 1 2
trd 4 3 99 3
trd 8 2 101 2
trd 6 2 101 1
bk b 99 3 1 1
bk s 101 2 1 1
bk s 101 1 2 4
[metadata] {"noOutputExpected": false}
collapse
The engine is fixed and every session in `/app/sess` runs correctly and fast. Only the five permitted files changed.

**What was wrong**

- `shown.avail` offered the order's whole remainder instead of its shown slice, and `refill` never moved the order to the back of its price queue. That produced the single 30-lot fill in the first session.
- `walk` measured the price cap from the last price at the start of the walk rather than the current one, so the second session stopped one level in. Trips were checked only once at the end of the walk instead of after every fill.
- `trip.check` sorted firing orders by trip price and id rather than arrival order, and knew nothing about fill pace.
- `hold.admit` used a room estimate that counted same-participant orders and ignored the moving cap, and had no way to undo a partly executed whole.

**What the engine does now**

- `walk` fills against shown slices, re-reads the cap against the live last price, prints `trp` lines before `shw`, and under fill pace runs each fill's batch immediately, recursively, before resuming.
- `trip.check` fires in arrival order, queues to the driver's pending list only under order pace, and short-circuits with cached best trip prices so the wide sessions stay cheap.
- `hold.admit` uses an exact liquidity precheck under order pace, where a whole's walk is deterministic. Under fill pace it snapshots book, last price, quantities, shown sizes, queue positions, parked set and pending queue, runs the whole into a private buffer, and either replays the buffer through `out.row` one line at a time or restores everything and prints only the cancellation.
- `shown.refill` discloses the next slice and requeues the order at the back of its level.

**Verification**

- The two named sessions now print the walks described in the rules: sliced fills alternating with disclosures in s1, and a three-level walk in s2 ending with the order behind trip 104 firing and resting.
- The fill-pace sample and three hand-built sessions covering nested wholes, same-participant pulls, a fired whole that fails on its own, and a failing whole whose side effects must vanish all behave as the rules require.
- Timing on the supplied large sessions:

| Session | Time |
|---|---|
| wide.txt | 0.7 s |
| book.txt | 0.1 s |

At three times these sizes the full graded set stays far inside the 300 second budget.