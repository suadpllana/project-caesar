"""The enumerated programs: one per graded decision, plus the side of each fence that has to
keep working.

Every case is small enough to read as a trace by hand, and each one was written for a specific
wrong reading. The name says which. `authoring/publish-settle-order/readings.py` checks that
this set actually separates those readings rather than only covering them on paper.
"""

CASES = {
    # --- ordinary behaviour: a publisher answers, a hold released takes its unit down -------
    "plain": [
        "unit u1", "pub u1 s1", "unit u2",
        "act u1", "act u2", "call u2 s1", "rel u2", "rel u1",
    ],
    # --- dependencies come up before the unit that named them, in declaration order ---------
    "deep": [
        "unit u1", "unit u2", "unit u3", "dep u3 u1", "dep u3 u2",
        "act u3",
    ],
    "dep-order": [
        "unit u1", "unit u2", "unit u3", "dep u3 u2", "dep u3 u1",
        "act u3",
    ],
    "rel-early": [
        "unit u1", "unit u2", "dep u2 u1",
        "act u2", "rel u1", "act u1", "rel u2",
    ],
    "chain": [
        "unit u1", "unit u2", "unit u3", "dep u3 u2", "dep u2 u1",
        "act u3", "rel u3",
    ],
    # --- a startup call resolves against the order as it stands at that moment --------------
    "boot-partial": [
        "unit u1", "unit u2", "dep u1 u2", "pub u1 s1", "boot u2 s1",
        "act u1", "call u2 s1",
    ],
    "boot-cycle": [
        "unit u1", "unit u2", "dep u1 u2", "dep u2 u1",
        "pub u1 s1", "pub u2 s2", "boot u1 s2", "boot u2 s1",
        "act u1",
    ],
    "boot-order": [
        "unit u1", "unit u2", "pub u2 s1", "pub u2 s2", "dep u1 u2",
        "boot u1 s2", "boot u1 s1",
        "act u1", "call u1 s1",
    ],
    # --- an ordering edge decides when a unit comes up and keeps nothing afterwards -------
    "pre-order": [
        "unit u1", "unit u2", "unit u3", "pre u3 u2", "dep u3 u1",
        "act u3",
    ],
    "pre-no-keep": [
        "unit u1", "unit u2", "pre u2 u1",
        "act u2", "act u1", "rel u1",
    ],
    "pre-vs-dep": [
        "unit u1", "unit u2", "unit u3", "dep u3 u1", "pre u3 u2",
        "act u3", "act u1", "act u2", "rel u1", "rel u2",
    ],
    # --- a fallback publication competes on publication order, not on being a fallback ------
    "fall-first": [
        "unit u1", "fall u1 s1", "unit u2", "pub u2 s1", "unit u3",
        "act u1", "act u2", "act u3", "call u3 s1",
    ],
    "fall-late": [
        "unit u1", "pub u1 s1", "unit u2", "fall u2 s1", "unit u3",
        "act u1", "act u2", "act u3", "call u3 s1",
    ],
    "fall-only": [
        "unit u1", "fall u1 s1", "unit u2",
        "act u1", "act u2", "call u2 s1",
    ],
    # --- an unanswered call settles nothing --------------------------------------------------
    "miss-open": [
        "unit u1", "unit u2", "pub u2 s1",
        "act u1", "call u1 s1", "act u2", "call u1 s1",
    ],
    "miss-boot": [
        "unit u1", "unit u2", "dep u1 u2", "boot u2 s1", "unit u3", "pub u3 s1",
        "act u1", "call u2 s1", "act u3", "call u2 s1",
    ],
    # --- a settled use is never resolved again ----------------------------------------------
    "stick-dead": [
        "unit u1", "unit u2", "pub u2 s1", "unit u3", "pub u3 s1",
        "act u2", "act u3", "act u1", "call u1 s1", "rel u2", "call u1 s1",
    ],
    "dead-stays": [
        "unit u1", "unit u2", "pub u2 s1", "unit u3", "pub u3 s1",
        "act u2", "act u1", "call u1 s1", "rel u2", "act u3",
        "call u1 s1", "call u1 s1",
    ],
    # --- a name that comes back is not the unit that left ------------------------------------
    "same-name": [
        "unit u1", "unit u2", "pub u2 s1",
        "act u2", "act u1", "call u1 s1", "rel u2", "act u2", "call u1 s1",
    ],
    "fresh-instance": [
        "unit u1", "unit u2", "pub u2 s1", "unit u3", "pub u3 s1",
        "act u2", "act u1", "call u1 s1", "rel u1", "act u3", "rel u2",
        "act u1", "call u1 s1",
    ],
    # --- holds ------------------------------------------------------------------------------
    "hold-two": [
        "unit u1", "act u1", "act u1", "rel u1", "rel u1",
    ],
    "rel-nohold": [
        "unit u1", "act u1", "rel u1", "rel u1", "act u1", "rel u1",
    ],
    "dep-holds": [
        "unit u1", "unit u2", "dep u2 u1",
        "act u1", "act u2", "rel u1", "rel u2",
    ],
    "stay-put": [
        "unit u1", "pub u1 s1", "unit u2", "pub u2 s1", "unit u3",
        "act u1", "act u2", "act u1", "act u3", "call u3 s1",
    ],
    # --- what a released hold takes down with it, and in what order --------------------------
    "casc-order": [
        "unit u1", "unit u2", "unit u3", "dep u3 u1", "dep u3 u2",
        "act u3", "rel u3",
    ],
    "casc-part": [
        "unit u1", "unit u2", "unit u3", "dep u3 u1", "dep u3 u2",
        "act u3", "act u2", "rel u3", "rel u2",
    ],
    # --- a call from a unit that is not live is not a call -----------------------------------
    "not-live": [
        "unit u1", "unit u2", "pub u2 s1",
        "act u2", "call u1 s1", "act u1", "call u1 s1", "rel u1", "call u1 s1",
    ],
}

ORDER = sorted(CASES)


def ops(name):
    return list(CASES[name])
