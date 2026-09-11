"""The enumerated programs: one per graded decision, plus the must-still-work side of each fence.

Each entry is named for the decision it pins, so a failure says which rule broke rather than
"one of the graded programs was wrong". `authoring/shard-spend-carry/readings.py` runs every
plausible wrong reading against this set and reports which case separates it; a reading this
set does not separate is either promoted to a shipped case or shown to be a correct variant.

The groups:

  map-*    what the map holds, in what order, and when it is laid again
  cut-*    the shard: a count of slots, rounded up, short at the end, and empty past the world
  spend-*  the walk: what a rank applies, where it stops, and what it leaves behind
  grd-*    gradients arriving for a parameter that is not in the map
  keep-*   what a checkpoint is, and which layout a restore means
"""

PROGS = {}


def _p(name, text):
    PROGS[name] = [line for line in text.strip().splitlines() if line.strip()]


# --- the map ---------------------------------------------------------------------------

_p("map-order", """
bud 100
par a 2
par b 3
ws 2
grd a 1
grd b 1
step
own 0
own 1
val a
val b
""")

_p("map-at-step", """
bud 100
par a 2
par b 2
ws 1
own 0
step
own 0
frz a
own 0
step
own 0
""")

_p("map-thaw-end", """
bud 100
par a 2
par b 3
ws 1
step
frz a
step
thw a
step
own 0
val a
mom a
""")

_p("map-round-trip", """
bud 100
par a 2
par b 2
ws 1
grd a 3
step
frz a
thw a
step
own 0
mom a
val a
""")

_p("map-chill", """
bud 100
par a 2
par b 2
ws 1
grd a 3
step
mom a
frz a
step
mom a
val a
""")

_p("map-late", """
bud 100
par a 2
par b 2
ws 1
step
frz a
step
par c 2
thw a
step
own 0
ws 3
step
own 1
own 2
""")

# --- the shard -------------------------------------------------------------------------

_p("cut-ceil", """
bud 100
par a 5
ws 2
step
own 0
own 1
""")

_p("cut-inside", """
bud 100
par a 2
par b 5
ws 3
step
own 0
own 1
own 2
""")

_p("cut-empty", """
bud 100
par a 2
ws 5
step
own 0
own 1
own 2
own 4
""")

_p("cut-past", """
bud 100
par a 4
ws 2
step
own 2
own 7
""")

# --- the walk --------------------------------------------------------------------------

_p("spend-prefix", """
bud 5
par a 4
par b 4
ws 2
grd a 1
grd b 2
step
val a
val b
mom b
""")

_p("spend-all", """
bud 1000
par a 4
par b 3
par c 2
ws 3
grd a 1
grd b 2
grd c 3
step
val a
val b
val c
mom b
""")

_p("spend-block", """
bud 3
par a 2
par b 2
ws 1
grd a 5
grd b 1
step
val a
val b
bud 12
step
val a
val b
""")

_p("spend-exact", """
bud 4
par a 3
ws 1
grd a 2
step
val a
mom a
""")

_p("spend-zero", """
bud 100
par a 3
ws 1
grd a 1
step
step
val a
mom a
""")

_p("spend-cancel", """
bud 100
par a 2
par b 2
ws 1
grd a 3
grd a -3
grd b 1
step
val a
mom a
val b
""")

_p("spend-long", """
bud 2
par a 9
ws 3
grd a 1
step
val a
mom a
own 1
own 2
""")

_p("spend-carry", """
bud 2
par a 5
ws 1
grd a 1
step
grd a 1
step
val a
mom a
""")

_p("spend-sign", """
bud 6
par a 3
ws 1
grd a -2
step
val a
mom a
grd a 1
step
val a
mom a
""")

_p("spend-share", """
bud 3
par a 4
par b 4
ws 2
grd a 2
grd b 1
step
val a
val b
step
val a
val b
""")

# --- gradients for a parameter that is out of the map ------------------------------------

_p("grd-frozen", """
bud 100
par a 2
par b 2
ws 1
step
frz a
step
grd a 4
thw a
step
val a
mom a
own 0
""")

_p("grd-while-out", """
bud 5
par a 3
par b 3
ws 1
grd a 1
step
frz a
step
grd a 3
step
val a
mom a
thw a
step
val a
mom a
""")

# --- checkpoints -------------------------------------------------------------------------

_p("keep-plain", """
bud 100
par a 3
ws 1
grd a 2
step
save s
grd a 1
step
val a
load s
val a
mom a
""")

_p("keep-moved", """
bud 100
par a 2
par b 3
ws 1
grd a 1
grd b 2
step
save s
frz a
step
thw a
step
load s
val a
val b
mom a
mom b
""")

_p("keep-absent", """
bud 100
par a 2
ws 1
grd a 1
step
frz a
step
par b 2
grd b 3
step
save s
grd b 1
step
load s
val a
mom a
val b
""")

_p("keep-cut", """
bud 2
par a 5
ws 1
grd a 1
step
save s
bud 100
step
val a
load s
val a
mom a
""")

_p("keep-pending", """
bud 100
par a 3
ws 1
step
save s
grd a 2
load s
step
val a
mom a
""")

_p("keep-empty", """
bud 100
par a 2
ws 1
save s
step
grd a 1
step
load s
val a
mom a
""")

ORDER = tuple(sorted(PROGS))


def ops(name):
    return list(PROGS[name])
