"""The enumerated pipelines: one per graded decision, and both sides of every fence.

Each is small enough to settle by hand, and each is named for the rule it pins, so a failure
says which rule broke instead of "some generated pipeline differed". Their plans were frozen
into seal/gt.json from the sealed model after being derived by hand
(authoring/restate-hold-plan/hand.py holds the hand derivations and checks them).
"""

CASES = {
    # --- the ordinary side: nothing reached has expired, nothing is published --------------
    "plain-rerun": """
now 96
src raw h 200
step cl h 200 raw
step tot d 200 cl/d
step wk d 200 tot~2
fix raw 30
""",
    # --- existence: the keep boundary, and publication outliving the keep -------------------
    "keep-edge": """
now 100
src raw h 500
step cl h 10 raw
step sm h 500 cl~3
fix raw 90
""",
    "keep-published": """
now 240
src raw d 1000
step dy d 48 raw
step wk d 1000 dy~4
pin dy 5
fix raw 8
""",
    "reach-bounded-by-now": """
now 100
src raw h 1000
step dy d 1000 raw/d
step hr h 1000 raw~5
fix raw 97
""",
    # --- what the correction reaches, through partitions that no longer exist ---------------
    "reach-through-expired": """
now 240
src raw h 1000
step cl h 24 raw
step tot d 1000 cl/d
step wk d 1000 tot~2
fix raw 100
""",
    # --- published partitions -----------------------------------------------------------
    "pinned-hold": """
now 240
src raw d 1000
step dy d 1000 raw
step wk d 1000 dy
pin dy 6
fix raw 6
""",
    "pinned-part": """
now 240
src raw d 1000
step dy d 1000 raw
step ev d 1000 raw
step wk d 1000 dy ev
pin dy 6
fix raw 6
""",
    "pinned-window-same": """
now 240
src raw d 1000
step dy d 1000 raw
step wk d 1000 dy~3
pin dy 5
fix raw 5
""",
    "pinned-unreached": """
now 240
src raw d 1000
step dy d 1000 raw
step wk d 1000 dy~2
pin dy 3
fix raw 8
""",
    "same-disagrees": """
now 240
src raw d 1000
step dy d 1000 raw
step mid d 1000 dy
step ev d 1000 raw
step wk d 1000 mid ev
pin dy 6
fix raw 6
""",
    # --- partitions computed for the plan ----------------------------------------------------
    "temp-window": """
now 240
src raw d 1000
step dy d 72 raw
step wk d 1000 dy~3
fix raw 8
""",
    "temp-once": """
now 240
src raw d 1000
step dy d 72 raw
step wk d 1000 dy~3
step mo d 1000 dy~4
fix raw 8
""",
    "temp-only-for-reruns": """
now 240
src raw d 1000
src oth d 1000
step dy d 1000 raw
step ex d 72 oth
step wk d 1000 dy ex~3
pin dy 8
fix raw 8
""",
    "lost-temps-unprinted": """
now 240
src raw d 96
src oth d 1000
step dy d 48 oth
step wk d 1000 dy~3 raw~4
fix oth 8
""",
    # --- partitions that cannot be computed --------------------------------------------------
    "lost-source": """
now 240
src raw d 72
step dy d 1000 raw
step wk d 1000 dy~3
step mo d 1000 raw~3
fix raw 8
""",
    "lost-temp-chain": """
now 240
src raw d 96
step dy d 48 raw
step wk d 1000 dy~4
fix raw 8
""",
    "lost-before-same": """
now 240
src raw d 1000
src oth d 72
step dy d 1000 raw
step wk d 1000 dy oth~3
pin dy 8
fix raw 8
""",
    # --- roll-ups standing in for a day of hours -------------------------------------------
    "stand-use": """
now 240
src raw h 1000
step x h 24 raw
step r d 1000 x/d
step s d 1000 x/d
stand r x
fix raw 100
""",
    "stand-any-hour": """
now 240
src raw h 1000
step x h 20 raw
step r d 1000 x/d
step s d 1000 x/d
stand r x
fix raw 225
""",
    "stand-refused-published": """
now 240
src raw h 1000
step x h 24 raw
step r d 1000 x/d
step s d 1000 x/d
step t d 1000 r
stand r x
pin r 4
fix raw 100
""",
    "stand-refused-part": """
now 240
src raw h 1000
step x h 20 raw~2
step s d 1000 x/d
step r d 1000 x/d
stand r x
pin x 225
fix raw 224
""",
    "stand-in-temp": """
now 240
src raw h 1000
step x h 24 raw
step r d 1000 x/d
step s d 48 x/d
step w d 1000 s~3
stand r x
fix raw 190
""",
    "mode-part-over-sub": """
now 240
src raw h 1000
step x h 24 raw
step r d 1000 x/d
step p d 1000 raw/d
step s d 1000 x/d p
stand r x
pin p 4
fix raw 100
""",
    # --- the order of the plan -----------------------------------------------------------
    "order-after-roll-up": """
now 240
src raw h 1000
step x h 24 raw
step s d 1000 x/d
step u d 1000 raw/d
step r d 1000 x/d
stand r x
fix raw 100
""",
    "holds-last": """
now 240
src raw d 1000
step dy d 1000 raw
step wk d 1000 raw~3 dy
pin dy 6
fix raw 6
""",
    # --- steps that read their own previous partition --------------------------------------
    "chain-published": """
now 240
src raw d 1000
step bal d 1000 raw bal-1
pin bal 6
fix raw 4
""",
    "chain-checkpoint": """
now 240
src raw d 1000
step bal d 72 raw bal-1
pin bal 2
fix raw 5
""",
    "chain-to-zero": """
now 168
src raw d 1000
step bal d 48 raw bal-1
fix raw 3
""",
    # --- reads that fall before hour 0, and previous periods between grains -----------------
    "prehistory": """
now 120
src raw d 1000
step dy d 1000 raw
step wk d 1000 dy~7
fix raw 1
""",
    "prev-cross": """
now 120
src raw h 1000
step dy d 1000 raw/d
step hr h 1000 dy-1
step dl d 1000 raw-1
fix raw 47
""",
}

ORDER = list(CASES)


def prog(name):
    """The pipeline's lines, without the blank lines that frame it above."""
    return [line for line in CASES[name].strip().splitlines() if line.strip()]
