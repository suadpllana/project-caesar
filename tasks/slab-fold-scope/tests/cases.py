"""The enumerated programs: one per graded decision, plus the must-still-work side of each fence.

Each entry is named for the decision it pins, so a failure says which rule broke rather than
"one of the graded programs was wrong". `authoring/slab-fold-scope/readings.py` runs every
plausible wrong reading against this set and reports which case separates it; a reading that
this set does not separate is either promoted to a shipped case or shown to be a correct
variant.

The groups:

  put-*     the append that takes keys away from the slab holding them, and what `add` counts
  cut-*     what a cut removes and what it reports, including the two ways to be void
  fold-*    the reach of a re-pack: what is inside the range, what era it must be from, the
            two-slab floor, and the numbers the output keeps
  mixed-*   the slab holding keys from both sides of the base: when it forces a second attempt
            and when it does not, and what the second attempt starts from
  own-*     a proposal's own earlier parts, seen by its later ones
  void-*    the number a proposal does not take
"""

PROGS = {}


def _p(name, text):
    PROGS[name] = [line for line in text.strip().splitlines() if line.strip()]


# --- the append -----------------------------------------------------------------------

_p("put-fresh", """
plan a
put a v 0 19
push a
rows v
at v 0
at v 19
at v 20
""")

_p("put-steal", """
plan a
put a v 0 19
push a
plan b
put b v 10 29
push b
rows v
at v 5
at v 15
at v 25
""")

_p("put-add", """
plan a
put a v 0 19
push a
plan b
put b v 4 9
push b
rows v
at v 5
at v 12
""")

_p("put-refill", """
plan a
put a v 0 19
push a
plan b
cut b v 5 14
put b v 8 11
push b
rows v
at v 6
at v 9
at v 12
""")

# --- the cut --------------------------------------------------------------------------

_p("cut-count", """
plan a
put a v 0 9
push a
plan b
cut b v 5 24
push b
rows v
""")

_p("cut-twice", """
plan a
put a v 0 9
push a
plan b
cut b v 5 24
push b
plan c
cut c v 5 24
push c
rows v
""")

_p("cut-empty", """
plan a
put a v 0 9
push a
plan b
put b v 20 29
push b
plan c
cut c v 0 9
push c
at v 5
at v 25
rows v
""")

_p("cut-none", """
plan a
put a v 0 9
push a
plan b
cut b v 500 599
push b
plan c
put c v 20 29
push c
rows v
""")

# --- the re-pack ----------------------------------------------------------------------

_p("fold-plain", """
plan a
put a v 0 9
push a
plan b
put b v 20 29
push b
plan c
fold c v 0 99
push c
at v 5
at v 25
rows v
""")

_p("fold-floor", """
plan a
put a v 0 9
push a
plan z
fold z v 0 99
push z
at v 5
plan b
put b v 20 29
push b
""")

_p("fold-inside", """
plan a
put a v 0 9
push a
plan b
put b v 10 19
push b
plan c
put c v 20 29
push c
plan d
fold d v 0 24
push d
at v 5
at v 15
at v 25
""")

_p("fold-hole", """
plan a
put a v 0 9
push a
plan b
put b v 20 29
push b
plan c
fold c v 0 99
push c
at v 5
at v 15
at v 25
rows v
""")

_p("fold-era", """
plan a
put a v 0 9
push a
plan b
put b v 20 29
push b
plan y
fold y v 0 99
plan c
put c v 40 49
push c
push y
at v 5
at v 25
at v 45
""")

_p("fold-old-base", """
plan a
put a v 0 9
push a
plan b
put b v 20 29
push b
plan y
fold y v 0 199
plan c
put c v 100 109
push c
plan d
fold d v 0 99
push d
push y
at v 5
at v 25
at v 105
""")

_p("fold-keeps", """
plan a
put a v 0 9
push a
plan b
put b v 20 29
push b
plan e
put e v 60 69
push e
plan y
fold y v 0 99
plan d
fold d v 0 49
push d
push y
at v 5
at v 25
at v 65
""")

# --- the slab holding both eras -------------------------------------------------------

_p("mixed-retry", """
plan a
put a v 0 9
push a
plan e
put e v 60 69
push e
plan y
fold y v 0 99
plan b
put b v 20 29
push b
plan c
fold c v 0 49
push c
at v 5
at v 65
push y
at v 5
at v 25
at v 65
rows v
""")

# The two unmixing cases carry a slab at 80..89 that lands after the re-pack and is younger
# than the early proposal's base. Without it a second attempt reaches exactly the slabs a
# first attempt would have, and the case cannot tell an unmixed slab from a mixed one.

_p("mixed-cut-unmix", """
plan a
put a v 0 9
push a
plan e
put e v 60 69
push e
plan y
cut y v 20 29
fold y v 0 99
plan b
put b v 20 29
push b
plan c
fold c v 0 49
push c
plan d
put d v 80 89
push d
push y
at v 5
at v 25
at v 65
at v 85
rows v
""")

_p("mixed-put-unmix", """
plan a
put a v 0 9
push a
plan e
put e v 60 69
push e
plan y
put y v 20 29
fold y v 0 99
plan b
put b v 20 29
push b
plan c
fold c v 0 49
push c
plan d
put d v 80 89
push d
push y
at v 5
at v 25
at v 65
at v 85
rows v
""")

_p("mixed-two-folds", """
plan a
put a v 0 9
push a
plan b
put b v 20 29
push b
plan c
put c v 100 109
push c
plan d
put d v 120 129
push d
plan y
fold y v 0 49
fold y v 100 199
plan e
put e v 30 39
push e
plan f
put f v 140 149
push f
plan g
fold g v 100 199
push g
push y
at v 5
at v 25
at v 35
at v 105
at v 145
""")

_p("mixed-number", """
plan a
put a v 0 9
push a
plan b
put b v 20 29
push b
plan c
put c v 100 109
push c
plan d
put d v 120 129
push d
plan y
put y v 200 209
fold y v 100 199
plan e
put e v 140 149
push e
plan f
fold f v 100 199
push f
push y
at v 205
at v 105
""")

_p("mixed-elsewhere", """
plan a
put a v 0 9
push a
plan e
put e v 40 49
push e
plan b
put b v 200 209
push b
plan y
fold y v 0 99
plan c
put c v 20 29
push c
plan f
put f v 300 309
push f
plan g
fold g v 200 399
push g
push y
at v 5
at v 25
at v 45
at v 205
""")

_p("mixed-astride", """
plan a
put a v 0 9
push a
plan b
put b v 60 69
push b
plan y
fold y v 0 99
plan c
put c v 150 159
push c
plan d
fold d v 60 199
push d
plan e
put e v 30 39
push e
push y
at v 5
at v 35
at v 65
at v 155
""")

# A slab that the range only partly holds, whose keys inside the range straddle the base.
# Reading era off the runs a window happens to show, rather than off the whole slab, forces a
# second attempt here where none is due, and the two slabs at 40..49 and 80..89 are what makes
# the difference visible.

_p("mixed-part-astride", """
plan a
put a v 20 29
push a
plan y
fold y v 0 99
plan b
put b v 60 69
push b
plan c
put c v 150 159
push c
plan d
fold d v 0 199
push d
plan e
put e v 80 89
push e
plan f
put f v 40 49
push f
push y
at v 25
at v 45
at v 65
at v 85
at v 155
""")

# --- a proposal's own earlier parts ----------------------------------------------------

_p("own-part", """
plan a
put a v 0 9
push a
plan b
put b v 20 29
push b
plan y
put y v 40 49
fold y v 0 99
push y
at v 5
at v 25
at v 45
""")

# A fold ahead of a put in the same proposal. Running the folds after the other parts gives
# the fold a slab the put has just made, which its era keeps out of reach, and the two orders
# leave different slabs behind.

_p("own-fold-first", """
plan a
put a v 0 9
push a
plan b
put b v 20 29
push b
plan y
fold y v 0 99
put y v 0 9
push y
at v 5
at v 25
rows v
""")

_p("own-buckets", """
plan a
put a v 0 9
push a
plan b
put b w 0 9
push b
plan y
put y v 20 29
cut y w 5 9
fold y v 0 99
push y
rows v
rows w
at v 5
at w 3
""")

# --- the number a proposal does not take ----------------------------------------------

_p("void-number", """
plan a
put a v 0 9
push a
plan z
cut z v 500 599
push z
plan b
put b v 20 29
push b
plan y
fold y v 0 99
push y
at v 5
""")

ORDER = sorted(PROGS)


def ops(name):
    return PROGS[name]
