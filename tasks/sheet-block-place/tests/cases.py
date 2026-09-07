"""Enumerated scripts, one per stated rule.

Each name says which decision the script pins down. The grader checks these against
gt.json, and the sealed model has to reproduce every one of them before a run can pass,
so a drift in either the model or the rules shows up here rather than in a generated
family where it would be one failure among hundreds.
"""

CASES = {

    # ---- what a block occupies, and what refuses it -----------------------------
    "owner-shows-its-first-value": """
put a1 RUN(3)
""",
    "block-refused-by-content": """
put a3 5
put a1 RUN(3)
""",
    "refused-owner-covers-nothing": """
put a3 5
put a1 RUN(3)
put b5 SUM(a1:a4)
put b6 CNT(a1:a4)
""",
    "overlap-earliest-wins": """
put b1 RUN(3)
put a2 ROW(5,3)
""",
    "later-block-fills-a-refused-gap": """
put c2 7
put b1 RUN(4)
put b3 REP(8,2)
""",
    "block-past-the-last-row": """
put a18 RUN(4)
put a17 RUN(4)
""",
    "block-past-the-last-column": """
put i1 ROW(3,3)
put h1 ROW(3,3)
""",
    "owner-cell-is-not-in-the-way": """
put a1 RUN(1)
put b1 RUN(2)
""",
    "clearing-frees-a-block": """
put a3 5
put a1 RUN(3)
clr a3
""",
    "content-put-under-a-block": """
put a1 RUN(4)
put a3 9
clr a3
""",
    "cover-reaches-through-a-range": """
put a1 REP(4,3)
put b5 SUM(a1:a3)
put b6 MAX(a1:a3)
""",
    "two-columns-of-blocks": """
put a1 RUN(5)
put b1 RUN(5)
put c1 SUM(a1:b5)
""",

    # ---- the loop rule -----------------------------------------------------------
    "read-into-own-quadrant": """
put b3 2
put b1 RUN(b3)
""",
    "read-same-row-to-the-right": """
put b1 3
put a1 SUM(b1:b3)
""",
    "read-up-and-right-is-fine": """
put b1 3
put c1 4
put a5 SUM(b1:c2)
""",
    "read-down-and-left-is-fine": """
put a2 3
put b3 4
put c1 SUM(a2:b3)
""",
    "loop-marks-the-whole-chain": """
put a4 2
put c2 RUN(d5)
put d5 SUM(c2:c3)
""",
    "loop-does-not-stop-at-a-sum": """
put b3 2
put b2 RUN(c4)
put a9 SUM(b2:b4)
put a10 CNT(b2:b4)
""",
    "owner-order-decides-a-loop": """
put c4 RUN(b8)
put b2 ROW(d6,3)
put b8 5
put d6 7
""",
    "loop-swallows-what-it-passed-through": """
put b1 MAX(a6:a9)
put a5 SUM(c4:c4)
""",
    "loop-in-a-count-argument": """
put b2 RUN(c4)
put a12 LEN(b2:b3)
""",

    # ---- reading a cell ----------------------------------------------------------
    "empty-is-zero-in-arithmetic": """
put b1 a1 + 5
""",
    "count-ignores-empty": """
put a1 3
put b5 CNT(a1:a4)
put b6 LEN(a1:a4)
""",
    "sum-steps-over-a-refusal": """
put a3 5
put a1 RUN(3)
put b7 SUM(a1:a3)
""",
    "count-includes-a-refusal": """
put a3 5
put a1 RUN(3)
put b7 CNT(a1:a3)
""",
    "max-with-nothing-numeric": """
put a3 5
put a1 RUN(3)
put b7 MAX(a1:a2)
put b8 MAX(a2:a2)
""",
    "left-error-wins": """
put a1 RUN(0)
put b3 7
put b1 RUN(4)
put c1 a1 + b1
put c2 b1 + a1
""",
    "block-in-arithmetic": """
put a5 RUN(2) + 1
put a6 GROW(a1:a2) * 2
""",
    "range-in-arithmetic": """
put c5 a1:b2 + 1
""",
    "a-range-cell-shows-a-refusal": """
put c5 a1:b2
""",

    # ---- picking, keeping, growing ------------------------------------------------
    "at-on-an-empty-cell": """
put a1 5
put a3 7
put c1 AT(a1:a3,2)
put c2 AT(a1:a3,3)
""",
    "at-past-the-end": """
put a1 5
put c1 AT(a1:a2,5)
put c2 AT(a1:a2,0)
""",
    "grow-keeps-a-hole": """
put a1 5
put a3 7
put c1 GROW(a1:a3)
""",
    "grow-keeps-a-refusal": """
put a3 5
put a1 RUN(3)
put c1 GROW(a1:a3)
""",
    "grow-keeps-the-shape": """
put a1 1
put b1 2
put a2 3
put d5 GROW(a1:b2)
""",
    "keep-takes-the-first-cells": """
put a1 1
put b1 2
put a2 3
put b2 4
put d5 KEEP(a1:b2,3)
""",
    "keep-past-the-end": """
put a1 1
put d5 KEEP(a1:a2,5)
""",
    "rep-of-an-error-is-a-block-of-errors": """
put a1 RUN(0)
put c1 REP(a1,3)
put e5 CNT(c1:c3)
put e6 SUM(c1:c3)
""",
    "row-runs-across": """
put a1 ROW(6,4)
put e5 SUM(a1:d1)
""",
    "row-width-limit": """
put c1 ROW(1,9)
put c2 ROW(1,11)
""",
    "count-must-be-at-least-one": """
put a1 RUN(0)
put a2 REP(3,0)
""",
    "count-past-the-sheet": """
put a1 RUN(21)
put a2 RUN(20)
""",
    "count-comes-from-a-cell": """
put a1 3
put b1 RUN(a1)
put a1 5
put a1 1
""",
    "count-from-a-refused-cell": """
put a3 5
put a1 RUN(3)
put c1 RUN(a1)
""",
    "len-counts-cells-not-values": """
put a1 5
put d5 LEN(a1:b3)
put d6 LEN(a1)
put d7 LEN(RUN(4))
""",
}

for _k in list(CASES):
    CASES[_k] = CASES[_k].strip("\n")
