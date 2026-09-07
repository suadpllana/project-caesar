"""Enumerated sheets, one per stated rule, small enough to check by hand.

Each entry is a whole script: a sheet size, a load section, `go`, and the edits that are
graded. The name says which rule the edits are aimed at. The expected reports live in
gt.json and were derived by hand from the rules; the sealed model has to reproduce every
one of them before a run can be graded, so neither can drift alone.
"""

CASES = {

    # ---- value reads, and the cutoff on them --------------------------------

    "value-moves-reader-follows": """
size 8
set r1c1 3
set r2c1 4
set r1c3 = SUM(r1c1:r2c1)
go
set r1c1 5
""",

    "value-restated-nothing-moves": """
size 8
set r1c1 3
set r2c1 4
set r1c3 = SUM(r1c1:r2c1)
go
set r1c1 3
""",

    "recompute-that-lands-where-it-was": """
size 8
set r1c1 4
set r2c1 2
set r1c3 = CNT(r1c1:r2c1)
set r1c4 = r1c3 + 1
go
set r1c1 7
clr r2c1
""",

    "empty-member-of-a-span": """
size 8
set r1c1 3
set r1c3 = SUM(r1c1:r3c1)
go
set r3c1 7
clr r3c1
""",

    "count-ignores-the-empties": """
size 8
set r1c1 3
set r3c1 5
set r1c3 = CNT(r1c1:r4c1)
go
set r2c1 0
clr r1c1
""",

    # ---- reads that depend on the values read -------------------------------

    "branch-not-taken-is-not-read": """
size 8
set r1c1 0
set r2c1 5
set r3c1 9
set r1c3 = IFZ(r1c1, r2c1, r3c1)
go
set r3c1 1
set r2c1 6
""",

    "branch-flips-and-the-reads-move": """
size 8
set r1c1 0
set r2c1 5
set r3c1 9
set r1c3 = IFZ(r1c1, r2c1, r3c1)
go
set r1c1 1
set r2c1 6
set r3c1 4
""",

    # ---- laying a block down ------------------------------------------------

    "a-block-occupies-what-is-under-it": """
size 8
set r1c1 3
set r1c2 = RUN(1, r1c1)
set r5c4 = r3c2 + 0
go
set r1c1 4
""",

    "an-empty-block-shows-nothing": """
size 8
set r1c1 3
set r1c2 = RUN(3, r1c1)
set r5c4 = r2c2 + 0
go
set r1c1 2
set r1c1 1
""",

    "a-block-that-runs-off-the-sheet": """
size 6
set r1c1 3
set r4c2 = RUN(1, r1c1)
go
set r1c1 4
set r1c1 2
""",

    "a-block-may-not-cover-its-own-input": """
size 8
set r5c2 7
set r6c2 5
set r1c2 = TOP(r5c2:r6c2, 2)
set r7c4 = r2c2 + 0
go
set r1c2 = TOP(r2c2:r6c2, 3)
""",

    # ---- occupancy: who is in the way --------------------------------------

    "content-planted-in-the-way": """
size 8
set r1c1 4
set r1c2 = RUN(1, r1c1)
set r6c4 = r2c2 + 0
go
set r3c2 9
""",

    "the-blocker-goes-away-again": """
size 8
set r1c1 4
set r1c2 = RUN(1, r1c1)
set r3c2 9
set r6c4 = r2c2 + 0
go
clr r3c2
""",

    "a-blocker-holding-the-very-same-value": """
size 8
set r1c1 4
set r1c2 = RUN(1, r1c1)
set r6c4 = r3c2 + 0
set r7c4 = r2c2 + 0
go
set r3c2 3
""",

    "the-value-dips-and-comes-back": """
size 8
set r1c1 4
set r1c2 = RUN(1, r1c1)
set r3c2 3
set r6c4 = r3c2 + 0
go
clr r3c2
""",

    "a-reader-that-sits-above-the-block": """
size 9
set r1c1 4
set r1c4 = r6c2 + 0
set r4c2 = RUN(1, r1c1)
set r6c2 3
go
clr r6c2
""",

    "the-lower-formula-is-in-the-way": """
size 9
set r1c1 6
set r1c2 = RUN(1, r1c1)
set r4c2 = SUM(r1c1:r1c1)
set r8c4 = r2c2 + 0
go
clr r4c2
set r4c2 = SUM(r1c1:r1c1)
""",

    "two-things-in-the-way": """
size 9
set r1c1 6
set r1c2 = RUN(1, r1c1)
set r3c2 8
set r5c2 9
set r8c4 = r2c2 + 0
go
clr r5c2
clr r3c2
""",

    "a-blocker-outside-the-block": """
size 8
set r1c1 2
set r1c2 = RUN(1, r1c1)
go
set r5c2 7
clr r5c2
""",

    # ---- giving cells up ----------------------------------------------------

    "a-shorter-block-lets-go": """
size 8
set r1c1 4
set r1c2 = RUN(1, r1c1)
set r6c4 = r4c2 + 0
set r7c4 = r2c2 + 0
go
set r1c1 2
""",

    "the-formula-stops-being-a-block": """
size 8
set r1c1 4
set r1c2 = RUN(1, r1c1)
set r6c4 = r3c2 + 0
go
set r1c2 = SUM(r1c1:r1c1)
""",

    "the-formula-is-cleared-away": """
size 8
set r1c1 4
set r1c2 = RUN(1, r1c1)
set r6c4 = r3c2 + 0
go
clr r1c2
""",

    "a-literal-lands-on-the-formula": """
size 8
set r1c1 4
set r1c2 = RUN(1, r1c1)
set r6c4 = r3c2 + 0
go
set r1c2 8
""",

    "a-cell-it-let-go-of-was-taken": """
size 8
set r1c1 4
set r1c2 = RUN(1, r1c1)
go
set r4c2 9
set r1c1 2
""",

    # ---- the edit itself ----------------------------------------------------

    "the-same-formula-written-again": """
size 8
set r1c1 3
set r2c1 4
set r1c3 = SUM(r1c1:r2c1)
set r2c3 = r1c3 + 1
go
set r1c3 = SUM(r1c1:r2c1)
""",

    "a-different-formula-over-the-same-cells": """
size 8
set r1c1 3
set r2c1 4
set r1c3 = SUM(r1c1:r2c1)
set r2c3 = r1c3 + 1
go
set r1c3 = CNT(r1c1:r2c1)
""",

    "clearing-a-cell-a-block-covers": """
size 8
set r1c1 4
set r1c2 = RUN(1, r1c1)
go
clr r3c2
clr r7c2
""",

    # ---- errors -------------------------------------------------------------

    "the-error-travels": """
size 6
set r1c1 4
set r4c2 = RUN(1, r1c1)
set r6c4 = r4c2 + 1
set r6c3 = CNT(r4c2:r4c2)
go
set r1c1 1
""",

    # ---- who is affected by which element -----------------------------------

    "the-head-holds-still-while-the-tail-moves": """
size 9
set r1c1 4
set r2c1 5
set r3c1 6
set r1c2 = TOP(r1c1:r3c1, 3)
set r7c4 = r1c2 + 0
set r8c4 = r3c2 + 0
go
set r1c1 1
""",

    "the-head-moves-while-the-tail-holds-still": """
size 9
set r1c1 4
set r2c1 5
set r3c1 6
set r1c2 = TOP(r1c1:r3c1, 3)
set r7c4 = r1c2 + 0
set r8c4 = r3c2 + 0
go
set r2c1 9
""",

    # ---- chains and joins ---------------------------------------------------

    "a-chain-stops-where-nothing-moved": """
size 8
set r1c1 2
set r2c1 3
set r1c3 = CNT(r1c1:r2c1)
set r2c3 = r1c3 * 2
set r3c3 = r2c3 + 1
go
set r1c1 5
clr r2c1
""",

    "two-ways-round-to-the-same-cell": """
size 8
set r1c1 2
set r1c3 = r1c1 + 1
set r2c3 = r1c1 * 2
set r3c3 = r1c3 + r2c3
go
set r1c1 5
""",
}
