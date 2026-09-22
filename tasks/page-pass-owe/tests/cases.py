"""The enumerated list files: one per graded decision, and both sides of every fence.

A generated population says a submission is wrong; these say which rule it got wrong. Each
name below is the rule the program pins, and each program is built so that exactly one
reading of that rule survives it. The must-still-work side is named too - `plain-run`,
`empty-not`, `owe-after`, `tag-back` - because a service that turns conservative and owes
or re-hands everything has to fail somewhere as well.

`tools/readingcheck.py` is what keeps this honest: it drives each wrong reading against
this set and reports any that the set does not separate.
"""

CASES = {

    # -- order and view ----------------------------------------------------------------

    # Place order is the key and then the id; sorting by key alone leaves these in
    # arrival order, which is a different page.
    "order-tie": """
cfg 100
row 5 2 0 1
row 3 2 0 1
row 9 1 0 1
open 1 0 5 20
next 1
""",

    # The plain key ordering, with arrival order unrelated to it.
    "order-key": """
cfg 100
row 1 7 0 1
row 2 3 0 1
row 3 5 0 1
open 1 0 5 20
next 1
""",

    # A scroll sees only its own tag, so row 2 is never in this page and never counted.
    "view-tag": """
cfg 100
row 1 1 0 1
row 2 2 1 1
row 3 3 0 1
open 1 0 5 20
next 1
""",

    # -- the ledger phase ---------------------------------------------------------------

    # The ledger is a queue: the entry at the front does not fit, so the phase stops even
    # though the entry behind it would have fitted.
    "led-front": """
cfg 100
row 1 1 0 3
row 2 9 0 1
open 1 0 5 6
next 1
add 3 2 0 2
add 4 3 0 9
add 5 4 0 2
next 1
""",

    # Ledger order is the order rows came to be owed, which here is the reverse of their
    # place order.
    "led-order": """
cfg 100
row 1 1 0 2
row 2 9 0 1
open 1 0 5 6
next 1
add 5 4 0 1
add 3 2 0 1
add 4 3 0 1
next 1
""",

    # -- the empty-page rule -------------------------------------------------------------

    # A ledger front heavier than a whole page goes out alone and spends the page's weight,
    # so the light entry behind it waits for the next page.
    "empty-head": """
cfg 100
row 1 1 0 2
row 2 9 0 1
open 1 0 5 6
next 1
add 3 2 0 20
add 4 3 0 1
next 1
next 1
""",

    # The same rule reached by the scan rather than by the ledger.
    "empty-scan": """
cfg 100
row 1 1 0 20
row 2 2 0 1
open 1 0 5 6
next 1
next 1
""",

    # The other side of it: a page that has already handed something out does not take a
    # row it has no weight for, it steps over it.
    "empty-not": """
cfg 100
row 1 1 0 2
row 2 2 0 20
row 3 3 0 1
open 1 0 5 6
next 1
next 1
""",

    # -- stepping over ---------------------------------------------------------------------

    # A row too heavy for what is left does not end the page; the scan goes past it and
    # hands out the lighter row behind it.
    "step-over": """
cfg 100
row 1 1 0 2
row 2 2 0 5
row 3 3 0 2
open 1 0 5 6
next 1
""",

    # And the row it stepped over is what the next page starts from.
    "step-owed": """
cfg 100
row 1 1 0 2
row 2 2 0 5
row 3 3 0 2
open 1 0 5 6
next 1
next 1
""",

    # -- the scan and its stops --------------------------------------------------------------

    # A row this scroll already has is passed by and the mark still goes past it, so the
    # row moved behind the scan is not handed out twice.
    "scan-skip": """
cfg 100
row 1 1 0 1
row 2 2 0 1
row 3 5 0 1
open 1 0 2 10
next 1
move 1 4
next 1
""",

    # The page fills at n rows and the mark stops short of the row it never looked at,
    # which is why that row is unhanded rather than owed.
    "scan-full": """
cfg 100
row 1 1 0 1
row 2 2 0 1
row 3 3 0 1
open 1 0 2 10
next 1
""",

    # A row whose weight is exactly what is left fits, and the page ends with nothing left.
    "scan-weight": """
cfg 100
row 1 1 0 4
row 2 2 0 2
row 3 3 0 1
open 1 0 9 6
next 1
next 1
""",

    # Two step-overs weigh as much as a page carries, so the scan stops with room and
    # weight still in hand and never looks at the light row behind them.
    "scan-over": """
cfg 100
row 1 1 0 6
row 2 2 0 5
row 3 3 0 5
row 4 4 0 1
open 1 0 9 8
next 1
""",

    # The allowance boundary: one step-over weighing exactly what a page carries is enough
    # to stop the scan, so the light row behind it is never looked at.
    "over-exact": """
cfg 200
row 1 1 0 3
row 2 2 0 8
row 3 3 0 1
open 1 0 9 8
next 1
""",

    # -- the mark ------------------------------------------------------------------------------

    # The mark is the last row the scan looked at, not the last it handed out: the row
    # added between the two is owed under the first reading and not under the second.
    "mark-look": """
cfg 100
row 1 1 0 6
row 2 3 0 5
row 3 5 0 5
row 4 7 0 1
open 1 0 9 8
next 1
add 5 4 0 1
next 1
""",

    # -- the hold ---------------------------------------------------------------------------------

    # One scroll owes nine of a hold of ten, so the other scroll's scan has no room to step
    # over and stops with its mark short of the row that stopped it.
    "hold-block": """
cfg 10
row 1 1 0 2
row 2 2 0 9
row 3 3 0 1
row 4 1 1 2
row 5 2 1 9
row 6 3 1 1
open 1 0 5 5
open 2 1 5 5
next 1
next 2
""",

    # And once the first scroll has been handed what it was owed, the second scroll's next
    # scan finds room for the same step-over.
    "hold-free": """
cfg 10
row 1 1 0 2
row 2 2 0 9
row 3 3 0 1
row 4 1 1 2
row 6 2 1 1
row 7 3 1 1
row 8 4 1 1
row 5 5 1 9
open 1 0 3 5
open 2 1 3 5
next 1
next 2
next 1
next 2
""",

    # The boundary itself: the weight already owed plus this row's weight comes to exactly
    # the hold, and that is room enough to step over it.
    "hold-exact": """
cfg 10
row 1 1 0 2
row 2 2 0 5
row 3 3 0 1
row 4 1 1 2
row 5 2 1 5
row 6 3 1 1
open 1 0 5 4
open 2 1 5 4
next 1
next 2
""",

    # The hold governs a scan, never an edit: this row weighs more than the whole hold and
    # comes to be owed anyway.
    "hold-edit": """
cfg 5
row 1 1 0 2
row 2 2 0 1
row 3 9 0 1
open 1 0 3 4
next 1
add 4 3 0 9
next 1
""",

    # -- owed membership -----------------------------------------------------------------------------

    # A move that carries an owed row past the mark retires its ledger entry.
    "owe-retire": """
cfg 100
row 1 1 0 2
row 2 2 0 9
row 3 3 0 1
open 1 0 5 4
next 1
move 2 9
next 1
""",

    # Carried back afterwards it is owed again, and it goes in behind the row that came to
    # be owed while it was away.
    "owe-return": """
cfg 100
row 1 1 0 2
row 2 2 0 9
row 5 9 0 1
open 1 0 5 4
next 1
move 2 8
add 6 1 0 3
move 2 2
next 1
next 1
""",

    # A row added at a place the scroll has already gone past is owed.
    "owe-add": """
cfg 100
row 1 1 0 1
row 2 2 0 1
open 1 0 5 10
next 1
add 3 1 0 1
next 1
""",

    # A row added ahead of the mark is not: the scan will reach it in its own time, and the
    # ledger order shows which of the two it was.
    "owe-after": """
cfg 100
row 1 1 0 1
row 2 5 0 1
row 3 9 0 5
open 1 0 5 4
next 1
add 4 10 0 1
add 5 2 0 1
next 1
""",

    # Dropping an owed row takes it out of the ledger and out of the weight held.
    "owe-drop": """
cfg 100
row 1 1 0 1
row 2 2 0 9
row 3 3 0 1
open 1 0 5 4
next 1
drop 2
next 1
""",

    # A row this scroll already has is not owed however far back it moves.
    "owe-taken": """
cfg 100
row 1 1 0 1
row 2 2 0 1
row 3 9 0 1
open 1 0 5 10
next 1
move 1 8
next 1
""",

    # -- tags and the delivery memory -------------------------------------------------------------------

    # Retagged away, an owed row is no longer in the view and no longer owed.
    "tag-leave": """
cfg 100
row 1 1 0 1
row 2 2 0 9
row 3 3 0 1
open 1 0 5 4
next 1
tag 2 1
next 1
""",

    # Retagged in behind the mark, a row comes to be owed to the scroll reading that tag.
    "tag-join": """
cfg 100
row 1 1 0 1
row 2 2 0 1
row 3 1 1 1
open 1 0 5 10
next 1
tag 3 0
next 1
""",

    # The memory belongs to the scroll, not to the row: leaving the view and coming back
    # does not make a handed row handable again.
    "tag-back": """
cfg 100
row 1 1 0 1
row 2 2 0 1
open 1 0 5 10
next 1
tag 1 1
tag 1 0
next 1
""",

    # And it belongs to one scroll: two scrolls on one tag are handed the same rows.
    "seen-scroll": """
cfg 100
row 1 1 0 1
row 2 2 0 1
open 1 0 5 10
open 2 0 5 10
next 1
next 2
""",

    # -- the closing report -------------------------------------------------------------------------------

    # Unhanded is not the same as owed: rows 3 and 4 are neither.
    "rep-u": """
cfg 100
row 1 1 0 1
row 2 2 0 9
row 3 3 0 1
row 4 4 0 1
open 1 0 5 4
next 1
""",

    # Handed out is remembered after the row is gone.
    "rep-d": """
cfg 100
row 1 1 0 1
row 2 2 0 1
open 1 0 5 10
next 1
drop 1
""",

    # The total is the weight owed across every scroll, not one of them.
    "rep-tot": """
cfg 100
row 1 1 0 1
row 2 2 0 9
row 3 1 1 1
row 4 2 1 7
open 1 0 5 4
open 2 1 5 4
next 1
next 2
""",

    # -- the ordinary case ----------------------------------------------------------------------------------

    # Nothing is ever too heavy and nothing is edited: every page is a plain run of the
    # view and the last one is empty. A service that owes rows whenever a page fills, or
    # that leaves its mark behind the last row handed out, fails here.
    "plain-run": """
cfg 100
row 1 1 0 2
row 2 2 0 2
row 3 3 0 2
row 4 4 0 2
row 5 5 0 2
row 6 6 0 2
open 1 0 2 20
next 1
next 1
next 1
next 1
""",
}

ORDER = tuple(sorted(CASES))


def prog(name):
    return CASES[name].strip().splitlines()
