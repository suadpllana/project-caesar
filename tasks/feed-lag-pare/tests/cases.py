"""The enumerated programs: one per graded decision, plus the must-still-work side of each fence.

Every name says which rule its program pins. A wrong reading of that rule changes this
program's trace, so a failure names the rule rather than reporting that something differs
somewhere in four hundred programs. The answers live in seal/gt.json, frozen before the
grading file was written.
"""

PROGS = {
    # --- rule 1, the fold -------------------------------------------------------------
    "fold-add-absent": """
        add 0 3
        mark m
        read m 0
        pare 0
    """,
    "fold-add-after-del": """
        set 0 9
        del 0
        add 0 3
        mark m
        read m 0
        pare 0
    """,
    "fold-set-wins": """
        add 0 4
        set 0 2
        add 0 1
        mark m
        read m 0
        pare 0
    """,
    "fold-del-reads-absent": """
        set 0 5
        del 0
        mark m
        read m 0
        pare 0
    """,

    # --- rule 2, held points ----------------------------------------------------------
    "head-is-held": """
        set 0 1
        add 0 4
        add 0 -2
        pare 0
    """,
    "head-moves-on": """
        set 0 1
        add 0 4
        mark m
        add 0 -2
        add 0 -1
        pare 0
    """,
    "two-pins-one-point": """
        set 0 1
        add 0 1
        mark m
        mark n
        add 0 1
        pare 0
        unmark n
        pare 0
    """,
    "unmark-merges": """
        set 0 1
        add 0 1
        mark m
        add 0 5
        pare 0
        unmark m
        pare 0
    """,

    # --- rules 3 and 4, the trailing point and the kept region ------------------------
    "feed-keeps-above": """
        set 0 1
        feed f 0 0
        add 0 4
        add 0 -2
        read f 0
        pare 0
    """,
    "feed-covers-range": """
        set 0 1
        set 1 1
        feed f 0 0
        add 0 4
        add 1 4
        pare 0
    """,
    "feed-lowest-wins": """
        set 0 1
        add 0 1
        feed f 0 0
        add 0 1
        add 0 1
        feed g 0 0
        add 0 1
        pare 0
    """,
    "feed-close-frees": """
        set 0 1
        feed f 0 0
        add 0 2
        add 0 3
        pare 0
        close f
        pare 0
    """,
    "feed-outside-collapses": """
        set 3 1
        add 3 1
        feed f 0 1
        add 3 1
        pare 0
    """,

    # --- rule 10, acknowledgements ----------------------------------------------------
    "ack-moves-up": """
        set 0 1
        add 0 1
        feed f 0 0
        add 0 1
        ack f 2
        read f 0
        pare 0
    """,
    "ack-back-refused": """
        set 0 1
        add 0 1
        add 0 1
        feed f 0 0
        ack f 1
        read f 0
        pare 0
    """,
    "ack-at-head": """
        set 0 1
        feed f 0 0
        add 0 1
        add 0 1
        ack f 3
        read f 0
        pare 0
    """,
    "ack-past-head-refused": """
        set 0 1
        feed f 0 0
        add 0 1
        ack f 9
        read f 0
        pare 0
    """,

    # --- rules 6, 7 and 8, what a collapse leaves -------------------------------------
    "span-nil-keeps-none": """
        set 0 1
        mark m
        add 0 4
        add 0 -4
        pare 0
    """,
    "span-absent-both-ends": """
        del 0
        mark m
        set 0 5
        del 0
        pare 0
    """,
    "span-one-entry-stands": """
        set 0 1
        add 0 4
        mark m
        add 0 -2
        pare 0
    """,
    "span-keeps-last": """
        set 0 1
        add 0 4
        add 0 2
        pare 0
    """,
    "span-kind-is-set": """
        add 0 2
        add 0 3
        pare 0
    """,
    "span-kind-is-del": """
        set 0 7
        mark m
        add 0 1
        del 0
        pare 0
    """,
    "span-last-retained": """
        add 0 -5
        add 0 -5
        mark p
        add 0 3
        add 0 -3
        add 0 3
        add 0 -3
        pare 2
        unmark p
        pare 0
    """,

    # --- rule 9, the budgeted pare ----------------------------------------------------
    "pare-most-first": """
        set 1 1
        add 1 1
        add 1 1
        set 0 1
        add 0 1
        mark m
        pare 3
    """,
    "pare-tie-lower-span": """
        set 0 1
        add 0 1
        mark m
        add 0 1
        add 0 1
        pare 3
    """,
    "pare-tie-smaller-key": """
        set 1 1
        add 1 1
        set 0 1
        add 0 1
        pare 3
    """,
    "pare-stops-at-budget": """
        set 0 1
        add 0 1
        add 0 1
        add 0 1
        pare 4
        pare 1
    """,
    "pare-nothing-to-take": """
        set 0 1
        mark m
        add 0 1
        mark n
        add 0 1
        pare 0
    """,

    # --- the report and the ordinary fences -------------------------------------------
    "report-key-order": """
        set 2 1
        set 0 1
        set 1 1
        add 2 1
        add 0 1
        pare 0
    """,
    "read-survives-pare": """
        set 0 4
        add 0 3
        mark m
        add 0 5
        add 0 -1
        mark n
        add 0 2
        read m 0
        pare 0
        read m 0
        read n 0
    """,
    "floor-only-is-right": """
        set 0 1
        add 0 2
        add 0 3
        set 1 4
        add 1 1
        mark m
        add 0 1
        add 1 1
        pare 0
    """,
    "nothing-may-go": """
        set 0 1
        mark m
        set 1 2
        mark n
        set 0 3
        feed f 0 1
        set 1 4
        pare 0
    """,
}

ORDER = tuple(sorted(PROGS))


def prog(name):
    """One program as a list of lines."""
    return [line.strip() for line in PROGS[name].strip().splitlines()]
