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

# IDs identify orders; they do not supply the arrival sequence. The resulting
# resting queue also exposes a wrong activation order after both orders fire.
_add("trip-arrival-with-unordered-ids", """
cap 10
mark 100
new 20 1 b 90 1 - day 100
new 10 2 b 90 1 - day 100
new 30 3 s 100 1 - day -
new 40 4 b 100 1 - day -
""")

# One fill both activates an order and exhausts a displayed slice. Notification
# precedes that slice's disclosure, while execution of the fired order is deferred.
_add("trip-before-disclosure", """
cap 10
mark 100
new 1 1 s 100 10 2 day -
new 2 2 b 99 1 - day 100
new 3 3 b 100 2 - part -
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

# Fill-boundary execution and the two admission fences.
_add("fill-capacity-is-consumed", """
pace fill
cap 5
mark 100
new 1 1 s 100 1 - day -
new 2 2 s 100 1 - day -
new 3 3 b 100 1 - day 100
new 4 4 b 100 2 - whole -
""")

_add("fill-capacity-is-supplied", """
pace fill
cap 5
mark 100
new 1 1 s 100 1 - day -
new 2 2 s 100 1 - day 100
new 3 3 b 100 2 - whole -
""")

_add("fill-last-unit-runs-the-batch", """
pace fill
cap 5
mark 100
new 1 1 s 100 1 - day -
new 2 2 b 90 1 - day 100
new 3 3 b 100 1 - whole -
""")

_add("fill-discloses-before-child-execution", """
pace fill
cap 5
mark 100
new 1 1 s 100 3 1 day -
new 2 2 b 100 1 - day 100
new 3 3 b 100 2 - whole -
""")

_add("fill-descendants-before-siblings", """
pace fill
cap 5
mark 100
new 1 1 s 100 1 - day -
new 2 2 s 101 1 - day -
new 3 3 s 102 1 - day -
new 20 4 b 102 1 - day 100
new 10 5 b 102 1 - day 100
new 15 6 b 90 1 - day 101
new 30 7 b 100 1 - part -
""")

_add("fill-child-failure-parent-commits", """
pace fill
cap 5
mark 100
new 1 1 s 100 1 - day -
new 2 2 s 100 1 - day -
new 3 3 b 100 2 - whole 100
new 4 4 b 100 1 - whole -
pull 2
pull 3
""")

_add("fill-child-failure-keeps-earlier-partial-fills", """
pace fill
cap 5
mark 100
new 1 1 s 100 1 - day -
new 2 2 s 100 1 - day -
new 3 3 b 100 2 - whole 100
new 4 4 b 100 2 - part -
""")

_add("fill-parent-failure-reruns-successful-child", """
pace fill
cap 5
mark 100
new 1 1 s 100 1 - day -
new 2 2 s 100 1 - day -
new 3 3 b 100 1 - whole 100
new 4 4 b 100 2 - whole -
pull 1
pull 2
pull 3
""")

_add("fill-parent-failure-reruns-failed-child", """
pace fill
cap 5
mark 100
new 1 1 s 100 1 - day -
new 2 2 b 100 3 - whole 100
new 3 3 b 100 2 - whole -
pull 2
""")

_add("fill-rollback-restores-disclosure-queue", """
pace fill
cap 5
mark 100
new 1 1 s 100 5 1 day -
new 2 2 s 100 2 - day -
new 3 3 b 100 2 - day 100
new 4 4 b 100 8 - whole -
new 5 5 b 100 1 - part -
pull 1
pull 2
""")

_add("fill-rollback-restores-last-price", """
pace fill
cap 3
mark 98
new 1 1 s 100 1 - day -
new 2 2 s 103 1 - day -
new 3 3 b 103 1 - day 100
new 4 4 b 106 2 - whole -
pull 1
new 5 5 b 103 1 - part -
""")

_add("fill-fired-batch-keeps-arrival-order", """
pace fill
cap 5
mark 100
new 1 1 s 100 2 - day -
new 30 2 b 90 1 - day 100
new 10 3 b 90 1 - day 100
new 20 4 b 100 3 - whole -
new 40 5 b 100 1 - part -
""")

_add("fill-child-price-moves-parent-band", """
pace fill
cap 3
mark 100
new 1 1 s 100 1 - day -
new 2 2 s 103 1 - day -
new 3 3 s 106 1 - day -
new 4 4 b 103 1 - day 100
new 5 5 b 106 2 - whole -
""")

_add("fill-child-same-hand-pull-is-atomic", """
pace fill
cap 5
mark 100
new 1 1 s 100 1 - day -
new 2 7 s 100 4 1 day -
new 3 7 b 100 1 - day 100
new 4 4 b 100 2 - whole -
pull 2
pull 3
""")

_add("fill-child-rest-removed-on-parent-failure", """
pace fill
cap 5
mark 100
new 1 1 s 100 1 - day -
new 2 2 b 90 1 - day 100
new 3 3 b 100 2 - whole -
pull 2
new 4 4 s 90 1 - part -
""")

_add("fill-sell-direction-and-no-price-whole", """
pace fill
cap 5
mark 100
new 1 1 b 100 1 - day -
new 2 2 b 100 1 - day 100
new 3 3 s - 2 - whole -
""")

_add("fill-child-failure-preserves-pending-sibling", """
pace fill
cap 5
mark 100
new 1 1 s 100 1 - day -
new 2 2 s 100 1 - day -
new 30 3 b 100 2 - whole 100
new 10 4 b 100 1 - whole 100
new 40 5 b 100 1 - whole -
""")

_add("fill-nested-failure-keeps-grandchild-fired", """
pace fill
cap 5
mark 100
new 1 1 s 100 1 - day -
new 2 2 s 101 1 - day -
new 3 3 s 102 1 - day -
new 4 4 b 102 3 - whole 100
new 5 5 b 90 1 - day 101
new 6 6 b 102 3 - whole -
""")

_add("order-selector-preserves-deferred-execution", """
pace order
cap 5
mark 100
new 1 1 s 100 1 - day -
new 2 2 s 100 1 - day -
new 3 3 b 100 1 - day 100
new 4 4 b 100 2 - whole -
""")

# ---------------------------------------------------------------- what a failed whole fired
# A firing is never taken back. Each case below has a whole order that comes up short after
# a fill that fired something; the pair of fences is the must-still-work side, where the
# failed order made no fill and so fired nothing.

_add("whole-keeps-what-it-fired", """
cap 40
mark 100
new 1 5 s 100 10 - day -
new 2 6 s 104 10 - day -
new 3 7 b 110 5 - day 102
new 4 8 b 110 30 - whole -
""")

_add("whole-fires-nothing-without-a-fill", """
cap 3
mark 98
new 1 5 s 103 10 - day -
new 2 6 b 110 5 - day 101
new 3 7 b 110 8 - whole -
""")

# The order that arrived first fires second; the batch after the cancellation is in
# arrival order, not in the order the discarded walk fired them.
_add("whole-fired-batch-is-arrival-order", """
cap 40
mark 100
new 1 5 s 100 10 - day -
new 2 6 s 104 10 - day -
new 3 7 b 110 4 - day 104
new 4 8 b 110 3 - day 100
new 5 9 b 110 30 - whole -
""")

# The failed whole was itself waiting; what it fired joins the end of the queue, behind
# the order that was already waiting after it.
_add("whole-fired-waits-its-turn", """
cap 40
mark 100
new 1 5 s 100 10 - day -
new 2 6 s 104 10 - day -
new 3 7 b 110 30 - whole 100
new 4 8 b 110 2 - day 100
new 5 9 b 110 5 - day 104
new 6 1 b 100 3 - day -
""")

_add("fill-parent-failure-keeps-child-fired", """
pace fill
cap 5
mark 100
new 1 1 s 100 2 1 day -
new 2 2 b 100 1 - day 100
new 3 3 b 100 3 - whole -
""")

# The inner whole fails and runs what it fired; the outer then fails and runs both of
# them again, announced once each after its own cancellation line.
_add("fill-nested-failure-fires-again", """
pace fill
cap 5
mark 100
new 1 1 s 100 1 1 day -
new 2 2 s 101 1 - day -
new 3 3 b 105 3 - whole 100
new 4 4 b 105 1 - day 101
new 5 5 b 105 5 - whole -
""")

_add("fill-fired-batch-precedes-waiting-siblings", """
pace fill
cap 5
mark 100
new 1 1 s 100 2 - day -
new 2 2 s 102 1 - day -
new 3 3 b 105 3 - whole 100
new 4 4 b 105 1 - day 100
new 5 5 b 105 1 - day 102
new 6 6 b 100 1 - day -
""")

_add("fill-fired-whole-stays-fired-under-parent-failure", """
pace fill
cap 5
mark 100
new 1 1 s 100 1 - day -
new 2 2 s 101 1 - day -
new 3 3 b 105 5 - whole 100
new 4 4 b 105 3 - whole -
""")

_add("fill-refired-order-fires-more", """
pace fill
cap 5
mark 100
new 1 1 s 100 1 - day -
new 2 2 s 103 1 - day -
new 3 3 b 105 1 - day 100
new 4 4 b 105 1 - day 103
new 5 5 b 105 3 - whole -
""")

_add("fill-failure-with-nothing-fired", """
pace fill
cap 5
mark 100
new 1 1 s 100 1 - day -
new 2 2 b 105 1 - day 103
new 3 3 b 105 3 - whole -
""")

# The inner whole succeeds and fires a grandchild; the outer fails, and the grandchild
# is announced and run again with the child, because it fired inside the outer's execution.
_add("fill-successful-child-firings-run-again", """
pace fill
cap 5
mark 100
new 1 1 s 100 1 - day -
new 2 2 s 101 1 - day -
new 3 3 s 102 1 - day -
new 4 4 b 105 1 - whole 100
new 5 5 b 105 1 - day 101
new 6 6 b 105 4 - whole -
""")

_add("fill-refired-order-starts-over", """
pace fill
cap 5
mark 100
new 1 1 s 100 3 1 day -
new 2 2 s 104 1 - day -
new 3 3 b 104 2 - day 100
new 4 4 b 104 6 - whole -
""")
