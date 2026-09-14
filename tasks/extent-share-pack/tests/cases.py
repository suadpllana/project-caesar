"""The enumerated programs: one per graded decision, plus the must-still-work side of each fence.

Each entry is named for the decision it pins, so a failure says which rule broke rather than
"one of the graded programs was wrong". `authoring/extent-share-pack/readings.py` runs every
plausible wrong reading against this set and reports which case separates it; a reading this set
does not separate is either promoted to a shipped case or shown to be a correct variant.

The groups:

  put-*    the write: a new extent, and what happens to the pointers it displaces
  use-*    the charge: a whole extent per volume on it, counted once however many slots
  hold-*   occupancy by block and presence by volume, where a tally and a set differ
  pack-*   the rewrite: the half rule, sharing, ordering, ids and the new block numbers
  drop-*   what removing a volume frees, and what it leaves eligible
  own-*    the drop-gain query: solo extents, the shared pair, three volumes, no gain
  cp-*     the copy: the pointers as they stood before the op, and the empty source
  line-*   what is printed, in what order, and which ops print nothing
"""

PROGS = {}


def _p(name, text):
    PROGS[name] = [line for line in text.strip().splitlines() if line.strip()]


# --- the write ------------------------------------------------------------------------

_p("put-fresh", """
vol a
fil a p 4
wr a p 0 3
use a
tot
at a p 0
at a p 3
""")

_p("put-steal", """
vol a
fil a p 6
wr a p 0 3
wr a p 2 5
use a
tot
at a p 2
""")

_p("put-first-id", """
vol a
fil a p 6
wr a p 0 3
tr a p 1 2
wr a p 3 3
at a p 0
at a p 3
tot
""")

# --- the charge -----------------------------------------------------------------------

_p("use-once", """
vol a
fil a p 4
wr a p 0 3
cp a p 0 1 a p 2
use a
tot
""")

_p("use-whole", """
vol a
fil a p 8
wr a p 0 5
vol b
fil b q 2
cp a p 0 0 b q 0
use b
use a
tot
""")

# --- occupancy and presence -------------------------------------------------------------

_p("hold-dup", """
vol a
fil a p 4
wr a p 0 3
cp a p 0 0 a p 1
tr a p 2 3
tot
at a p 0
at a p 1
""")

_p("hold-twice", """
vol a
fil a p 4
wr a p 0 1
cp a p 0 0 a p 2
tr a p 0 0
use a
tot
""")

_p("hold-last", """
vol a
fil a p 2
wr a p 0 1
sn a b
tr a p 0 1
tot
use a
use b
""")

# --- the rewrite ------------------------------------------------------------------------

_p("pack-half", """
vol a
fil a p 4
wr a p 0 3
tr a p 2 3
tot
at a p 0
""")

_p("pack-under", """
vol a
fil a p 5
wr a p 0 4
tr a p 0 0
tr a p 2 2
tr a p 4 4
at a p 1
at a p 3
tot
""")

_p("pack-shared", """
vol a
fil a p 4
wr a p 0 3
vol b
fil b q 4
cp a p 0 0 b q 0
tr a p 1 3
tot
at a p 0
""")

_p("pack-order", """
vol a
fil a p 8
wr a p 0 3
wr a p 4 7
tr a p 1 6
at a p 0
at a p 7
tot
""")

_p("pack-dup", """
vol a
fil a p 6
wr a p 0 4
cp a p 4 4 a p 0
tr a p 1 3
at a p 0
at a p 4
tot
""")

_p("pack-one", """
vol a
fil a p 4
wr a p 0 1
tr a p 1 1
tot
at a p 0
""")

# --- dropping a volume --------------------------------------------------------------------

_p("drop-gone", """
vol a
fil a p 4
wr a p 0 3
vol b
fil b q 4
wr b q 0 3
own a
rm a
tot
use b
""")

_p("drop-cascade", """
vol a
fil a p 4
wr a p 0 3
sn a b
tr a p 1 3
tr b p 1 3
tot
rm b
tot
at a p 0
""")

_p("drop-keeps", """
vol a
fil a p 4
wr a p 0 3
sn a b
rm b
tot
use a
at a p 2
""")

# --- the drop-gain query --------------------------------------------------------------------

_p("own-solo", """
vol a
fil a p 4
wr a p 0 3
own a
tot
""")

_p("own-pair", """
vol a
fil a p 6
wr a p 0 5
vol b
fil b q 6
cp a p 0 1 b q 0
tr a p 2 5
own a
own b
use a
tot
""")

_p("own-three", """
vol a
fil a p 4
wr a p 0 3
vol b
fil b q 4
cp a p 0 0 b q 0
vol c
fil c r 4
cp a p 0 0 c r 0
tr a p 1 3
own a
own b
tot
""")

_p("own-nogain", """
vol a
fil a p 4
wr a p 0 3
vol b
fil b q 4
cp a p 0 3 b q 0
tr a p 2 3
own a
own b
tot
""")

_p("own-dup", """
vol a
fil a p 6
wr a p 0 5
vol b
fil b q 6
cp a p 0 0 b q 0
cp a p 0 0 b q 1
tr a p 1 5
own a
own b
use b
tot
""")

_p("own-snap", """
vol a
fil a p 4
wr a p 0 3
sn a b
use a
use b
own a
own b
tot
""")

# --- the copy ---------------------------------------------------------------------------------

_p("cp-before", """
vol a
fil a p 4
wr a p 0 1
wr a p 2 3
cp a p 0 2 a p 1
at a p 0
at a p 1
at a p 2
at a p 3
tot
""")

_p("cp-empty", """
vol a
fil a p 4
wr a p 0 1
cp a p 2 2 a p 0
at a p 0
tot
""")

# --- what is printed ----------------------------------------------------------------------------

_p("line-order", """
vol a
fil a p 8
wr a p 0 1
wr a p 2 7
tr a p 0 5
at a p 6
tot
""")

_p("line-quiet", """
vol a
bulk a p 3 2
tot
use a
at a p 3
at a p 5
vol b
fil b q 2
tr b q 0 1
tot
own a
""")

ORDER = sorted(PROGS)


def ops(name):
    return list(PROGS[name])
