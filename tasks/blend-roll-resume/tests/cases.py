"""The enumerated scripts: one per graded decision, plus the must-still-work side of each fence.

Each is named for the decision it pins, so a failure says which rule broke rather than "one of
the graded scripts was wrong". `authoring/blend-roll-resume/readings.py` runs every plausible
wrong reading against this set and reports which case separates it; a reading this set does not
separate is either promoted to a shipped case or shown to be a correct variant.

The groups:

  pick-*   which source a draw goes to, and what breaks a tie
  base-*   the counters going back to zero when the blend changes, and when they must not
  roll-*   the cursor, the epoch boundary and the permutation that comes with it
  cap-*    a source leaving instead of starting the epoch its cap names, and the `done` line
  lay-*    which draws of a step reach which rank and slot
  back-*   what a stop puts back and what it leaves alone
  show-*   a feed as a question: what it reports and what it must not change
  join-*   a source declared while the run is going
"""

PROGS = {}


def _p(name, text):
    PROGS[name] = [line for line in text.strip().splitlines() if line.strip()]


# --- which source a draw goes to -------------------------------------------------------

_p("pick-tie-order", """
seed 11
src ab 4 2 0
src cd 4 2 0
run 1 1 2
feed 0 0
feed 0 1
""")

_p("pick-tie-weight", """
seed 12
src ab 6 1 0
src cd 6 3 0
run 1 1 1
feed 0 0
go 1
feed 0 0
""")

_p("pick-ratio", """
seed 13
src ab 8 3 0
src cd 8 1 0
run 1 4 1
feed 0 0
go 1
feed 0 0
""")

# --- the counters and the blend --------------------------------------------------------

_p("base-weigh", """
seed 21
src ab 5 1 0
src cd 5 3 0
run 1 3 1
go 2
feed 0 0
wt cd 1
feed 0 0
""")

_p("base-weigh-same", """
seed 22
src ab 5 1 0
src cd 5 3 0
run 1 2 1
go 2
feed 0 0
wt cd 3
feed 0 0
""")

_p("base-depart", """
seed 23
src ab 7 1 0
src cd 7 2 0
src ef 2 1 1
run 1 2 1
go 1
feed 0 0
go 3
feed 0 0
at ef
""")

_p("base-hold", """
seed 24
src ab 9 2 0
src cd 9 1 0
run 1 3 1
go 1
feed 0 0
go 1
feed 0 0
""")

# --- the cursor and the epoch ----------------------------------------------------------

_p("roll-over", """
seed 31
src ab 3 1 0
run 1 1 1
at ab
go 3
at ab
go 1
at ab
feed 0 0
""")

_p("roll-edge", """
seed 32
src ab 4 1 0
run 1 2 1
go 1
at ab
go 1
at ab
""")

_p("roll-share", """
seed 33
src ab 2 1 0
src cd 5 2 0
run 1 3 1
go 2
at ab
at cd
feed 0 0
""")

# --- the cap -----------------------------------------------------------------------

_p("cap-edge", """
seed 41
src ab 9 1 0
src cd 3 1 1
run 1 1 2
go 3
at cd
at ab
""")

_p("cap-two", """
seed 42
src ab 9 1 0
src cd 2 1 2
run 1 1 2
go 3
at cd
at ab
""")

_p("cap-none", """
seed 43
src ab 2 1 0
src cd 3 1 0
run 1 2 1
go 6
at ab
at cd
""")

_p("cap-first-draw", """
seed 44
src ab 9 1 0
src cd 1 1 1
run 1 1 1
feed 0 0
go 1
go 1
at cd
""")

_p("cap-last-draw", """
seed 45
src ab 9 3 0
src cd 1 1 1
run 1 4 1
go 1
at cd
at ab
""")

_p("cap-two-out", """
seed 46
src ab 9 1 0
src cd 2 1 1
src ef 2 1 1
run 1 2 1
go 4
at cd
at ef
at ab
""")

# --- where a step's draws go -------------------------------------------------------

_p("lay-spread", """
seed 51
src ab 20 2 0
src cd 20 1 0
run 2 2 2
feed 0 0
feed 1 0
feed 0 1
feed 1 1
""")

_p("lay-single", """
seed 52
src ab 20 2 0
src cd 20 1 0
run 1 2 3
feed 0 0
feed 0 1
feed 0 2
""")

# --- the checkpoint ----------------------------------------------------------------

_p("back-plain", """
seed 61
src ab 12 2 0
src cd 12 1 0
run 1 2 2
go 1
save
go 1
feed 0 0
stop
run 1 2 2
feed 0 0
go 1
feed 0 0
""")

_p("back-step", """
seed 62
src ab 20 1 0
src cd 6 1 1
run 1 2 1
go 1
save
go 1
stop
run 1 2 1
go 5
at cd
""")

_p("back-blend", """
seed 63
src ab 20 1 0
src cd 2 1 1
run 1 2 1
go 1
save
go 1
at cd
stop
run 1 2 1
at cd
at ab
feed 0 0
""")

_p("back-weight", """
seed 64
src ab 12 1 0
src cd 12 1 0
run 1 2 1
go 1
save
wt cd 5
stop
run 1 4 1
feed 0 0
""")

_p("back-rebase", """
seed 65
src ab 12 1 0
src cd 12 3 0
src ef 1 1 1
run 1 2 1
go 1
save
go 1
stop
run 1 2 1
feed 0 0
at ef
""")

_p("back-swap", """
seed 67
src ab 12 1 0
src cd 12 3 0
run 1 3 1
go 1
save
go 1
wt ab 3
wt cd 1
stop
run 1 3 1
feed 0 0
""")

_p("back-hold", """
seed 66
src ab 12 1 0
src cd 12 3 0
run 1 3 1
wt cd 3
go 1
save
go 2
stop
run 1 3 1
feed 0 0
""")

# --- a feed is a question ----------------------------------------------------------

_p("show-twice", """
seed 71
src ab 9 2 0
src cd 9 1 0
run 1 2 1
feed 0 0
feed 0 0
go 1
feed 0 0
""")

_p("show-quiet", """
seed 72
src ab 9 1 0
src cd 1 1 1
run 1 2 1
feed 0 0
at cd
go 1
at cd
""")

_p("show-tail", """
seed 73
src ab 20 3 0
src cd 20 1 0
run 2 1 3
feed 1 2
go 1
feed 0 0
""")

# --- a source declared while the run is going --------------------------------------

_p("join-mid", """
seed 81
src ab 9 1 0
run 1 2 1
go 1
feed 0 0
src cd 9 3 0
feed 0 0
at cd
""")

_p("join-back", """
seed 82
src ab 12 1 0
run 1 2 1
go 1
save
src cd 6 1 0
go 1
at cd
stop
run 1 2 1
at cd
at ab
feed 0 0
""")

_p("join-cap", """
seed 83
src ab 12 1 0
run 1 2 1
go 1
src cd 2 1 1
go 2
at cd
at ab
""")

ORDER = sorted(PROGS)


def ops(name):
    return PROGS[name]
