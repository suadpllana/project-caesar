"""The enumerated programs: one per graded decision, plus the must-still-work side of each
fence. Every name below is referred to by the grader's docstring and by a cheat, so a wrong
reading of any one rule fails a case that names it.

Geometry the programs are built against, all of it from `pan/mtr.py`: a row of text length
L at panel width W stands 18 * ceil(L / W) + 6 tall, the view is 300 tall, the panel opens
40 wide, and a row nobody has measured is assumed to be 24 tall while no row has been
measured. So at the opening width a row of 30 characters is 24 tall, one of 60 is 42, one
of 190 is 96 and one of 460 is 222.
"""

CASE = {
    # 1. the assumed height is the floor mean of the measured rows, the default only
    #    while none of them is measured
    "mean-none": [
        "bulk 8 30 4",
        "tall",
        "face",
    ],
    "mean-one": [
        "ins 0 big 460",
        "bulk 8 30 4",
        "pass",
        "tall",
        "top",
    ],
    "mean-floor": [
        "bulk 3 30 1",
        "ins 3 d 60",
        "pass",
        "ins 4 z 30",
        "tall",
        "top",
        "face",
    ],
    # 2. the assumption reaches every unmeasured row, so a measurement moves the rows
    #    ahead of the anchor as well as the ones behind it
    "mean-above": [
        "bulk 40 30 170",
        "roll 500",
        "pass",
        "top",
        "tall",
        "face",
    ],
    # 3. a pass measures one row, re-seats, and asks again
    "pass-grow": [
        "bulk 30 30 4",
        "ins 12 big 460",
        "roll 288",
        "pass",
        "seen_marker",
        "top",
        "tall",
        "face",
    ],
    "pass-none": [
        "bulk 8 30 4",
        "pass",
        "pass",
        "top",
        "tall",
    ],
    "pass-shrink": [
        "bulk 6 460 4",
        "bulk 20 30 4",
        "roll 900",
        "pass",
        "top",
        "tall",
        "face",
    ],
    # 4. the anchor is taken before anything is measured
    "anchor-first": [
        "bulk 15 20 4",
        "ins 0 big 300",
        "pass",
        "roll 400",
        "pass",
        "pass",
        "set k5 460",
        "top",
        "tall",
        "face",
    ],
    # 5. the held distance survives a clamp inside the pass
    "clamp-mid": [
        "bulk 20 30 4",
        "ins 18 big 460",
        "roll 4000",
        "pass",
        "top",
        "tall",
        "face",
    ],
    "clamp-fall": [
        "bulk 8 460 4",
        "bulk 22 30 4",
        "roll 0",
        "pass",
        "top",
        "roll 40000",
        "pass",
        "top",
        "tall",
        "face",
        "pass",
        "top",
        "face",
    ],
    "clamp-hold": [
        "bulk 36 38 4",
        "pass",
        "roll 1200",
        "pass",
        "top",
        "tall",
        "face",
    ],
    # 6. a re-seat is clamped to the scroll range from both ends
    "clamp-shrink": [
        "bulk 30 30 4",
        "roll 240",
        "del k30",
        "del k29",
        "del k28",
        "del k27",
        "del k26",
        "del k25",
        "del k24",
        "del k23",
        "del k22",
        "del k21",
        "top",
        "tall",
        "face",
    ],
    "clamp-zero": [
        "bulk 30 30 4",
        "roll 100",
        "del k1",
        "del k2",
        "del k3",
        "del k4",
        "del k5",
        "top",
        "face",
    ],
    # 7. roll clamps, then takes the anchor from where it landed
    "roll-past": [
        "bulk 20 30 4",
        "roll 9000",
        "top",
        "face",
        "ins 0 a 460",
        "top",
    ],
    "roll-back": [
        "bulk 20 30 4",
        "roll 300",
        "roll -9000",
        "top",
        "face",
    ],
    # 8. every edit re-seats against the held anchor
    "ins-above": [
        "bulk 30 30 4",
        "roll 240",
        "face",
        "ins 0 a 190",
        "top",
        "face",
    ],
    "ins-below": [
        "bulk 30 30 4",
        "roll 240",
        "ins 29 z 460",
        "top",
        "tall",
        "face",
    ],
    "del-above": [
        "bulk 30 30 4",
        "roll 240",
        "del k1",
        "top",
        "face",
    ],
    # 9. deleting the anchor falls to the row that took its index
    "del-anchor": [
        "bulk 30 30 4",
        "roll 240",
        "face",
        "del k11",
        "ins 0 a 190",
        "top",
        "face",
    ],
    "del-last": [
        "bulk 20 30 4",
        "roll 9000",
        "face",
        "del k20",
        "del k19",
        "top",
        "face",
    ],
    "del-tail": [
        "bulk 40 30 4",
        "ins 40 tail 700",
        "roll 40000",
        "pass",
        "roll 40000",
        "face",
        "del tail",
        "bulk 30 30 4",
        "top",
        "face",
        "tall",
    ],
    "del-all": [
        "bulk 4 30 4",
        "roll 40",
        "del k1",
        "del k2",
        "del k3",
        "del k4",
        "top",
        "tall",
        "face",
        "pass",
    ],
    # 10. a move keeps the row's measurement and its anchor role
    "move-keep": [
        "bulk 8 30 4",
        "ins 0 big 460",
        "pass",
        "tall",
        "move big 8",
        "tall",
        "top",
    ],
    "move-anchor": [
        "bulk 30 30 4",
        "roll 240",
        "face",
        "move k11 0",
        "top",
        "face",
    ],
    # 11. re-texting a row gives up its measurement, and a sample from the mean
    "set-drop": [
        "bulk 8 30 4",
        "ins 0 big 460",
        "pass",
        "tall",
        "set big 30",
        "tall",
    ],
    "set-mean": [
        "ins 0 a 460",
        "ins 1 b 190",
        "bulk 8 30 4",
        "pass",
        "tall",
        "set a 30",
        "tall",
        "top",
        "face",
    ],
    # 12. a width change gives up every measurement
    "span-all": [
        "bulk 10 60 4",
        "pass",
        "tall",
        "span 12",
        "tall",
        "top",
    ],
    "span-again": [
        "bulk 10 60 4",
        "pass",
        "span 12",
        "pass",
        "tall",
        "face",
    ],
    # 13. face names the first row the view touches, and its edge relative to the view's
    "face-inside": [
        "bulk 20 30 4",
        "roll 250",
        "face",
    ],
    "face-edge": [
        "bulk 20 30 4",
        "roll 240",
        "face",
    ],
    "face-empty": [
        "face",
        "tall",
        "top",
    ],
    # a name that is not in the list does nothing, a re-seat included
    "gone-name": [
        "bulk 30 30 4",
        "ins 12 big 460",
        "roll 40000",
        "pass",
        "top",
        "del nosuch",
        "set nosuch 30",
        "move nosuch 0",
        "top",
        "face",
        "tall",
    ],
    # 14. tall counts the unmeasured rows at the assumed height
    "tall-mixed": [
        "bulk 30 30 170",
        "roll 200",
        "pass",
        "tall",
    ],
    # the late cases: everything ordinary passes first, then one sample leaves the mean
    "late-set": [
        "bulk 26 30 170",
        "roll 9000",
        "pass",
        "top",
        "tall",
        "set k1 460",
        "top",
        "tall",
        "pass",
        "top",
        "tall",
        "face",
    ],
    "late-churn": [
        "bulk 18 30 170",
        "roll 300",
        "pass",
        "ins 2 a 460",
        "pass",
        "move a 17",
        "del k9",
        "pass",
        "set k12 460",
        "span 25",
        "pass",
        "roll 120",
        "pass",
        "top",
        "tall",
        "face",
    ],
}

CASE["pass-grow"].remove("seen_marker")

ORDER = tuple(sorted(CASE))


def ops(name):
    return list(CASE[name])
