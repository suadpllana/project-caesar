"""Enumerated event files, one per graded decision and one per side of each fence.

A generated population says a submission is wrong; these say which rule it got wrong. Every
wrong reading in the authoring set is failed by at least one program here, so a failure names
a rule instead of reading as bad luck on random input (tools/readingcheck.py measures that).

Heights are chosen so the arithmetic is short: most groups set the low and high bounds equal,
so a row's real height is that number and the only thing that moves is whether the row has
been measured yet.
"""

PROGRAMS = {

    # --- the band -------------------------------------------------------------------

    # The ordinary side: nothing is close enough to push the pinned header off, so the
    # band is the whole header height on every frame.
    "band-whole": [
        "cfg 60 0 3",
        "g 1 12 8 8 8 6",
        "g 2 12 8 8 8 6",
        "scroll 20",
        "scroll 12",
        "scroll -8",
    ],

    # The next header arrives inside the band and shortens it.
    "band-push": [
        "cfg 40 0 3",
        "g 1 20 5 5 5 1",
        "g 2 20 5 5 5 2",
        "scroll 10",
        "scroll 4",
        "scroll 1",
    ],

    # The offset lands exactly on a header top: that header has pinned, the one above
    # has not.
    "band-at-top": [
        "cfg 40 0 3",
        "g 1 10 10 10 10 2",
        "g 2 10 10 10 10 2",
        "g 3 10 10 10 10 2",
        "go 30",
        "go 29",
        "go 60",
    ],

    # The last group has no next header, so the push-off is measured against the end of
    # the document.
    "band-last": [
        "cfg 20 0 3",
        "g 1 30 5 5 5 1",
        "go 10",
        "go 14",
        "go 5",
    ],

    # --- the window -----------------------------------------------------------------

    # Every height is ten and the viewport is forty, so items sit exactly on both edges.
    "win-edges": [
        "cfg 40 0 3",
        "g 1 10 10 10 10 10",
        "go 0",
        "go 10",
        "go 20",
        "go 35",
    ],

    # Overscan belongs on both sides.
    "win-over-both": [
        "cfg 40 2 3",
        "g 1 10 10 10 10 12",
        "go 50",
        "go 60",
        "go 20",
    ],

    # Overscan clipped at the top of the flow and again at the end.
    "win-over-clip": [
        "cfg 40 3 3",
        "g 1 10 10 10 10 6",
        "go 0",
        "go 1000",
    ],

    # --- measuring ------------------------------------------------------------------

    # A row measured on one frame is not measured again on the next, so the per-frame
    # count falls to zero while the window stands still.
    "meas-once": [
        "cfg 40 0 3",
        "g 1 10 10 10 10 8",
        "scroll 0",
        "scroll 0",
        "scroll 10",
        "scroll -10",
    ],

    # The rows the overscan reaches are measured even though they are off screen.
    "meas-over": [
        "cfg 30 2 3",
        "g 1 10 10 10 10 10",
        "go 40",
    ],

    # --- the hold -------------------------------------------------------------------

    # The first visible item is behind the band; the item lying across the line is the
    # one the frame holds.
    "hold-under-band": [
        "cfg 60 0 3",
        "g 1 25 10 10 10 6",
        "go 30",
        "go 41",
        "go 55",
    ],

    # The gap is the held item's top less the line, so it is zero or negative.
    "hold-gap": [
        "cfg 50 0 3",
        "g 1 8 12 12 12 8",
        "go 17",
        "go 23",
        "go 29",
    ],

    # The line falls on the total: the last item is held.
    "hold-end": [
        "cfg 20 0 3",
        "g 1 30 5 5 5 1",
        "go 10",
        "go 12",
    ],

    # --- the hold across an edit ----------------------------------------------------

    # An insert above the hold moves it down the flow; the gap does not change, so the
    # offset follows it.
    "edit-ins-above": [
        "cfg 40 0 3",
        "g 1 10 10 10 10 8",
        "go 40",
        "ins 1 0 3",
        "ins 1 1 1",
    ],

    # An insert below the hold changes nothing about it.
    "edit-ins-below": [
        "cfg 40 0 3",
        "g 1 10 10 10 10 8",
        "go 30",
        "ins 1 7 2",
        "ins 1 9 1",
    ],

    # A delete above the hold leaves the hold itself alone.
    "edit-del-above": [
        "cfg 40 0 3",
        "g 1 10 10 10 10 10",
        "go 60",
        "del 1 0 2",
        "del 1 1 1",
    ],

    # The delete takes the held row and rows survive after it.
    "edit-del-held": [
        "cfg 40 0 3",
        "g 1 10 10 10 10 10",
        "g 2 10 10 10 10 4",
        "go 50",
        "del 1 3 3",
        "del 1 2 2",
    ],

    # The delete takes the held row and nothing survives after it, so the hold falls back
    # to the item before.
    "edit-del-tail": [
        "cfg 30 0 3",
        "g 1 10 10 10 10 3",
        "g 2 10 10 10 10 5",
        "go 70",
        "del 2 2 3",
        "del 2 1 1",
    ],

    # The gap moves by the difference of the two tops as they stood before the edit, not
    # after it.
    "edit-del-gap": [
        "cfg 40 0 3",
        "g 1 6 9 9 9 10",
        "go 48",
        "del 1 4 2",
        "del 1 3 1",
    ],

    # --- the foot -------------------------------------------------------------------

    # Resting at the foot, an insert keeps the pane at the foot rather than holding an
    # item.
    "foot-rest": [
        "cfg 40 0 3",
        "g 1 10 10 10 10 8",
        "go 900",
        "ins 1 0 2",
        "ins 1 8 2",
    ],

    # Leaving the foot by one pixel must not snap back.
    "foot-leave": [
        "cfg 40 0 3",
        "g 1 10 10 10 10 8",
        "go 900",
        "scroll -1",
        "scroll -1",
        "scroll 1",
    ],

    # At the foot with rows the pane has never measured: the frame's own measuring grows
    # the total, so the foot it settles at is not the foot it started from.
    "foot-grow": [
        "cfg 40 0 4",
        "g 1 10 4 40 40 12",
        "go 900",
        "scroll 0",
    ],

    # At the foot where a delete shrinks the document under it.
    "foot-shrink": [
        "cfg 40 0 3",
        "g 1 10 10 10 10 12",
        "go 900",
        "del 1 0 5",
        "del 1 0 4",
    ],

    # --- the settle loop ------------------------------------------------------------

    # The estimate is far under the truth, so the first pass's measuring moves the window
    # and a second pass is needed.
    "pass-two": [
        "cfg 60 0 4",
        "g 1 10 3 45 45 14",
        "go 40",
        "go 90",
    ],

    # The same shape under a cap of one: the frame stops unsettled.
    "pass-cap": [
        "cfg 60 0 1",
        "g 1 10 3 45 45 14",
        "go 40",
        "go 90",
    ],

    # The ordinary side: a frame over rows that are already measured settles in one pass
    # and leaves the offset exactly where the scroll put it.
    "pass-still": [
        "cfg 40 0 4",
        "g 1 10 10 10 10 10",
        "go 30",
        "scroll 10",
        "scroll 10",
        "scroll -20",
    ],

    # Both halves of the settle condition, on a document whose estimate is already the truth
    # so that measuring never moves anything by itself. The first frames measure without
    # moving the offset; the insert then moves the offset without measuring anything, because
    # the rows it puts in are far above the window.
    "pass-both-tests": [
        "cfg 40 0 4",
        "g 1 10 10 10 10 12",
        "go 0",
        "go 40",
        "go 80",
        "go 90",
        "ins 1 0 3",
    ],

    # Measuring inside the pinned group moves the next header, so the band the next pass
    # works from is not the band this one rendered.
    "pass-band-moves": [
        "cfg 40 0 4",
        "g 1 24 4 26 26 2",
        "g 2 24 4 26 26 2",
        "g 3 24 4 26 26 2",
        "go 20",
        "go 46",
    ],

    # The line reports the last pass's band and window, not the first pass's and not a
    # fresh pair worked out after the offset settled.
    "pass-report": [
        "cfg 50 1 4",
        "g 1 12 3 38 38 10",
        "go 60",
        "go 10",
    ],

    # --- clamping -------------------------------------------------------------------

    # Holding the item would put the offset past the foot.
    "clamp-foot": [
        "cfg 40 0 4",
        "g 1 10 30 6 6 10",
        "go 200",
        "scroll -5",
    ],

    # Holding the item would put the offset above the top of the document.
    "clamp-top": [
        "cfg 40 0 4",
        "g 1 10 30 6 6 10",
        "go 12",
        "go 4",
    ],

    # --- the viewport ---------------------------------------------------------------

    # A taller viewport moves the foot and widens the window.
    "size-grow": [
        "cfg 30 0 3",
        "g 1 10 10 10 10 8",
        "go 40",
        "size 90",
        "size 200",
    ],

    # A shorter viewport narrows the window and can leave the pane at the foot.
    "size-shrink": [
        "cfg 90 0 3",
        "g 1 10 10 10 10 8",
        "go 20",
        "size 30",
        "size 10",
    ],

    # --- ordinary running -----------------------------------------------------------

    # Nothing concentrated: a document read top to bottom and back.
    "plain-read": [
        "cfg 50 1 3",
        "g 1 9 11 11 11 7",
        "g 2 9 11 11 11 7",
        "g 3 9 11 11 11 7",
        "scroll 30",
        "scroll 30",
        "scroll 30",
        "scroll -45",
        "scroll -45",
    ],

    # A group with no rows at all, and one that loses every row it had.
    "empty-group": [
        "cfg 40 0 3",
        "g 1 10 10 10 10 0",
        "g 2 10 10 10 10 4",
        "g 3 10 10 10 10 0",
        "go 20",
        "del 2 0 4",
        "go 0",
        "ins 2 0 2",
    ],
}

ORDER = sorted(PROGRAMS)


def prog(name):
    return list(PROGRAMS[name])
