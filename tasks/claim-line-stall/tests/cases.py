"""The enumerated programs: one per graded decision, and both sides of every fence.

Each is small enough to work by hand and is aimed at exactly one reading. Where a decision
has two ways to be wrong - refusing what should be granted and granting what should be held -
both sides appear, because a service that turns conservative passes a set that only tests the
failure side.

Answers for these are frozen in `seal/gt.json`, written before the grading file existed, and
the grader asserts that the sealed model still reproduces that file byte for byte before it
judges anything.
"""

PROGRAMS = {

    # --- coverage: an ask the job's own claims already satisfy ------------------------

    "cover-same": """
        take j1 u1/c1 w
        take j1 u1/c1 r
        take j2 u1/c1 r
        show u1
    """,

    "cover-unit": """
        take j1 u1 r
        take j1 u1/c3 r
        show u1
        drop j1 u1
        show u1
    """,

    "cover-weak": """
        take j2 u1/c3 r
        take j1 u1 r
        take j1 u1/c3 w
        show u1
    """,

    # --- the refusal test: held claims, and asks standing ahead -----------------------

    "fair-hold": """
        take j1 u1/c1 w
        take j2 u1/c1 r
        show u1
    """,

    "fair-wait": """
        take j1 u1/c1 r
        take j2 u1/c1 w
        take j3 u1/c1 r
        show u1
    """,

    "fair-grant": """
        take j1 u1/c1 r
        take j3 u1/c1 r
        take j4 u1/c2 w
        show u1
    """,

    "fair-apart": """
        take j1 u1/c1 r
        take j2 u1/c1 w
        take j3 u1/c2 r
        show u1
    """,

    # --- the order of the line, and that it is read rather than stamped ---------------

    "ahead-lift": """
        take j1 u1 r
        take j2 u1 w
        take j1 u1/c2 w
        show u1
    """,

    "ahead-flip": """
        take j1 u1/c1 w
        take j3 u1/c5 r
        take j2 u1 r
        take j1 u1 w
        drop j1 u1/c1
        show u1
    """,

    "ahead-two": """
        take j1 u1/c1 w
        take j2 u1 r
        take j3 u1/c1 r
        take j1 u1 w
        show u1
    """,

    # --- raising a cell ask to the whole unit -----------------------------------------

    "raise-four": """
        take j1 u1/c1 r
        take j1 u1/c2 r
        take j1 u1/c3 r
        take j1 u1/c4 r
        take j1 u1/c5 r
        show u1
    """,

    "raise-three": """
        take j1 u1/c1 r
        take j1 u1/c2 r
        take j1 u1/c3 r
        take j1 u1/c4 r
        show u1
    """,

    "raise-apart": """
        take j1 u1/c1 r
        take j1 u1/c2 r
        take j1 u2/c1 r
        take j1 u2/c2 r
        take j1 u1/c3 r
        show u1
        show u2
    """,

    "raise-mode": """
        take j1 u1/c1 r
        take j1 u1/c2 w
        take j1 u1/c3 r
        take j1 u1/c4 r
        take j2 u1/c9 r
        take j1 u1/c5 r
        show u1
    """,

    "raise-hold": """
        take j1 u1/c1 w
        take j1 u1/c2 w
        take j1 u1/c3 w
        take j1 u1/c4 w
        take j2 u1/c7 r
        take j1 u1/c5 w
        take j3 u1/c2 r
        show u1
    """,

    "raise-swallow": """
        take j1 u1/c1 r
        take j1 u1/c2 r
        take j1 u1/c3 r
        take j1 u1/c4 r
        take j1 u1/c5 r
        show u1
        drop j1 u1/c1
        drop j1 u1
        show u1
    """,

    # --- settling after a release ------------------------------------------------------

    "settle-order": """
        take j1 u1/c1 r
        take j2 u1/c1 w
        take j3 u1/c1 r
        drop j1 u1/c1
        show u1
    """,

    "settle-once": """
        take j1 u1 w
        take j2 u1/c1 r
        take j3 u1/c2 r
        take j4 u1 w
        end j1
        show u1
    """,

    "settle-blocked": """
        take j1 u1/c1 w
        take j2 u1/c1 r
        take j3 u1/c2 w
        take j4 u1/c2 r
        drop j1 u1/c1
        show u1
    """,

    # --- when a job is forgotten, and what that does to its number ---------------------

    "forget-new": """
        take j1 u1/c1 r
        take j2 u1/c2 r
        drop j1 u1/c1
        take j1 u1/c3 r
        show u1
    """,

    "forget-wait": """
        take j1 u1/c1 w
        take j2 u1/c1 r
        take j3 u1/c2 r
        drop j1 u1/c1
        show u1
    """,

    # --- jobs that can never proceed, and which one is cancelled -----------------------

    "knot-hold": """
        take j1 u1/c1 w
        take j2 u1/c2 w
        take j1 u1/c2 w
        take j2 u1/c1 w
        show u1
    """,

    "knot-ahead": """
        take j1 u1/c1 r
        take j2 u1 w
        take j3 u1/c2 r
        take j1 u1/c2 w
        show u1
    """,

    "knot-none": """
        take j1 u1/c1 w
        take j2 u1/c1 w
        take j3 u1/c1 w
        show u1
        drop j1 u1/c1
        show u1
    """,

    "knot-raise": """
        take j1 u1/c1 w
        take j1 u1/c2 w
        take j1 u1/c3 w
        take j1 u1/c4 w
        take j2 u1/c7 w
        take j1 u1/c5 w
        take j2 u1/c1 r
        show u1
    """,

    "pick-few": """
        take j1 u1/c1 w
        take j1 u1/c2 w
        take j2 u2/c1 w
        take j1 u2/c1 w
        take j2 u1/c1 w
        show u1
        show u2
    """,

    "pick-young": """
        take j1 u1/c1 w
        take j2 u2/c1 w
        take j1 u2/c1 w
        take j2 u1/c1 w
        show u1
    """,


    "knot-apart": """
        take j3 u1/c9 w
        take j2 u1/c5 w
        take j1 u1/c5 r
        take j2 u1/c9 r
        show u1
    """,

    "pick-old": """
        take j1 u1/c1 w
        take j2 u2/c1 w
        take j2 u2/c2 w
        take j1 u2/c1 w
        take j2 u1/c1 w
        show u1
        show u2
    """,

    "settle-pair": """
        take j1 u1/c1 w
        take j2 u1/c1 r
        take j3 u1/c1 r
        drop j1 u1/c1
        show u1
    """,

    "settle-jump": """
        take j1 u1/c1 w
        take j2 u1/c1 w
        take j3 u1/c2 r
        take j3 u1 r
        drop j1 u1/c1
        show u1
    """,


    "settle-swap": """
        take j1 u1/c1 w
        take j2 u1/c1 r
        take j3 u1/c9 r
        take j3 u1 r
        drop j1 u1/c1
        show u1
    """,

    "fair-share": """
        take j1 u1/c5 w
        take j2 u1 r
        take j3 u1/c1 r
        show u1
    """,

    # --- the ops themselves -------------------------------------------------------------

    "busy-take": """
        take j1 u1/c1 w
        take j2 u1/c1 r
        take j2 u2/c1 r
        drop j1 u1/c1
        show u1
        show u2
    """,

    "end-ask": """
        take j1 u1/c1 w
        take j2 u1/c1 r
        take j3 u1/c1 r
        end j2
        drop j1 u1/c1
        show u1
    """,

    "drop-none": """
        take j1 u1/c1 r
        drop j1 u1/c2
        drop j2 u1/c1
        drop j1 u1
        end j5
        show u1
    """,

    "show-order": """
        take j2 u1/c4 r
        take j1 u1 r
        take j1 u1/c10 w
        take j1 u1/c2 w
        show u1
        show u2
    """,
}

ORDER = tuple(sorted(PROGRAMS))


def ops(name):
    return [line.strip() for line in PROGRAMS[name].strip().splitlines()]
