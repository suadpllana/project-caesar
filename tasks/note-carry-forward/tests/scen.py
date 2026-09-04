"""The graded streams.

A stream is a list of revisions and the things reviewers did between them.
FIXED are written out by hand, one per rule and one per corner where two of
them meet. The generated block is drawn from a seed the run is given, so the
streams a submission is graded on are not the streams it was written against.

An event is [step, kind, payload]: ("open", [id, [lines]]) opens a thread on
those lines of revision `step`, ("reply", id) and ("resolve", id) are what the
author and the reviewer do to one.
"""

import random


def _open(step, nid, lo, hi):
    return [step, "open", [nid, list(range(lo, hi + 1))]]


FIXED = [
    # a span follows its lines through an untouched revision
    {"name": "carry-plain",
     "revs": [["a", "b", "c", "d", "e", "f"], ["a", "b", "c", "d", "e", "f", "g"]],
     "events": [_open(0, 0, 1, 2)]},
    # a span that loses some lines keeps the rest
    {"name": "span-shrinks",
     "revs": [["a", "b", "c", "d", "e"], ["a", "b", "d", "e"]],
     "events": [_open(0, 0, 1, 3)]},
    # a span that loses all of them leaves the thread outdated, and it stays
    # on the board with the empty span it ended on
    {"name": "outdated-stays-listed",
     "revs": [["a", "b", "c", "d"], ["a", "X", "Y", "d"], ["a", "X", "Y", "d"]],
     "events": [_open(0, 0, 1, 2)]},
    # the change reaching one line of a span is enough. Two edits close enough
    # together to be one change take the kept lines between them with them, and
    # the span keeps two lines beyond it that the change never reaches
    {"name": "raise-on-one-line-of-the-span",
     "revs": [["a", "b", "c", "d", "e", "f", "g", "h", "i"],
              ["X", "b", "c", "Y", "e", "f", "g", "h", "i"]],
     "events": [_open(0, 0, 2, 5)]},
    # and a change that reaches none of it is not a raise
    {"name": "no-raise-when-the-change-misses",
     "revs": [["a", "b", "c", "d", "e", "f", "g", "h"],
              ["a", "b", "c", "d", "e", "f", "X", "h"]],
     "events": [_open(0, 0, 1, 2)]},
    # raised once while it stays caught
    {"name": "raised-once-while-it-stays-caught",
     "revs": [["a", "b", "c", "d", "e"], ["a", "X", "c", "Y", "e"],
              ["a", "P", "c", "Q", "e"], ["a", "P", "c", "Q", "e"]],
     "events": [_open(0, 0, 2, 2)]},
    # and again once a revision has let it go
    {"name": "raised-again-after-it-is-let-go",
     "revs": [["a", "b", "c", "d", "e"], ["a", "X", "c", "Y", "e"],
              ["a", "X", "c", "Y", "e"], ["a", "P", "c", "Q", "e"]],
     "events": [_open(0, 0, 2, 2)]},
    # an answered thread that is caught again goes back to open
    {"name": "answered-reopens-when-caught",
     "revs": [["a", "b", "c", "d", "e"], ["a", "b", "c", "d", "e"],
              ["a", "X", "c", "Y", "e"]],
     "events": [_open(0, 0, 2, 2), [1, "reply", 0]]},
    # a resolved thread is never raised and never reopened
    {"name": "resolved-is-not-raised",
     "revs": [["a", "b", "c", "d", "e"], ["a", "b", "c", "d", "e"],
              ["a", "X", "c", "Y", "e"]],
     "events": [_open(0, 0, 2, 2), [1, "resolve", 0]]},
    # two spans that share a line become one, older takes the union
    {"name": "absorb-on-overlap",
     "revs": [["a", "b", "c", "d", "e"], ["a", "b", "c", "d", "e"]],
     "events": [_open(0, 0, 1, 2), _open(0, 1, 2, 3)]},
    # spans that share nothing stay apart
    {"name": "no-absorb-without-overlap",
     "revs": [["a", "b", "c", "d", "e"], ["a", "b", "c", "d", "e"]],
     "events": [_open(0, 0, 0, 1), _open(0, 1, 3, 4)]},
    # the union reaches a third thread neither half reached alone
    {"name": "absorb-chains-through-the-union",
     "revs": [["a", "b", "c", "d", "e", "f"], ["a", "b", "c", "d", "e", "f"]],
     "events": [_open(0, 0, 0, 1), _open(0, 2, 3, 4), _open(0, 1, 1, 3)]},
    # carrying squeezes two spans together that were opened apart
    {"name": "carry-squeezes-spans-together",
     "revs": [["a", "b", "c", "d", "e", "f", "g"], ["a", "b", "f", "g"]],
     "events": [_open(0, 0, 0, 1), _open(0, 1, 1, 5)]},
    # an open thread drags the merged thread open
    {"name": "open-drags-the-merge-open",
     "revs": [["a", "b", "c", "d"], ["a", "b", "c", "d"]],
     "events": [_open(0, 0, 1, 2), [0, "reply", 0], _open(1, 1, 2, 3)]},
    # nothing at all
    {"name": "no-threads", "revs": [["a"], ["b"]], "events": []},
    # which copy of a repeated line survived is the script's own business, and
    # a mapping rebuilt from an ordinary walk picks a different one
    {"name": "tie-break-picks-the-surviving-copy",
     "revs": [["ln0", "ln0", "ln1", "ln1", "ln0", "ln0"], ["ln1", "ln1"],
              ["ln0"], ["ln0"], ["ln0", "ln0"]],
     "events": [[0, "open", [0, [4, 5]]], [1, "reply", 0], [2, "open", [1, [0]]],
                [2, "open", [2, [0]]], [3, "open", [3, [0]]], [3, "open", [4, [0]]]]},
    # a resolved thread is still reached or let go by what a revision does to
    # its lines. It is not raised while it is resolved, but the verdict is what
    # a later raise is measured against once a merge has dragged it open again
    {"name": "resolved-still-tracks-being-reached",
     "revs": [["ln0", "ln2"], ["ln0", "ln0"], ["ln0", "ln1"]],
     "events": [_open(0, 0, 0, 1), [0, "resolve", 0], _open(1, 1, 1, 1)]},
    # the survivor of a merge holds the union, so a change that reached either
    # half has reached what it now holds, and that is not a fresh raise
    {"name": "merged-thread-inherits-being-reached",
     "revs": [["ln0", "ln2", "ln2"], ["ln0", "ln2", "ln0"], ["ln0", "ln0", "ln0"]],
     "events": [_open(0, 0, 0, 1), _open(0, 1, 2, 2), _open(1, 2, 0, 1)]},
    # replies and resolutions land before the merging, so the resolve is what
    # the open half then drags back open
    {"name": "talk-lands-before-the-merge",
     "revs": [["ln0"], ["ln0"]],
     "events": [_open(0, 0, 0, 0), _open(0, 1, 0, 0), [0, "resolve", 0]]},
    # two absorbs in one revision whose absorbed order and owner order
    # disagree, so the log says which of the two the sequence follows
    {"name": "absorbs-ordered-by-the-one-absorbed",
     "revs": [["ln0", "ln1", "ln2", "ln3", "ln4", "ln5", "ln6", "ln7"],
              ["ln0", "ln1", "ln2", "ln3", "ln4", "ln5", "ln6", "ln7"]],
     "events": [_open(0, 0, 0, 1), _open(0, 1, 4, 5),
                _open(0, 2, 5, 6), _open(0, 3, 1, 2)]},
    # a reply only moves an open thread, so one aimed at a settled thread
    # leaves it settled
    {"name": "reply-to-a-resolved-thread-does-nothing",
     "revs": [["ln0"], ["ln0"]],
     "events": [_open(0, 0, 0, 0), [0, "resolve", 0], [1, "reply", 0]]},
    # and one aimed at a thread that has been absorbed is aimed at nothing,
    # rather than at whoever holds its span now
    {"name": "talk-to-an-absorbed-thread-does-nothing",
     "revs": [["ln2"], ["ln2"], ["ln2"]],
     "events": [_open(1, 0, 0, 0), _open(1, 1, 0, 0), [2, "resolve", 1]]},
    # the change reaching part of a span is enough, over a stream long enough
    # that requiring the whole span comes apart
    {"name": "part-of-the-span-is-enough",
     "revs": [["ln3", "ln3", "ln3", "ln3", "ln1", "ln2"],
              ["ln3", "ln3", "ln0", "ln3", "ln2"], ["ln3", "ln0", "ln3", "ln2"],
              ["ln3", "ln0", "ln0", "ln3"], ["ln0", "ln0"], ["ln2"]],
     "events": [[1, "open", [0, [1, 2, 3]]], [2, "open", [1, [1]]],
                [3, "resolve", 0]]},
]


def wide(count, seed):
    """The streams that hold a few hundred threads at once.

    A file of a few hundred lines with a thread on every fourth one, so most of
    them are still on the board at the head instead of merging away. Which
    lines a change reaches is a fact about the pair of revisions rather than
    about the thread being asked, so these settle in about a second a stream
    for a board that works it out once a revision, and cost the whole edit
    script per thread for one that works it out again for each of them."""
    rng = random.Random(seed * 6271 + 41)
    out = []
    for index in range(count):
        size = rng.randrange(260, 341)
        pool = ["ln%d" % i for i in range(size // 4)]
        revs = [[rng.choice(pool) for _ in range(size)]]
        events = []
        nid = 0
        for lo in range(0, size, 4):
            events.append([0, "open", [nid, [lo]]])
            nid += 1
        seen = list(range(nid))
        for step in range(rng.randrange(5, 8)):
            if step:
                for _ in range(rng.randrange(0, 4)):
                    lo = rng.randrange(len(revs[-1]))
                    hi = min(len(revs[-1]) - 1, lo + rng.randrange(0, 3))
                    events.append([step, "open", [nid, list(range(lo, hi + 1))]])
                    seen.append(nid)
                    nid += 1
            for _ in range(rng.randrange(0, 4)):
                events.append([step, rng.choice(["reply", "resolve"]),
                               rng.choice(seen)])
            nxt = list(revs[-1])
            for _ in range(rng.randrange(2, 6)):
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
        out.append({"name": "wide%04d" % index, "revs": revs, "events": events})
    return out


def generated(count, seed):
    """Short files edited hard, which is the shape that leaves a span caught
    in a change for more than one revision running and squeezes spans that
    were opened apart into one another."""
    rng = random.Random(seed * 7919 + 13)
    out = []
    for index in range(count):
        pool = ["ln%d" % i for i in range(rng.randrange(2, 5))]
        revs = [[rng.choice(pool) for _ in range(rng.randrange(6, 16))]]
        events = []
        nid = 0
        seen = []
        for step in range(rng.randrange(4, 11)):
            for _ in range(rng.randrange(0, 3)):
                if revs[-1]:
                    lo = rng.randrange(len(revs[-1]))
                    hi = min(len(revs[-1]) - 1, lo + rng.randrange(0, 3))
                    events.append([step, "open", [nid, list(range(lo, hi + 1))]])
                    seen.append(nid)
                    nid += 1
            if seen and rng.random() < 0.45:
                events.append([step, rng.choice(["reply", "resolve"]),
                               rng.choice(seen)])
            nxt = list(revs[-1])
            for _ in range(rng.randrange(2, 8)):
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
        out.append({"name": "gen%04d" % index, "revs": revs, "events": events})
    return out
