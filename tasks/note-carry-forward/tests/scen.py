"""The graded streams.

FIXED are written out by hand, one per rule the board has to get right, plus
the corners where two of them meet. The generated block is drawn from a seed
the run is given, so the streams a submission is graded on are not the streams
it was written against.
"""

import random

FIXED = [
    # a note follows its line through an untouched revision
    {"name": "carry-plain",
     "revs": [["a", "b", "c", "d", "e", "f", "g"],
              ["a", "b", "c", "d", "e", "f", "g", "h"]],
     "opens": [[0, 0, 2]]},
    # the line under the note goes, so the note goes
    {"name": "retire-dropped",
     "revs": [["a", "b", "c", "d", "e"], ["a", "b", "d", "e"]],
     "opens": [[0, 0, 2]]},
    # a kept line that sits between two runs of one change is inside it
    {"name": "raise-kept-inside-change",
     "revs": [["a", "b", "c", "d", "e"], ["a", "X", "c", "Y", "e"]],
     "opens": [[0, 0, 2]]},
    # the same kept line, with the two changes far enough apart to be two
    {"name": "raise-not-when-changes-are-apart",
     "revs": [["a", "b", "c", "d", "e", "f", "g", "h"],
              ["a", "X", "c", "d", "e", "Y", "g", "h"]],
     "opens": [[0, 0, 3]]},
    # two notes come to rest on one line: the older takes it
    {"name": "absorb-older-wins",
     "revs": [["a", "b", "c", "d"], ["a", "b", "c", "d"]],
     "opens": [[0, 0, 1], [0, 1, 1]]},
    # opened at the head, nothing has landed since
    {"name": "open-at-head",
     "revs": [["a", "b", "c"], ["a", "b", "c", "d"]],
     "opens": [[1, 0, 3]]},
    # a note opened after the first revision still replays from there
    {"name": "open-midstream",
     "revs": [["a", "b", "a", "b"], ["a", "b", "a"], ["b", "a"]],
     "opens": [[1, 0, 2]]},
    # both sides empty
    {"name": "empty-revision",
     "revs": [["a", "b"], [], ["c"]],
     "opens": [[0, 0, 0]]},
    # the note sits on the last line
    {"name": "last-line",
     "revs": [["a", "b", "c"], ["a", "b", "c", "d", "e"]],
     "opens": [[0, 0, 2]]},
    # no notes at all
    {"name": "no-notes", "revs": [["a"], ["b"]], "opens": []},
    # which copy of a repeated line survived is the script's own business, and
    # an ordinary longest-common-subsequence backtrace picks a different one
    {"name": "tie-break-picks-the-survivor",
     "revs": [["ln1", "ln0", "ln1", "ln1", "ln0", "ln1", "ln1", "ln1"],
              ["ln1", "ln1", "ln0", "ln1", "ln1"],
              ["ln1", "ln1", "ln0", "ln1", "ln1"],
              ["ln1", "ln0", "ln1"]],
     "opens": [[2, 0, 1]]},
    # the standard library's matcher settles the same pair differently again
    {"name": "matcher-keeps-another-copy",
     "revs": [["ln3", "ln5", "ln4", "ln5", "ln4", "ln1", "ln0", "ln0"],
              ["ln3", "ln5", "ln4", "ln5", "ln4", "ln0"],
              ["ln3", "ln5", "ln5", "ln4", "ln0"],
              ["ln3", "ln5", "ln0"]],
     "opens": [[0, 0, 7]]},
    # a line the change replaced carries its note to the replacement
    {"name": "replace-carries-the-note",
     "revs": [["a", "b", "c", "d", "e"], ["a", "b", "X", "d", "e"]],
     "opens": [[0, 0, 2]]},
    # the drop and the add stand two kept lines apart, which is one change,
    # so they pair
    {"name": "replace-across-a-gap",
     "revs": [["p", "q", "r", "s", "t", "u", "v"],
              ["p", "r", "s", "Z", "t", "u", "v"]],
     "opens": [[0, 0, 1]]},
    # three kept lines apart is two changes, so the drop has no partner
    {"name": "too-far-to-pair",
     "revs": [["p", "q", "r", "s", "t", "u", "v", "w"],
              ["p", "r", "s", "t", "Z", "u", "v", "w"]],
     "opens": [[0, 0, 1]]},
    # two gone and one come: the first pairs, the second is really gone
    {"name": "more-gone-than-came",
     "revs": [["a", "b", "c", "d", "e", "f"], ["a", "X", "d", "e", "f"]],
     "opens": [[0, 0, 1], [0, 1, 2]]},
    # two gone and two come, which pins which of them pairs with which
    {"name": "pair-in-order",
     "revs": [["a", "b", "c", "d", "e", "f"], ["a", "X", "Y", "d", "e", "f"]],
     "opens": [[0, 0, 1], [0, 1, 2]]},
    # a replaced line is carried again by the revision after it
    {"name": "replace-then-carry",
     "revs": [["a", "b", "c", "d", "e"], ["a", "b", "X", "d", "e"],
              ["a", "b", "X", "d", "e", "f"]],
     "opens": [[0, 0, 2]]},
    # one revision that retires two notes and raises a third, which pins the
    # order the three kinds of event come out in
    {"name": "retire-and-raise-in-one-revision",
     "revs": [["ln1", "ln1", "ln2", "ln3", "ln4", "ln1", "ln4", "ln0"],
              ["ln1", "ln2", "ln3", "ln4", "ln1", "ln4"],
              ["ln1", "ln4", "ln3", "ln4"],
              ["ln1", "ln4", "ln2"]],
     "opens": [[0, 0, 2], [2, 1, 3], [2, 2, 1]]},
]

_POOLS = [2, 2, 3, 3, 4, 5, 6]


def generated(count, seed):
    rng = random.Random(seed * 7919 + 13)
    out = []
    for index in range(count):
        pool = ["ln%d" % i for i in range(rng.choice(_POOLS))]
        revs = [[rng.choice(pool) for _ in range(rng.randrange(6, 26))]]
        opens = []
        nid = 0
        for step in range(rng.randrange(3, 9)):
            for _ in range(rng.randrange(0, 3)):
                if revs[-1]:
                    opens.append([step, nid, rng.randrange(len(revs[-1]))])
                    nid += 1
            nxt = list(revs[-1])
            for _ in range(rng.randrange(1, 5)):
                if not nxt:
                    break
                p = rng.randrange(len(nxt))
                z = rng.randrange(3)
                if z == 0 and len(nxt) > 1:
                    del nxt[p]
                elif z == 1:
                    nxt.insert(p, rng.choice(pool))
                else:
                    nxt[p] = rng.choice(pool)
            revs.append(nxt)
        out.append({"name": "gen%04d" % index, "revs": revs, "opens": opens})
    return out
