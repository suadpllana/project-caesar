"""The ordinary cases: the side of each fence that a careful-but-overreaching stage breaks.

The wrong readings get their case from hunt.py, which searches for one. These are written
rather than searched, because what they pin is that nothing happens: no refusal, no eviction,
no early halt, and a request that cannot see the one before it.
"""

HAND = {
    # Room for everyone. Nothing is refused, nothing is evicted, and both requests run the
    # whole ceiling out; a stage that leans on the kept set to make progress breaks here.
    "easy-run": """cfg 3 2 2 1 3 5
sc 1 2 9
sc 1 3 7
sc 1 4 5
sc 2 3 8
sc 2 4 6
sc 2 5 4
sc 3 4 7
sc 3 5 6
sc 3 1 3
sc 4 5 8
sc 4 1 5
sc 4 2 4
sc 5 1 7
sc 5 2 6
sc 5 3 5
sc 4 0 2
ask one 1
ask two 2""",

    # A beam that reaches the kept set is still a beam: it closes at one step and is expected
    # to produce a longer hypothesis at a later one.
    "close-goes-on": """cfg 1 3 1 0 4 6
sc 1 2 5
sc 2 3 6
sc 3 4 7
sc 4 5 8
sc 5 6 9
sc 2 0 1
sc 3 0 1
sc 4 0 1
sc 5 0 1
sc 6 0 1
ask on 1""",

    # The same prompt asked twice. The second block must be the first one over again: no span,
    # no member and no numbering survives a request.
    "ask-apart": """cfg 2 2 1 1 2 5
sc 1 2 6
sc 2 3 5
sc 3 2 4
sc 2 1 3
sc 1 3 7
sc 3 0 2
sc 2 0 1
ask first 1
ask again 1""",

    # No stop row anywhere: nothing closes, nothing is lent, and the report is empty.
    "never-close": """cfg 2 2 1 0 2 4
sc 1 2 5
sc 2 3 4
sc 3 1 3
sc 1 3 2
sc 2 1 6
ask run 1""",

    # The last prompt token has no continuation at all, so the first step takes nothing.
    "no-row": """cfg 2 2 1 0 1 6
sc 1 2 5
sc 2 3 4
sc 9 0 3
ask stuck 1 9""",

    # A kept set of one, met by a hypothesis worse than the one it holds: the new member is
    # taken in and given up on the same step.
    "self-drop": """cfg 1 3 1 0 1 6
sc 1 2 9
sc 2 3 9
sc 3 4 1
sc 4 5 1
sc 2 0 9
sc 3 0 1
sc 4 0 1
sc 5 0 1
ask drop 1""",

    # A prompt shorter than a span, so the first steps have no span to repeat.
    "short-prompt": """cfg 2 4 1 0 2 8
sc 1 2 6
sc 2 3 5
sc 3 1 4
sc 1 3 3
sc 3 2 7
sc 2 1 2
sc 3 0 1
ask brief 1""",

    # Five continuations on five tokens against three slots: exactly three are taken, and the
    # two that miss are the two lowest.
    "width-take": """cfg 3 2 1 0 2 4
sc 1 2 9
sc 1 3 8
sc 1 4 7
sc 1 5 6
sc 1 6 5
sc 2 3 4
sc 3 4 4
sc 4 5 4
sc 2 0 3
sc 3 0 3
ask five 1""",

    # One score everywhere, so the smaller slot, then the smaller token, then the order the
    # members entered decide every line.
    "tie-all": """cfg 2 2 1 0 3 5
sc 1 2 3
sc 1 3 3
sc 2 3 3
sc 2 1 3
sc 3 1 3
sc 3 2 3
sc 1 0 3
sc 2 0 3
sc 3 0 3
ask flat 1""",

    # A hypothesis that closes on its first allowed step against one that closes far later,
    # with a penalty big enough to put the short one ahead on the report.
    "penalty-wins": """cfg 2 3 1 3 2 7
sc 1 2 9
sc 2 3 9
sc 3 4 4
sc 4 5 4
sc 5 6 4
sc 2 0 9
sc 6 0 9
sc 3 0 1
sc 4 0 1
sc 5 0 1
ask pen 1""",
}
