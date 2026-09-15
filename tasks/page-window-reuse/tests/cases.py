"""The enumerated programs: one per graded decision, plus the must-still-work side of each fence.

Each entry is named for the decision it pins, so a failure says which rule broke rather than
"one of the graded programs was wrong". `authoring/page-window-reuse/readings.py` runs every
plausible wrong reading against this set and reports which case separates it; a reading the
set does not separate is either promoted to a shipped case or shown to be a correct variant.

The groups:

  fill-*    what a fill holds while it runs and what it lets go when the prompt is complete
  live-*    residency: the first tokens, the last tokens, and the short prompt that keeps all
  walk-*    reuse: how far a walk from the start of the prompt gets, and what it takes
  rest-*    where a page goes when its last holder leaves it
  back-*    the take-back: which page, what comes back with it, and what is left out of reach
  kick-*    preemption: who, when, what it releases and what that is worth
  twin-*    a page completing onto tokens that already sit below the same page
  turn-*    the step: the two phases, the budget, the page boundary and the queue
  end-*     finishing and cancelling
"""

PROGS = {}


def _p(name, text):
    PROGS[name] = [line for line in text.strip().splitlines() if line.strip()]


# --- what a fill holds, and what it lets go -------------------------------------------

_p("fill-hold-all", """
pool 3 4 4 4 4
ask a 12:1 2:5
ask b 4:2 2:6
step
step
step
at a 0
at a 4
at a 8
step
""")

_p("fill-lets-go", """
pool 8 4 4 4 16
ask a 16:1 2:5
step
at a 0
at a 4
at a 8
at a 12
ask b 8:2 2:6
step
at b 0
""")

_p("fill-short-keeps", """
pool 8 4 8 8 16
ask a 8:1 2:5
step
at a 0
at a 4
step
at a 0
at a 4
""")

_p("fill-holds-middle", """
pool 3 4 0 1 8
ask a 20:1 2:5
step
step
step
at a 16
at a 0
""")

# --- residency ------------------------------------------------------------------------

_p("live-sink-stays", """
pool 12 4 4 4 16
ask a 12:1 8:5
step
step
step
step
at a 0
at a 4
at a 8
at a 16
""")

_p("live-no-sink", """
pool 12 4 0 4 16
ask a 12:1 8:5
step
at a 0
step
step
at a 0
at a 8
at a 12
""")

_p("live-window-edge", """
pool 12 4 4 6 16
ask a 16:1 4:5
step
at a 4
at a 8
at a 12
step
at a 4
at a 8
""")

# --- reuse ------------------------------------------------------------------------------

_p("walk-whole", """
pool 12 4 4 4 16
ask a 12:1 2:5
step
ask b 12:1 2:6
step
at b 0
at b 4
at b 8
""")

_p("walk-held", """
pool 12 4 4 4 16
ask a 8:1 6:5
step
step
ask b 8:1 2:6
step
at b 0
at b 4
""")

_p("walk-stops-at-gap", """
pool 6 4 4 4 8
ask a 12:1 6:5
step
step
ask b 8:2 2:6
step
step
ask c 12:1 2:7
step
at c 0
at c 4
at c 8
""")

_p("walk-part-page", """
pool 12 4 4 4 16
ask a 10:1 2:5
step
ask b 10:1 2:6
step
at b 0
at b 8
""")

# --- where a released page goes ----------------------------------------------------------

_p("rest-reusable", """
pool 6 4 4 4 8
ask a 8:1 1:5
step
step
ask b 8:2 1:6
step
step
ask c 8:1 1:7
step
at c 0
at c 4
""")

_p("rest-free-at-once", """
pool 6 4 4 4 12
ask a 12:1 4:5
step
ask b 8:2 2:6
step
step
ask c 12:1 2:7
step
at c 0
at c 4
step
""")

_p("rest-strand-frees", """
pool 5 4 4 4 8
ask a 12:1 6:5
step
step
ask b 8:2 1:6
step
step
step
step
ask c 4:3 1:7
step
at c 0
at a 8
""")

# --- the take-back ------------------------------------------------------------------------

_p("back-oldest", """
pool 6 4 4 4 12
ask a 12:1 1:5
step
step
ask b 8:2 1:6
step
ask c 8:3 1:7
step
step
""")

_p("back-strand", """
pool 6 4 4 4 24
ask a 20:1 1:5
step
step
ask b 12:2 1:6
step
""")

_p("back-under-part", """
pool 5 4 4 4 8
ask a 8:1 8:5
step
step
step
step
ask b 8:2 1:6
step
ask c 8:1 1:7
step
at c 0
at c 4
""")

# --- preemption ------------------------------------------------------------------------

_p("kick-newest", """
pool 4 4 4 4 8
ask a 8:1 8:5
ask b 8:2 8:6
step
step
step
at a 0
at b 0
""")

_p("kick-alone", """
pool 2 4 4 4 8
ask a 12:1 2:5
step
step
step
""")

_p("kick-ends-turn", """
pool 4 4 4 4 16
ask a 8:1 8:5
ask b 8:2 8:6
ask c 4:3 2:7
step
step
step
step
""")

# --- a page completing onto tokens already below the same page ----------------------------

_p("twin-hands-back", """
pool 12 4 4 8 12
ask a 8:1 8:5
step
step
step
step
step
ask b 8:1 8:5
step
step
step
step
step
at a 8
at b 8
at b 4
""")

_p("twin-other-prev", """
pool 12 4 4 8 12
ask a 8:1 8:5
step
step
step
step
step
ask b 8:2 8:5
step
step
step
step
step
at a 8
at b 8
""")

# --- the step -------------------------------------------------------------------------

_p("turn-decode-first", """
pool 8 4 4 4 4
ask a 4:1 4:5
step
ask b 4:2 2:6
step
step
at a 4
at b 0
""")

_p("turn-page-edge", """
pool 8 4 4 4 6
ask a 8:1 2:5
step
at a 0
at a 4
step
at a 0
at a 4
""")

_p("turn-no-jump", """
pool 8 4 4 4 6
ask a 12:1 2:5
ask b 2:2 2:6
step
step
at b 0
step
at b 0
""")

_p("turn-reuse-free", """
pool 12 4 4 4 4
ask a 8:1 2:5
step
step
ask b 8:1 2:6
step
at b 0
at b 4
""")

_p("back-free-first", """
pool 8 4 4 4 12
ask a 8:1 1:5
step
step
ask b 8:2 1:6
step
at b 0
at b 4
""")

_p("back-order-of-release", """
pool 4 4 4 8 16
ask a 8:1 1:5
step
step
ask b 12:2 1:6
step
at b 0
at b 8
""")

# --- finishing and cancelling ---------------------------------------------------------

_p("end-done-frees", """
pool 6 4 4 4 8
ask a 8:1 2:5
step
step
step
ask b 8:2 2:6
step
at b 0
at b 4
""")

_p("end-stop-waiting", """
pool 4 4 4 4 4
ask a 8:1 2:5
ask b 8:2 2:6
step
stop b
step
step
at a 0
at a 4
""")

_p("end-stop-part", """
pool 4 4 4 4 4
ask a 12:1 2:5
step
step
stop a
ask b 12:2 2:6
step
step
step
at b 0
at b 8
""")

_p("end-stop-live", """
pool 4 4 4 4 8
ask a 8:1 4:5
step
ask b 8:2 2:6
step
stop a
step
at b 0
at b 4
""")

ORDER = tuple(sorted(PROGS))


def ops(name):
    return list(PROGS[name])
