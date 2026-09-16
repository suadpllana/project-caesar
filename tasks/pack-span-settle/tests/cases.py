"""The enumerated shards: one per graded decision, plus the must-still-work side of each fence.

Each shard is small enough to settle by hand, and each is named for the rule it pins, so a
failure names the rule rather than a line number. Their traces are frozen in `seal/gt.json`,
which was built before the grading file was written; the grader checks the sealed model still
reproduces that file exactly before it grades anything.
"""

SHARDS = {
    # --- the ordinary side of every fence -------------------------------------------
    # Records that fit in the room left share a window; nothing is closed short, and a
    # record cut into one piece has its length less one scored positions.
    "plain-fit": [
        "width 12", "span 2", "floor 1",
        "rec a 5 2", "rec b 4 3", "rec c 3 1", "seal",
    ],
    # A record exactly filling the room leaves no slot behind and needs no short close.
    "exact-fill": [
        "width 10", "span 1", "floor 1",
        "rec a 4 1", "rec b 6 2", "rec c 10 3", "seal",
    ],
    # Two records meeting inside a window: the position where one ends and the next begins
    # is not scored, because its next position belongs to another record.
    "cross-count": [
        "width 9", "span 1", "floor 1",
        "rec a 3 1", "rec b 3 1", "rec c 3 1", "seal",
    ],

    # --- the cut ---------------------------------------------------------------------
    # A record that is not finished fills the window to the brim: the piece is the whole of
    # the room whenever what is left over is two tokens or more.
    "fill-brim": [
        "width 7", "span 2", "floor 1",
        "rec a 16 3", "seal",
    ],
    # A record carried into a second window loses a scored position to the cut.
    "carry-two": [
        "width 8", "span 2", "floor 1",
        "rec a 5 2", "rec b 6 3", "seal",
    ],
    # Taking the whole of the room would strand a single token, so the piece steps back one
    # and the window is closed with one slot unused.
    "stranded-tail": [
        "width 10", "span 1", "floor 1",
        "rec a 11 1", "seal",
    ],
    # One slot left and a record still to lay: no piece of two tokens fits, so the window is
    # closed with that slot unused.
    "room-one": [
        "width 7", "span 1", "floor 1",
        "rec a 6 1", "rec b 4 1", "seal",
    ],
    # Two slots left against three tokens: a piece of two would strand one and a piece of one
    # is not allowed, so the window is closed with both slots unused.
    "room-two": [
        "width 8", "span 1", "floor 1",
        "rec a 6 1", "rec b 3 1", "seal",
    ],
    # A record whose first piece lands in the window after a short close reports that window.
    "first-window": [
        "width 6", "span 3", "floor 1",
        "rec a 5 1", "rec b 4 2", "seal",
    ],

    # --- what is laid at all ---------------------------------------------------------
    # A one token record carries no scored position: it is passed over and takes no room, so
    # the record after it starts exactly where it would have.
    "one-token": [
        "width 9", "span 1", "floor 1",
        "rec a 4 1", "rec b 1 5", "rec c 4 2", "seal",
    ],
    # Two tokens is the floor, not three: a two token record is laid and scores one position.
    "two-token": [
        "width 9", "span 1", "floor 1",
        "rec a 4 1", "rec b 2 6", "rec c 3 2", "seal",
    ],
    # A skipped record leaves the layout exactly as it was, including a later short close.
    "skip-shifts": [
        "width 7", "span 2", "floor 1",
        "rec a 6 1", "rec b 1 9", "rec c 4 1", "seal",
    ],

    # --- the floor -------------------------------------------------------------------
    # A step carrying exactly the floor is kept.
    "floor-edge": [
        "width 6", "span 1", "floor 5",
        "rec a 6 2", "seal",
    ],
    # A step one position short of the floor is dropped, and prints at its close.
    "floor-under": [
        "width 6", "span 1", "floor 6",
        "rec a 6 2", "seal",
    ],
    # Every step a record touches is dropped, so it has no scored position to carry weight.
    "drop-void": [
        "width 6", "span 1", "floor 9",
        "rec a 4 3", "rec b 4 5", "seal",
    ],
    # One step kept and one dropped: only the kept one counts toward the divisor, so the
    # record's scored positions and its divisor are different numbers.
    "drop-part": [
        "width 8", "span 1", "floor 5",
        "rec a 11 3", "seal",
    ],
    # A dropped step prints when it closes, which is before the kept steps waiting behind it
    # on the same record settle.
    "drop-order": [
        "width 6", "span 1", "floor 4",
        "rec a 20 3", "seal",
    ],

    # --- settlement ------------------------------------------------------------------
    # A step closed while a record is still being laid waits for that record.
    "band-waits": [
        "width 6", "span 1", "floor 1",
        "rec a 14 5", "seal",
    ],
    # One record ending settles several steps at once, printed in index order after it.
    "settle-order": [
        "width 6", "span 1", "floor 1",
        "rec a 4 1", "rec b 20 7", "seal",
    ],
    # A record spanning several steps carries its weight into each of them.
    "many-bands": [
        "width 5", "span 2", "floor 1",
        "rec a 30 6", "rec b 4 1", "seal",
    ],
    # A step whose records all ended inside it settles at its own close.
    "band-closes": [
        "width 6", "span 2", "floor 1",
        "rec a 5 1", "rec b 6 2", "rec c 5 3", "seal",
    ],

    # --- the settings ----------------------------------------------------------------
    # A width op sets the width of windows opened after it; the open window keeps its own.
    "width-next": [
        "width 10", "span 2", "floor 1",
        "rec a 4 1", "width 5", "rec b 9 2", "seal",
    ],
    # A span op sets how many windows the steps opened after it hold; the open step keeps
    # the span it was opened with, and the steps after it take the new one.
    "span-next": [
        "width 6", "span 3", "floor 1",
        "rec a 8 1", "span 1", "rec b 20 2", "seal",
    ],
    # A floor op sets the floor of the steps opened after it; the open step keeps the floor
    # it was opened with, so a step still open when the op arrives is decided by the old one.
    "floor-next": [
        "width 6", "span 1", "floor 1",
        "rec a 4 1", "floor 20", "rec b 6 2", "seal",
    ],

    # --- sealing ---------------------------------------------------------------------
    # Seal closes a window with room still in it and the step holding it.
    "seal-short": [
        "width 12", "span 4", "floor 1",
        "rec a 5 1", "seal",
    ],
    # Seal with nothing open settles nothing and prints nothing more.
    "seal-empty": [
        "width 4", "span 1", "floor 1",
        "rec a 4 1", "seal",
    ],

    # --- the fractions ---------------------------------------------------------------
    # A weight and a divisor sharing a factor are printed in lowest terms.
    "frac-reduce": [
        "width 10", "span 1", "floor 1",
        "rec a 7 12", "seal",
    ],
    # A step summing weights over different denominators.
    "frac-sum": [
        "width 16", "span 1", "floor 1",
        "rec a 4 1", "rec b 6 1", "rec c 8 1", "seal",
    ],
    # A weight of one spread over many positions stays a fraction.
    "weight-one": [
        "width 40", "span 1", "floor 1",
        "rec a 33 1", "seal",
    ],
}

ORDER = sorted(SHARDS)


def ops(name):
    return list(SHARDS[name])
