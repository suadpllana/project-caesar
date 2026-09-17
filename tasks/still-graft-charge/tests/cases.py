"""The enumerated programs: one per graded decision, plus the must-still-work side of each fence.

Each entry is named for the decision it pins, so a failure says which rule broke rather than
"one of the graded programs was wrong". `authoring/still-graft-charge/readings.py` runs every
plausible wrong reading against this set and reports which case separates it; a reading this
set does not separate is either promoted to a shipped case or shown to be a correct variant.

The groups:

  put-*     what a put makes, what it takes over, and the number it carries
  still-*   what a still holds, and why taking one moves no charge
  graft-*   what a graft's head starts as, and what happens to the line above as it diverges
  lift-*    which stills a lift moves, what it does to the two origins, and to the charges
  drop-*    what a drop is refused, and what it actually releases
  cap-*     the charge a put has to leave the line under, from both sides
  cut-*     what a cut stops holding, and what that releases
"""

PROGS = {}


def _p(name, text):
    PROGS[name] = [line for line in text.strip().splitlines() if line.strip()]


# --- what a put makes -----------------------------------------------------------------

_p("put-fresh", """
line p
put p 0 3 5
ask p
at p 0
at p 3
at p 4
""")

_p("put-over", """
line p
put p 0 3 5
put p 1 2 7
ask p
at p 1
""")

_p("put-keep", """
line p
put p 0 1 5
still p a
put p 0 1 9
ask p
drop a
ask p
""")

_p("put-number", """
line p
cap p 5
put p 0 0 5
put p 1 1 5
cut p 0 0
put p 1 1 5
at p 0
at p 1
""")

# --- what a still holds ---------------------------------------------------------------

_p("still-frozen", """
line p
put p 0 1 4
still p a
put p 0 0 6
graft a q
ask p
ask q
at q 0
""")

_p("still-lines", """
line p
put p 0 0 7
still p a
still p b
still p c
ask p
""")

_p("still-empty", """
line p
still p a
graft a q
put q 0 0 4
ask p
ask q
""")

# --- what a graft starts as ------------------------------------------------------------

_p("graft-share", """
line p
put p 0 2 5
still p a
graft a q
ask p
ask q
""")

_p("graft-diverge", """
line p
put p 0 2 5
still p a
graft a q
put q 0 0 3
ask p
ask q
""")

_p("graft-cut", """
line p
put p 0 2 5
still p a
graft a q
cut q 1 1
ask p
ask q
""")

_p("graft-chain", """
line p
put p 0 1 5
still p a
graft a q
still q b
graft b r
put r 0 0 3
ask p
ask q
ask r
""")

# --- the lift ---------------------------------------------------------------------------

_p("lift-prefix", """
line p
put p 0 1 4
still p a
put p 0 0 6
still p b
graft b q
put p 0 0 9
still p c
cut p 0 0
ask p
ask q
lift q
ask p
ask q
""")

_p("lift-swap", """
line p
put p 0 1 4
still p a
graft a q
put q 0 0 7
cut p 0 1
lift q
ask p
ask q
lift p
ask p
ask q
""")

_p("lift-root", """
line p
put p 0 0 3
lift p
ask p
""")

_p("lift-busy", """
line p
put p 0 1 4
still p a
graft a q
lift q
drop a
ask p
ask q
""")

# --- the drop -----------------------------------------------------------------------------

_p("drop-busy", """
line p
put p 0 1 6
still p a
graft a q
drop a
ask p
ask q
""")

_p("drop-none", """
line p
put p 0 1 5
still p a
drop a
ask p
""")

_p("drop-some", """
line p
put p 0 0 5
still p a
put p 0 0 6
drop a
ask p
""")

_p("drop-other", """
line p
put p 0 0 5
still p a
still p b
put p 0 0 6
drop a
drop b
ask p
""")

_p("drop-graft", """
line p
put p 0 1 5
still p a
graft a q
put q 0 1 2
still p b
put p 0 1 8
drop b
ask p
ask q
""")

# --- the cap -------------------------------------------------------------------------------

_p("cap-fit", """
line p
put p 0 3 5
cap p 20
put p 0 3 5
ask p
""")

_p("cap-over", """
line p
put p 0 3 5
cap p 20
put p 4 4 1
ask p
at p 4
""")

_p("cap-still", """
line p
put p 0 1 5
cap p 20
still p a
put p 0 1 5
ask p
""")

_p("cap-cross", """
line p
put p 0 1 5
still p a
graft a q
cap p 12
put p 2 2 6
ask p
put q 0 0 3
ask p
put p 3 3 2
ask p
at p 3
""")

_p("cap-none", """
line p
put p 0 5 9
put p 0 5 9
put p 0 5 9
ask p
""")

# --- the cut --------------------------------------------------------------------------------

_p("cut-hold", """
line p
put p 0 1 5
still p a
cut p 0 0
ask p
drop a
ask p
""")

_p("cut-free", """
line p
put p 0 1 5
cut p 0 0
ask p
at p 0
at p 1
""")


ORDER = sorted(PROGS)


def ops(name):
    return PROGS[name]
