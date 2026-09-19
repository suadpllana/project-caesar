"""The enumerated programs: one per graded decision, and both sides of every fence.

Each one is small enough that its whole trace can be read by hand, and the name of a case is
the name of the rule it pins, so a failure says which rule broke rather than "a generated
program came out wrong".

  match-plain          a link takes the rows whose column holds the key; empty and dangling are not those rows
  out-deep-first       a removal comes out children first, the changed row last
  group-longest        a row met again by a longer chain sits at the longer one
  group-order-table    one group, two tables: declaration order
  group-order-key      one group, one table: key order
  group-order-col      one row, two columns: column order
  drop-over-clear      a row taken out ignores the column another link would have cleared
  drop-first-link      two links taking one row out: the line names the one declared first
  col-first-link       two links on one column: the one declared first decides it
  clear-stays          a cleared row is still there, so nothing carries on from it
  mov-shallow-first    a re-key comes out the other way up, the changed row first
  follow-key-carries   a follow onto a key column re-keys that row and carries on from it
  follow-plain-stops   a follow onto any other column stops there
  move-and-clear       one row re-keyed and cleared in one change, both lines naming the old key
  kind-picks-action    the same link acts one way for a removal and another for a re-key
  clash-held           a key another row already holds stops the change
  clash-noop           a row given the key it already has is not a clash
  bar-on-removed-row   a restrict link fires on a row the change would itself have removed
  bar-quiet            a restrict link with no row pointing through it does not fire
  bar-pick-first       two restricts: the link declared first, then the smaller key
  bar-nothing-applied  a change stopped by a restrict leaves the store as it found it
  wait-after-change    a deferred link is answered from the store the change leaves
  wait-child-removed   a row the change removes cannot be the one left dangling
  wait-dangle-stands   a pointer that was already dangling stops nothing
  wait-pick-first      two deferred hits: the link declared first, then the smaller key
  wait-undone          a change stopped by a deferred link is walked back, rows and all
  undo-cols            the walk-back puts cleared columns and moved keys back too
  none-missing         a change naming a key that is not there does nothing and says so
  ordinary-quiet       links everywhere and nothing to do but the change itself
"""

CASES = {
    # --- what a link matches -------------------------------------------------------
    "match-plain": """
tab a k
tab b k p
link l1 b p a drop follow
put a 1
put b 10 1
put b 11 -
put b 12 7
out a 1
""",

    # --- the order a change comes out in -------------------------------------------
    "out-deep-first": """
tab a k
tab b k p
tab c k p
link l1 b p a drop follow
link l2 c p b drop follow
put a 1
put b 10 1
put c 20 10
out a 1
""",
    "group-longest": """
tab a k
tab b k p
tab c k p q
link l1 b p a drop follow
link l2 c p a drop follow
link l3 c q b drop follow
put a 1
put b 10 1
put c 20 1 10
out a 1
""",
    "group-order-table": """
tab a k
tab b k p
tab c k p
link l1 b p a drop follow
link l2 c p a drop follow
put a 1
put b 30 1
put c 20 1
out a 1
""",
    "group-order-key": """
tab a k
tab b k p
link l1 b p a drop follow
put a 1
put b 30 1
put b 10 1
out a 1
""",
    "group-order-col": """
tab a k
tab c k x y
link l1 c y a clear clear
link l2 c x a clear clear
put a 5
put c 20 5 5
out a 5
""",

    # --- what a row ends up taking --------------------------------------------------
    "drop-over-clear": """
tab a k
tab b k p
tab c k p q
link l1 b p a drop follow
link l2 c q a clear clear
link l3 c p b drop follow
put a 1
put b 10 1
put c 20 10 1
out a 1
""",
    "drop-first-link": """
tab a k
tab q k p
tab c k x y
link l1 q p a drop follow
link l2 c x q drop follow
link l3 c y a drop follow
put a 5
put q 5 5
put c 20 5 5
out a 5
""",
    "col-first-link": """
tab a k
tab q k p
tab c k x
link l1 q p a drop follow
link l2 c x q clear clear
link l3 c x a clear clear
put a 5
put q 5 5
put c 20 5
out a 5
""",
    "clear-stays": """
tab a k
tab b k p
tab c k p
link l1 b p a clear clear
link l2 c p b drop follow
put a 1
put b 10 1
put c 20 10
out a 1
""",

    # --- re-keying ------------------------------------------------------------------
    "mov-shallow-first": """
tab a k
tab b k p
tab c k p
link l1 b p a drop follow
link l2 c p b drop follow
put a 1
put b 10 1
put c 20 10
mov a 1 7
""",
    "follow-key-carries": """
tab a k
tab b k
tab c k p
link l1 b k a drop follow
link l2 c p b drop follow
put a 3
put b 3
put c 20 3
mov a 3 8
""",
    "follow-plain-stops": """
tab a k
tab b k p
tab c k p
link l1 b p a drop follow
link l2 c p b drop follow
put a 3
put b 10 3
put c 20 10
mov a 3 8
""",
    "move-and-clear": """
tab a k
tab q k
tab c k y
link l1 q k a drop follow
link l2 c k a drop follow
link l3 c y q clear clear
put a 5
put q 5
put c 5 5
mov a 5 8
""",
    "kind-picks-action": """
tab a k
tab b k p
link l1 b p a bar follow
put a 1
put b 10 1
mov a 1 7
out a 7
""",
    "clash-held": """
tab a k
put a 1
put a 2
mov a 1 2
out a 1
""",
    "clash-noop": """
tab a k x
put a 1 -
mov a 1 1
""",

    # --- the restrict links ---------------------------------------------------------
    "bar-on-removed-row": """
tab a k
tab b k p q
link l1 b p a drop follow
link l2 b q a bar follow
put a 1
put b 10 1 1
out a 1
""",
    "bar-quiet": """
tab a k
tab b k p q
link l1 b p a drop follow
link l2 b q a bar follow
put a 1
put b 10 1 -
out a 1
""",
    "bar-pick-first": """
tab a k
tab b k p
tab c k p
link l1 b p a bar follow
link l2 c p a bar follow
put a 1
put b 30 1
put b 10 1
put c 20 1
out a 1
""",
    "bar-nothing-applied": """
tab a k
tab b k p q
link l1 b p a drop follow
link l2 b q a bar follow
put a 1
put a 2
put b 10 1 1
out a 1
mov a 2 5
out a 1
""",

    # --- the deferred links ---------------------------------------------------------
    "wait-after-change": """
tab a k
tab b k p
link l1 b p a wait wait
put a 1
put b 10 1
out a 1
""",
    "wait-child-removed": """
tab a k
tab b k p q
link l1 b p a drop follow
link l2 b q a wait wait
put a 1
put b 10 1 1
out a 1
""",
    "wait-dangle-stands": """
tab a k
tab b k p
link l1 b p a wait wait
put a 1
put a 2
put b 10 7
out a 1
""",
    "wait-pick-first": """
tab a k
tab b k p
tab c k p
link l1 b p a wait wait
link l2 c p a wait wait
put a 1
put b 30 1
put b 10 1
put c 20 1
out a 1
""",
    "wait-undone": """
tab a k
tab b k p
tab c k p
link l1 b p a drop follow
link l2 c p a wait wait
put a 1
put b 10 1
put c 20 1
out a 1
out a 1
""",
    "undo-cols": """
tab a k
tab q k
tab c k y
tab d k p
link l1 q k a drop follow
link l2 c y q clear clear
link l3 d p a wait wait
put a 5
put q 5
put c 20 5
put d 30 5
mov a 5 8
mov a 5 9
""",

    # --- nothing to do ---------------------------------------------------------------
    "none-missing": """
tab a k
put a 1
out a 9
mov a 9 3
out a 1
""",
    "ordinary-quiet": """
tab a k
tab b k p
tab c k p
link l1 b p a drop follow
link l2 c p b bar follow
put a 1
put a 2
put b 10 2
put c 20 30
out a 1
""",
}

ORDER = sorted(CASES)


def prog(name):
    """One enumerated program, as the lines of a program file."""
    return CASES[name].strip().splitlines()
