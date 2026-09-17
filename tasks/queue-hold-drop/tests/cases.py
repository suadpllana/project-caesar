"""The enumerated programs: one per graded decision, plus the must-still-work side of each fence.

Each is named for the rule it pins, so a failure says which rule broke rather than "one of the
graded programs was wrong". `authoring/queue-hold-drop/readings.py` runs every plausible wrong
reading against this set and reports which case separates it; a reading nothing here separates
is either shipped as a new case or shown to be a correct variant.

The groups:

  hold-*    which changes may go out, and how one that stays behind holds later ones
  name-*    which records a change names, which is what holding and taking away are about
  ans-*     which change an answer lands on, and the answer with nothing to answer
  take-*    acceptance: the confirmed records, the id, and the identity the ack prints
  gone-*    refusal: what it takes off the queue besides the change refused
  stop-*    the removal of a record the server has never confirmed
  reach-*   the records a removal takes, decided when the change is laid over, and the move
            that would put a record under itself
  lay-*     what one change does to the records it is laid over, including doing nothing
  view-*    the laid-over view: what is in it and the order it comes out in
  say-*     the printed shapes
"""

PROGS = {}


def _p(name, text):
    PROGS[name] = [line for line in text.strip().splitlines() if line.strip()]


# --- which changes go out -------------------------------------------------------------

_p("hold-plain", """
oth new q1 -
set q1 w 4
add q1 h 2
mov q1 -
snd
ask q1
""")

_p("hold-wait", """
oth new q1 -
new a q1
set a w 1
snd
ask a
""")

_p("hold-new-own", """
oth new q1 -
new a q1
new b q1
snd
""")

_p("hold-new-up", """
oth new q1 -
new a q1
new b a
snd
""")

_p("hold-spread", """
oth new q1 -
oth new q2 -
oth new q3 -
new a q1
mov q2 a
mov q3 q2
set q3 w 1
set q1 h 5
snd
""")

_p("hold-spread-far", """
oth new q1 -
oth new q2 -
new a q1
mov q2 a
set q2 w 3
snd
""")

_p("hold-again", """
oth new q1 -
new a q1
set a w 6
snd
ok
snd
ask a
""")

# --- what a change names --------------------------------------------------------------

_p("name-mov-up", """
oth new q1 -
oth new q2 -
new a q1
mov q2 a
snd
""")

_p("name-set-one", """
oth new q1 -
oth new q2 -
new a q1
set a w 1
set q2 h 2
snd
""")

# --- which change an answer lands on ----------------------------------------------------

_p("ans-sent", """
oth new q1 -
new a q1
snd
new b a
set q1 w 9
snd
ok
ok
ask q1
""")

_p("ans-idle", """
oth new q1 -
set q1 w 1
ok
no
ask q1
""")

_p("ans-idle-after", """
oth new q1 -
set q1 w 1
snd
ok
ok
ask q1
""")

# --- acceptance -------------------------------------------------------------------------

_p("take-id", """
oth new q1 -
new a q1
snd
ok
ask a
""")

_p("take-order", """
oth new q1 -
new a q1
snd
new b q1
snd
ok
ok
ask a
ask b
""")

_p("take-base", """
oth new q1 -
add q1 w 3
snd
ok
ask q1
add q1 w 3
snd
ok
ask q1
""")

_p("take-gone-up", """
oth new q1 -
new a q1
snd
oth cut q1
ok
ask a
all
""")

# --- refusal ------------------------------------------------------------------------------

_p("gone-one", """
oth new q1 -
oth new q2 -
set q1 w 1
set q2 h 2
snd
no
ask q1
ask q2
""")

_p("gone-kids", """
oth new q1 -
new a q1
new b a
set b w 1
snd
no
ask q1
""")

_p("gone-chain", """
oth new q1 -
oth new q2 -
new a q1
new b a
mov q2 b
set q2 w 7
snd
no
ask q2
""")

_p("gone-back", """
oth new q1 -
new a q1
snd
set a w 5
set q1 h 2
snd
ok
no
snd
ask a
ask q1
""")

_p("gone-front", """
oth new q1 -
new a q1
snd
mov a q1
set q1 w 5
snd
ok
no
snd
ask a
ask q1
""")

_p("gone-sent", """
oth new q1 -
oth new q2 -
set q1 w 4
add q1 h 1
set q2 k 2
snd
no
ok
ok
ask q1
ask q2
""")

# --- the removal of a record the server has never confirmed --------------------------------

_p("stop-cut", """
oth new q1 -
new a q1
set a w 1
cut a
snd
ask a
all
""")

_p("stop-id", """
oth new q1 -
new a q1
new b q1
cut a
snd
ok
ask b
""")

_p("stop-away", """
oth new q1 -
oth new q2 -
new a q1
mov q2 a
set q2 w 3
cut a
snd
ask q2
all
""")

_p("stop-kept", """
oth new q1 -
oth new q2 q1
cut q2
snd
ask q2
""")

_p("stop-side", """
oth new q1 -
new a q1
new b q1
set b w 5
cut a
snd
all
""")

# --- what a removal takes, and the move that would put a record under itself ----------------

_p("reach-under", """
oth new q1 -
oth new q2 q1
oth new q3 q2
cut q1
ask q2
ask q3
""")

_p("reach-late", """
oth new q1 -
oth new q2 -
cut q1
ask q2
oth mov q2 q1
ask q2
""")

_p("reach-out", """
oth new q1 -
oth new q2 q1
cut q1
ask q2
oth mov q2 -
ask q2
""")

_p("reach-cycle", """
oth new q1 -
oth new q2 q1
oth new q3 q2
mov q1 q3
ask q1
ask q3
""")

_p("reach-top", """
oth new q1 -
oth new q2 q1
mov q2 -
ask q2
""")

# --- what one change does to the records it is laid over -------------------------------------

_p("lay-miss", """
oth new q1 -
oth cut q1
set q1 w 5
add q1 h 1
mov q1 -
ask q1
all
""")

_p("lay-add", """
oth new q1 -
oth set q1 w 10
add q1 w 5
add q1 w 5
ask q1
""")

_p("lay-add-base", """
oth new q1 -
add q1 w 5
ask q1
oth set q1 w 40
ask q1
""")

_p("lay-up-miss", """
oth new q1 -
new a q9
set a w 1
all
""")

# --- the laid-over view ------------------------------------------------------------------------

_p("view-sent", """
oth new q1 -
set q1 w 3
snd
ask q1
ok
ask q1
""")

_p("view-order", """
oth new q1 -
new a -
oth new q2 -
new b -
all
""")

_p("view-order-move", """
oth new q1 -
new a -
new b -
all
snd
ok
all
""")

# --- the printed shapes --------------------------------------------------------------------------

_p("say-fields", """
oth new q1 -
set q1 w 1
set q1 h 2
set q1 k 0
add q1 n 4
ask q1
""")

_p("say-top", """
oth new q1 -
oth new q2 q1
ask q1
ask q2
oth cut q1
ask q2
""")


ORDER = sorted(PROGS)


def ops(name):
    return list(PROGS[name])
