"""The enumerated programs: one per graded decision, and the ordinary side of each fence.

Every name under `WRONG` is the name of a wrong reading of the contract, and the program is
the smallest one found that the reading gets wrong: a failure here says which rule broke
rather than "some of the generated programs differ". The names under `PLAIN` are written
rather than searched, and each pins that something does *not* happen - no refusal, no
eviction, no early halt, nothing carried from the request before.

Frozen answers for all of them live in `seal/gt.json`.
"""

WRONG = {
    # the reach lets a penalty above the largest score pull it down
    "bound-negative": """cfg 2 3 4 6 3 9
sc 1 2 5
sc 2 1 4
sc 1 1 1
sc 2 2 5
sc 1 0 1
ask q0 2""",
    # the reach is tested before the kept set is full
    "bound-nofull": """cfg 1 2 1 0 1 2
sc 1 4 8
ask q0 4 1""",
    # the reach ignores the penalty on the steps still to come
    "bound-nopen": """cfg 1 2 1 2 1 4
sc 2 2 2
sc 2 0 3
sc 3 2 3
ask q0 3""",
    # the reach is read off the raw score with no penalty at all
    "bound-raw": """cfg 1 2 1 1 1 3
sc 2 2 2
sc 2 0 3
sc 3 2 3
ask q0 3""",
    # the stop token is offered as an ordinary continuation too
    "cand-stop": """cfg 3 3 2 0 1 4
sc 3 2 6
sc 1 4 8
sc 1 3 9
sc 3 4 6
sc 4 1 3
sc 3 0 4
ask q0 4 1""",
    # the ceiling is read one step early
    "cap-early": """cfg 1 2 1 0 1 2
sc 1 3 9
ask q0 4 1""",
    # the beam takes the stop row's score with it when it closes
    "close-absorbs": """cfg 1 3 1 0 1 6
sc 3 2 6
sc 2 3 5
sc 1 2 6
sc 4 1 3
sc 3 0 4
ask q0 4""",
    # closures are settled after the step's candidates are ranked
    "close-after": """cfg 2 2 1 0 1 4
sc 3 2 6
sc 2 3 5
sc 2 2 8
sc 1 3 9
sc 3 0 4
ask q0 4 1""",
    # the ceiling is read before the empty selection
    "halt-order": """cfg 2 2 1 0 1 9
sc 6 5 2
sc 5 3 9
sc 3 5 1
sc 6 6 9
sc 3 6 9
sc 5 6 9
sc 3 3 9
sc 6 3 9
ask q0 3""",
    # the kept set is numbered from one
    "hyp-one": """cfg 1 2 1 0 1 2
sc 1 3 9
sc 3 0 4
ask q0 4 1""",
    # the kept set is printed with the prompt in front of the tokens
    "hyp-prompt": """cfg 1 2 1 0 1 2
sc 1 3 9
sc 3 0 4
ask q0 4 1""",
    # a member lends only the spans that lie inside what it emitted
    "lend-emitted": """cfg 2 2 1 0 1 2
sc 1 0 1
sc 2 1 5
sc 2 2 1
ask q0 1 1 1 2""",
    # the lent spans are one set, so an eviction frees a span another member holds
    "lend-flat": """cfg 2 2 1 0 2 4
sc 3 0 3
sc 3 3 5
sc 1 0 1
sc 2 3 1
sc 1 3 4
sc 3 1 2
ask q1 3 2""",
    # an evicted hypothesis keeps its bans
    "lend-keeps": """cfg 2 3 1 0 1 6
sc 3 2 6
sc 2 3 5
sc 2 2 8
sc 1 3 9
sc 3 0 4
ask q0 4 1""",
    # a closed hypothesis bans nothing
    "lend-none": """cfg 2 2 1 0 1 4
sc 3 2 6
sc 2 3 5
sc 2 2 8
sc 1 3 9
sc 3 0 4
ask q0 4 1""",
    # the kept set is listed with the longer hypothesis first on a tie
    "list-tie": """cfg 2 2 1 1 2 5
sc 3 0 3
sc 3 3 5
sc 2 1 5
sc 1 3 4
sc 1 2 3
sc 2 0 4
sc 3 1 2
ask q1 3 2""",
    # the repeat test covers only the tokens the search emitted
    "own-emitted": """cfg 1 2 1 0 1 2
sc 1 2 4
sc 2 1 4
ask q0 2 1""",
    # a sequence exactly as long as a span is treated as too short
    "own-short": """cfg 1 2 1 0 1 4
sc 3 2 6
sc 2 3 5
sc 1 3 9
ask q0 4 1""",
    # the kept set gives one up as soon as it holds H
    "pool-atleast": """cfg 1 2 1 0 1 2
sc 1 3 9
sc 3 0 4
ask q0 4 1""",
    # a full kept set refuses later hypotheses instead of dropping its worst
    "pool-first": """cfg 2 2 1 0 1 4
sc 2 3 5
sc 1 3 9
sc 1 2 6
sc 4 1 3
sc 3 0 4
ask q0 4""",
    # the kept set gives up its oldest member
    "pool-oldest": """cfg 1 2 1 2 1 4
sc 3 2 6
sc 2 3 5
sc 1 3 9
sc 3 0 4
sc 2 0 7
ask q0 4 1""",
    # a tie on the final score goes to the longer hypothesis
    "pool-tielen": """cfg 1 2 1 0 1 4
sc 3 0 3
sc 2 3 1
sc 3 2 4
sc 1 3 4
sc 2 0 4
ask q0 1""",
    # a tie on score and length goes to the later hypothesis
    "pool-tieorder": """cfg 2 2 1 0 1 3
sc 3 0 3
sc 3 3 5
sc 2 3 1
sc 3 2 4
sc 2 0 4
ask q0 1 1 1 2""",
    # a tie on score goes to the larger slot
    "rank-slotdesc": """cfg 2 2 1 0 1 4
sc 3 2 6
sc 2 2 8
sc 1 3 9
sc 1 1 8
ask q0 4 1""",
    # a tie on score and place goes to the larger token
    "rank-tokdesc": """cfg 1 2 1 0 1 4
sc 3 2 6
sc 2 2 8
sc 1 3 9
sc 2 1 8
ask q0 4 1""",
    # a tie on score goes to the smaller token before the smaller slot
    "rank-toktie": """cfg 3 3 3 0 1 6
sc 3 2 6
sc 1 3 9
sc 2 1 8
sc 1 1 8
sc 2 0 7
ask q0 4 1""",
    # the beams are the top w by score with no rule about the final token
    "rank-topw": """cfg 3 3 1 0 1 5
sc 3 2 6
sc 2 3 5
sc 2 2 8
sc 1 2 6
sc 3 0 4
ask q0 4 1""",
    # one more beam is taken than the width allows
    "rank-wplus": """cfg 1 2 1 0 1 2
sc 3 2 6
sc 1 2 4
sc 1 3 1
ask q0 2 1""",
    # closures are settled from the last beam back
    "shut-desc": """cfg 2 2 1 0 1 4
sc 3 2 6
sc 2 3 5
sc 2 2 8
sc 1 3 9
sc 3 0 4
sc 2 0 7
ask q0 4 1""",
    # the floor is passed one token early
    "stop-floor": """cfg 1 2 3 0 1 3
sc 2 3 5
sc 1 2 6
sc 3 0 4
ask q0 4 1""",
    # the stop token counts toward the length
    "stop-len": """cfg 1 2 1 0 1 2
sc 1 3 9
sc 3 0 4
ask q0 4 1""",
    # the stop row's score is not counted
    "stop-noscore": """cfg 1 2 1 0 1 2
sc 1 3 9
sc 3 0 4
ask q0 4 1""",
}

PLAIN = {
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
    "never-close": """cfg 2 2 1 0 2 4
sc 1 2 5
sc 2 3 4
sc 3 1 3
sc 1 3 2
sc 2 1 6
ask run 1""",
    "no-row": """cfg 2 2 1 0 1 6
sc 1 2 5
sc 2 3 4
sc 9 0 3
ask stuck 1 9""",
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
    "short-prompt": """cfg 2 4 1 0 2 8
sc 1 2 6
sc 2 3 5
sc 3 1 4
sc 1 3 3
sc 3 2 7
sc 2 1 2
sc 3 0 1
ask brief 1""",
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
}

PROGS = dict(WRONG)
PROGS.update(PLAIN)
ORDER = sorted(PROGS)


def prog(name):
    return PROGS[name].strip("\n").split("\n")
