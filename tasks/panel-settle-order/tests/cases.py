"""The enumerated set: one panel per rule, aimed where a plausible reading diverges.

Each entry names the reading it exists to fail. The generated panels in gen.py cover the
combinations nobody thought of; this set pins the individual rules and makes a failure
legible - a submission that fails only latch-order has a different bug from one that fails
only flip-deeper.

Fence panels are marked MUST-WORK. They exist so that an implementation which overshoots -
re-running gauges that nothing woke, tripping latches that saw no movement, refusing to
settle a panel that has no conditional in it at all - fails exactly as hard as one that
undershoots.
"""

PANELS = {}
NOTE = {}


def case(name, note, text):
    PANELS[name] = text.strip("\n") + "\n"
    NOTE[name] = note


case("order-diamond",
     "a gauge reading two arms of a split runs once, after both arms: taking gauges in the "
     "order they were woken runs it first, on values neither arm has produced yet", """
F a 1
G sink add(left, right)
G left add(a, 1)
G right add(a, 2)
R a=5
""")

case("order-scrambled",
     "declaration order is not dependency order: a chain declared outermost first must "
     "still run innermost first", """
F src 2
G out add(mid, tail)
G tail add(mid, 1)
G mid add(step, 1)
G step add(src, 1)
R src=7
""")

case("tie-declaration",
     "two gauges the same distance from the feeds run in the order the panel declares "
     "them, not by name and not by when they were woken", """
F a 0
G zeta add(a, 1)
G alpha add(a, 2)
G both add(zeta, alpha)
R a=4
""")

case("flip-deeper",
     "a conditional that starts reading a deeper entry has moved further from the feeds, "
     "so a distance settled earlier in the panel is stale: running it at that distance "
     "reaches it before the entry it now reads has settled", """
F sel 0
F base 0
G face pick(sel, deep, base)
G one add(base, 1)
G deep add(one, 1)
R sel=1 base=2
""")

case("flip-shallower",
     "the mirror: a conditional that stops reading a deep entry has moved back toward the "
     "feeds, and a distance that only ever grows runs it later than it belongs. The last "
     "round is the one that tells the two apart, because it wakes the conditional and a "
     "gauge that is genuinely one step out at the same moment", """
F sel 1
F base 0
G face pick(sel, deep, base)
G one add(base, 1)
G deep add(one, 1)
R sel=0 base=2
R base=5
""")

case("flip-far",
     "the distance goes above the entry that was read, not one step further out", """
F sel 0
F base 0
G face pick(sel, d3, base)
G d1 add(base, 1)
G d2 add(d1, 1)
G d3 add(d2, 1)
R sel=1 base=2
""")

case("drop-wake",
     "an entry a gauge has stopped reading stops waking it: a later move on the arm the "
     "conditional no longer takes must run nothing at all", """
F sel 1
F x 0
F y 7
G face pick(sel, x, y)
R sel=0
R x=5
""")

case("take-wake",
     "MUST-WORK, the other side of drop-wake: the arm the conditional has just started "
     "reading does wake it", """
F sel 1
F x 0
F y 7
G face pick(sel, x, y)
R sel=0
R y=5
""")

case("latch-settles",
     "a latch reports what its entry came to rest at, so it cannot trip while the round "
     "is still moving", """
F a 0
G sum add(a, mid)
G mid add(a, 1)
T w sum
R a=3
""")

case("latch-no-move",
     "a gauge that runs and comes back with the value it already had has not moved, and a "
     "latch on it does not trip", """
F a 1
F b 1
G same gt(a, b)
G other add(a, 1)
T w same
R a=0
""")

case("build-quiet",
     "MUST-WORK: nothing trips while the panel is coming up, however far the gauges move "
     "from nothing to their first values", """
F a 4
G one add(a, 1)
G two add(one, 1)
T w one
T v two
R a=4
""")

case("latch-order",
     "two latches that both trip in one round trip in the order the panel declares them, "
     "and their writes reach the next round in that order", """
F a 0
F z 0
G p add(a, 1)
G q add(a, 2)
T second q z=2
T first p z=9
R a=5
""")

case("latch-once",
     "a latch trips at most once in a round even though its entry is reached more than "
     "once while the round settles", """
F a 0
G top add(mid, side)
G mid add(a, 1)
G side add(a, 2)
T w top
R a=6
""")

case("write-back-round",
     "what a latch writes lands as the next round rather than inside the one that tripped "
     "it, so the trace shows a fresh round with its own inputs", """
F a 0
F b 0
G sum add(a, b)
T w sum b=3
R a=1
""")

case("write-back-cascade",
     "a write-back that moves an entry a second latch watches makes a further round, and "
     "the panel is not finished until nothing more is written", """
F a 0
F b 0
F c 0
G x add(a, b)
G y add(x, c)
T wx x b=2
T wy y c=3
R a=1
""")

case("no-move-no-run",
     "MUST-WORK: a feed written the value it already holds has not moved, and nothing runs", """
F a 3
G one add(a, 1)
G two add(one, 1)
R a=3
R a=4
""")

case("quiet-panel",
     "MUST-WORK: a panel with no conditional and no latch settles once per round and is "
     "never asked to do anything else", """
F a 1
F b 2
G s add(a, b)
G t sub(a, b)
R a=5
R b=1
""")

case("unread-feed",
     "MUST-WORK: a feed nothing reads moves without waking anything", """
F used 1
F spare 0
G one add(used, 1)
R spare=9
R used=2
""")

case("chained-flip",
     "a conditional whose own condition is a gauge: the arm changes because something "
     "upstream moved in the same round", """
F a 0
F lo 1
F hi 8
G gate gt(a, 2)
G face pick(gate, hi, lo)
G lo2 add(lo, 1)
R a=5
R a=0
""")

case("two-flips",
     "two conditionals that swap arms in the same round, one moving out and one moving in", """
F sel 0
F base 1
G left pick(sel, deep, base)
G right pick(sel, base, deep)
G one add(base, 1)
G deep add(one, 1)
R sel=1
R sel=0
""")
