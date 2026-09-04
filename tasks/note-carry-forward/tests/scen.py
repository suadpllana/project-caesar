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
    # one revision that retires two notes and raises a third, which pins the
    # order the three kinds of event come out in
    {"name": "retire-and-raise-in-one-revision",
     "revs": [["ln1", "ln1", "ln2", "ln3", "ln4", "ln1", "ln4", "ln0"],
              ["ln1", "ln2", "ln3", "ln4", "ln1", "ln4"],
              ["ln1", "ln4", "ln3", "ln4"],
              ["ln1", "ln4", "ln2"]],
     "opens": [[0, 0, 2], [2, 1, 3], [2, 2, 1]]},
    # a note that stays inside a change for two revisions running is asked
    # about once, not twice
    {"name": "raised-once-while-it-stays-inside",
     "revs": [["ln1", "ln1", "ln0", "ln0", "ln0", "ln1"],
              ["ln1", "ln1"],
              ["ln0", "ln0", "ln0", "ln1"],
              ["ln1", "ln1", "ln2", "ln0"],
              ["ln1", "ln0", "ln1", "ln0"]],
     "opens": [[0, 0, 3], [0, 1, 1], [1, 2, 0], [1, 3, 1]]},
    # and a note that leaves a change and is caught by a later one is asked
    # about again, so the rule is not once and never after
    {"name": "raised-again-after-it-leaves",
     "revs": [["a", "b", "c", "d", "e", "f", "g", "h", "i"],
              ["a", "X", "c", "Y", "e", "f", "g", "h", "i"],
              ["a", "X", "c", "Y", "e", "f", "g", "h", "i"],
              ["a", "P", "c", "Q", "e", "f", "g", "h", "i"]],
     "opens": [[0, 0, 2]]},
]

def generated(count, seed):
    """Short files edited hard, which is the shape that puts a note inside a
    change for more than one revision running."""
    rng = random.Random(seed * 7919 + 13)
    out = []
    for index in range(count):
        pool = ["ln%d" % i for i in range(rng.randrange(2, 5))]
        revs = [[rng.choice(pool) for _ in range(rng.randrange(5, 16))]]
        opens = []
        nid = 0
        for step in range(rng.randrange(4, 11)):
            for _ in range(rng.randrange(0, 4)):
                if revs[-1]:
                    opens.append([step, nid, rng.randrange(len(revs[-1]))])
                    nid += 1
            nxt = list(revs[-1])
            for _ in range(rng.randrange(3, 10)):
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
