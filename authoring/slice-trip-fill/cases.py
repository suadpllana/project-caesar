"""The enumerated sessions.

One per rule, named for the reading it exists to fail, and including the
must-still-work side of every fence. Their expected results are in gt.json.
"""

SESS = {}


def _add(name, body):
    SESS[name] = body.strip("\n") + "\n"


# ---------------------------------------------------------------- disclosure

_add("show-interleaves", """
cap 5
mark 100
new 1 1 s 100 30 10 day -
new 2 2 s 100 25 - day -
new 3 3 b 100 60 - day -
""")

_add("show-alone-refills", """
cap 5
mark 100
new 1 1 s 100 30 10 day -
new 2 2 b 100 30 - day -
""")

_add("show-goes-to-the-back", """
cap 5
mark 100
new 1 1 s 100 20 10 day -
new 2 2 s 100 5 - day -
new 3 3 b 100 10 - day -
""")

_add("show-on-a-resting-remainder", """
cap 5
mark 100
new 1 1 b 100 12 - day -
new 2 2 s 100 30 7 day -
""")

_add("show-larger-than-the-order", """
cap 5
mark 100
new 1 1 s 100 8 20 day -
new 2 2 b 100 8 - day -
""")

# ---------------------------------------------------------------- same participant

_add("hand-pulled-at-the-front", """
cap 5
mark 100
new 1 1 s 100 10 - day -
new 2 2 s 100 10 - day -
new 3 1 b 100 15 - day -
""")

_add("hand-takes-the-hidden-part", """
cap 5
mark 100
new 1 1 s 100 40 5 day -
new 2 2 s 100 10 - day -
new 3 1 b 100 20 - day -
""")

_add("hand-pull-does-not-step", """
cap 3
mark 98
new 1 1 s 100 10 - day -
new 2 2 s 103 10 - day -
new 3 1 b - 20 - day -
""")

_add("other-hand-steps", """
cap 3
mark 98
new 1 9 s 100 10 - day -
new 2 2 s 103 10 - day -
new 3 1 b - 20 - day -
""")

# ---------------------------------------------------------------- the band

_add("band-steps-with-the-fills", """
cap 3
mark 98
new 1 5 s 100 10 - day -
new 2 6 s 103 10 - day -
new 3 7 s 106 10 - day -
new 4 8 b - 40 - day -
""")

_add("band-stops-the-walk", """
cap 3
mark 98
new 1 5 s 100 10 - day -
new 2 6 s 105 10 - day -
new 3 7 b 110 30 - day -
""")

_add("band-does-not-look-past", """
cap 3
mark 98
new 1 5 s 100 10 - day -
new 2 6 s 105 10 - day -
new 3 7 b 110 30 - day -
new 4 8 b 99 10 - day -
new 5 9 s 95 12 - day -
""")

_add("band-off-a-stale-mark", """
cap 5
mark 110
new 1 5 s 100 10 - day -
new 2 6 s 108 10 - day -
new 3 7 b - 15 - day -
""")

_add("limit-stops-the-walk", """
cap 40
mark 100
new 1 5 s 100 10 - day -
new 2 6 s 104 10 - day -
new 3 7 b 102 25 - day -
""")

# ---------------------------------------------------------------- all or nothing

_add("whole-leaves-nothing-behind", """
cap 3
mark 98
new 1 1 s 100 10 - day -
new 2 2 s 103 10 - day -
new 3 1 b - 15 - whole -
new 4 7 b - 15 - whole -
""")

_add("whole-fills-exactly", """
cap 5
mark 100
new 1 1 s 100 10 - day -
new 2 2 s 102 10 - day -
new 3 3 b 102 20 - whole -
""")

_add("whole-discounts-the-same-hand", """
cap 5
mark 100
new 1 1 s 100 10 - day -
new 2 2 s 100 10 - day -
new 3 1 b 100 15 - whole -
""")

_add("whole-discounts-past-the-band", """
cap 3
mark 98
new 1 5 s 100 10 - day -
new 2 6 s 108 10 - day -
new 3 7 b 110 15 - whole -
""")

_add("whole-counts-the-step", """
cap 3
mark 98
new 1 5 s 100 10 - day -
new 2 6 s 103 10 - day -
new 3 7 b 105 15 - whole -
""")

_add("whole-counts-the-hidden-part", """
cap 5
mark 100
new 1 1 s 100 30 5 day -
new 2 2 b 100 25 - whole -
""")

_add("whole-never-rests", """
cap 5
mark 100
new 1 1 s 100 10 - day -
new 2 2 b 100 25 - whole -
""")

_add("whole-market-order", """
cap 3
mark 98
new 1 5 s 100 10 - day -
new 2 6 s 103 10 - day -
new 3 7 b - 20 - whole -
""")

# ---------------------------------------------------------------- activation

_add("trip-lands-on-the-fill", """
cap 40
mark 100
new 1 5 s 100 10 - day -
new 2 6 s 104 10 - day -
new 3 7 b 103 5 - day 102
new 4 8 b 104 25 - day -
""")

_add("trip-cascades", """
cap 6
mark 100
new 1 5 s 100 10 - day -
new 2 6 s 104 10 - day -
new 3 7 s 108 10 - day -
new 4 1 b 110 30 - day 101
new 5 2 b 110 10 - day 105
new 6 9 b 104 15 - day -
""")

_add("trip-order-is-arrival", """
cap 40
mark 100
new 1 5 s 100 10 - day -
new 2 6 s 106 20 - day -
new 3 7 b 99 5 - day 103
new 4 8 b 98 5 - day 101
new 5 9 b 106 20 - day -
""")

_add("trip-waits-for-a-fill", """
cap 40
mark 100
new 1 5 s 100 10 - day -
new 2 6 b 90 10 - day 99
""")

_add("trip-pulled-before-it-fires", """
cap 40
mark 100
new 1 5 s 100 10 - day -
new 2 6 b 105 10 - day 99
pull 2
new 3 7 b 100 10 - day -
""")

_add("trip-sell-side", """
cap 40
mark 100
new 1 5 b 100 10 - day -
new 2 6 b 94 10 - day -
new 3 7 s 90 8 - day 101
new 4 8 s 94 20 - day -
""")

# ---------------------------------------------------------------- ordinary

_add("plain-cross", """
cap 40
mark 100
new 1 5 s 100 10 - day -
new 2 6 b 100 10 - day -
""")

_add("plain-rests-both-sides", """
cap 40
mark 100
new 1 5 s 102 10 - day -
new 2 6 b 98 10 - day -
new 3 7 s 103 5 - day -
new 4 8 b 98 7 - day -
""")

_add("part-cancels-the-remainder", """
cap 40
mark 100
new 1 5 s 100 10 - day -
new 2 6 b 100 25 - part -
""")

_add("market-cancels-the-remainder", """
cap 40
mark 100
new 1 5 s 100 10 - day -
new 2 6 b - 25 - day -
""")

_add("pull-an-unknown-id", """
cap 40
mark 100
new 1 5 s 100 10 - day -
pull 77
pull 1
new 2 6 b 100 10 - day -
""")

_add("pull-a-partly-filled-rest", """
cap 40
mark 100
new 1 5 s 100 30 8 day -
new 2 6 b 100 10 - day -
pull 1
new 3 7 b 100 10 - day -
""")
