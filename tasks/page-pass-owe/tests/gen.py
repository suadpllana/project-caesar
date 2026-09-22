"""Generates the list files the submission is graded on.

The seed is drawn inside the verifier after the agent's container is gone, so nothing
that was submitted has seen these programs. They are not sampled uniformly: each family
is shaped around one decision, because an unshaped population exercises a mechanism on a
percent of its programs and then says nothing about it.

  plain   nothing is ever too heavy and nothing is edited - the must-still-work side of
          the step-over fence, where a page has to be a plain run of the view
  ties    keys drawn from a span far smaller than the row count, with ids shuffled
          against insertion order, so place order is decided by the id and not by arrival
  heavy   a third of the rows heavier than half a page, so step-overs, ledger drains and
          heads heavier than a page all happen often
  over    weights clustered just above half a page, so two step-overs reach the allowance
          and the scan stops on it rather than on the page filling
  empty   rows heavier than a whole page, reached both by the scan and at the ledger front
  hold    a hold only a few rows wide with scrolls on separate tags, so one scroll's
          ledger decides whether another's scan may step over, and draining one unblocks
          the other
  edit    moves that carry rows across marks in both directions, plus drops, so ledger
          entries retire and come back at the end
  share   several scrolls on one tag with different limits, so the delivery memory has to
          be per scroll and the ledgers diverge
  churn   retags between two tags with scrolls on both, so rows leave a view and come
          back after having been handed out

  wide    a hundred and twenty thousand rows over eighty tags with forty scrolls asking
          for four thousand pages: the family that makes re-deriving the view on every
          page infeasible while leaving it exactly correct
  deep    forty thousand rows over two tags with eight scrolls, three thousand pages and
          fifteen thousand edits: the same boundary with the cost in the length of one
          view rather than in the number of them, and the family that makes re-sorting a
          view on every edit infeasible
"""

import random

SMALL = ("plain", "ties", "heavy", "over", "empty", "hold", "edit", "share", "churn")

SHAPE = {
    "plain": {"tags": (2, 3), "rows": (18, 34), "keys": 24, "scrolls": (1, 2),
              "n": (3, 6), "c": (28, 40), "hold": 400, "edits": 0.0, "mix": ()},
    "ties": {"tags": (2, 3), "rows": (20, 36), "keys": 5, "scrolls": (1, 2),
             "n": (3, 6), "c": (20, 30), "hold": 200, "edits": 0.25,
             "mix": ("move", "move", "add")},
    "heavy": {"tags": (2, 3), "rows": (18, 32), "keys": 20, "scrolls": (1, 2),
              "n": (4, 7), "c": (10, 14), "hold": 90, "edits": 0.2,
              "mix": ("move", "drop", "add")},
    "over": {"tags": (2, 3), "rows": (20, 34), "keys": 22, "scrolls": (1, 2),
             "n": (6, 9), "c": (12, 16), "hold": 120, "edits": 0.15,
             "mix": ("move", "add")},
    "empty": {"tags": (2, 2), "rows": (16, 28), "keys": 18, "scrolls": (1, 2),
              "n": (4, 6), "c": (8, 11), "hold": 150, "edits": 0.2,
              "mix": ("move", "add")},
    "hold": {"tags": (3, 4), "rows": (24, 40), "keys": 20, "scrolls": (3, 4),
             "n": (3, 5), "c": (10, 13), "hold": 0, "edits": 0.15,
             "mix": ("move", "add")},
    "edit": {"tags": (2, 3), "rows": (20, 34), "keys": 16, "scrolls": (2, 3),
             "n": (3, 5), "c": (12, 18), "hold": 140, "edits": 0.5,
             "mix": ("move", "move", "move", "drop", "add", "tag")},
    "share": {"tags": (1, 2), "rows": (20, 34), "keys": 18, "scrolls": (3, 4),
              "n": (2, 5), "c": (9, 16), "hold": 130, "edits": 0.25,
              "mix": ("move", "add", "drop")},
    "churn": {"tags": (2, 2), "rows": (18, 30), "keys": 16, "scrolls": (2, 3),
              "n": (3, 5), "c": (11, 16), "hold": 130, "edits": 0.45,
              "mix": ("tag", "tag", "tag", "move")},
}


def _weight(rng, fam, cap):
    """Weights are what decide whether a row fits, so each family draws its own."""
    if fam == "plain":
        return rng.randint(1, 4)
    if fam == "heavy":
        return rng.randint(1, 3) if rng.random() < 0.6 else rng.randint(cap // 2, cap + 3)
    if fam == "over":
        return rng.randint(1, 3) if rng.random() < 0.35 else rng.randint(cap // 2 + 1, cap - 1)
    if fam == "empty":
        return rng.randint(1, 3) if rng.random() < 0.6 else rng.randint(cap + 1, cap + 5)
    if fam == "hold":
        return rng.randint(1, 2) if rng.random() < 0.45 else rng.randint(cap // 2, cap)
    return rng.randint(1, max(2, cap // 2))


def _prog(rng, fam):
    sh = SHAPE[fam]
    ntags = rng.randint(*sh["tags"])
    nrows = rng.randint(*sh["rows"])
    nscrolls = rng.randint(*sh["scrolls"])
    caps = [rng.randint(*sh["c"]) for _ in range(nscrolls)]
    cap = max(caps)

    hold = sh["hold"] or rng.randint(cap, cap * 2)
    lines = ["cfg %d" % hold]

    ids = list(range(1, nrows + 1))
    rng.shuffle(ids)
    live = []
    for i in ids:
        k = rng.randint(1, sh["keys"])
        g = rng.randrange(ntags)
        w = _weight(rng, fam, cap)
        lines.append("row %d %d %d %d" % (i, k, g, w))
        live.append(i)

    for s in range(nscrolls):
        g = 0 if fam == "share" else s % ntags
        lines.append("open %d %d %d %d" % (s + 1, g, rng.randint(*sh["n"]), caps[s]))

    nid = nrows + 1
    steps = rng.randint(10, 18)
    for _ in range(steps):
        if live and sh["mix"] and rng.random() < sh["edits"]:
            what = rng.choice(sh["mix"])
            if what == "add":
                k = rng.randint(1, sh["keys"])
                lines.append("add %d %d %d %d" % (nid, k, rng.randrange(ntags),
                                                  _weight(rng, fam, cap)))
                live.append(nid)
                nid += 1
            elif what == "drop":
                i = live.pop(rng.randrange(len(live)))
                lines.append("drop %d" % i)
            elif what == "tag":
                lines.append("tag %d %d" % (rng.choice(live), rng.randrange(ntags)))
            else:
                lines.append("move %d %d" % (rng.choice(live),
                                             rng.randint(1, sh["keys"])))
        else:
            lines.append("next %d" % rng.randint(1, nscrolls))
    return lines


def _big(rng, nrows, ntags, nscrolls, keys, pages, edits, cap, rownum, hold):
    """One scale program. Rows first, then pages and edits interleaved."""
    lines = ["cfg %d" % hold]
    ids = list(range(1, nrows + 1))
    rng.shuffle(ids)
    live = []
    for i in ids:
        lines.append("row %d %d %d %d" % (i, rng.randint(1, keys), rng.randrange(ntags),
                                          rng.randint(1, cap - 2)
                                          if rng.random() < 0.8
                                          else rng.randint(cap // 2, cap + 2)))
        live.append(i)
    for s in range(nscrolls):
        lines.append("open %d %d %d %d" % (s + 1, s % ntags, rownum, cap))
    nid = nrows + 1
    plan = ["next"] * pages + ["edit"] * edits
    rng.shuffle(plan)
    for what in plan:
        if what == "next":
            lines.append("next %d" % rng.randint(1, nscrolls))
            continue
        pick = rng.random()
        if pick < 0.5:
            lines.append("move %d %d" % (rng.choice(live), rng.randint(1, keys)))
        elif pick < 0.7:
            lines.append("tag %d %d" % (rng.choice(live), rng.randrange(ntags)))
        elif pick < 0.85:
            lines.append("add %d %d %d %d" % (nid, rng.randint(1, keys),
                                              rng.randrange(ntags),
                                              rng.randint(1, cap - 2)))
            live.append(nid)
            nid += 1
        else:
            lines.append("drop %d" % live.pop(rng.randrange(len(live))))
    return lines


def wide(rng):
    return _big(rng, 120000, 80, 40, 40000, 4000, 4000, 14, 20, 20000)


def deep(rng):
    return _big(rng, 40000, 2, 8, 16000, 3000, 15000, 14, 20, 20000)


def programs(seed, per):
    """(family, name, lines) for every generated program, in a fixed order."""
    out = []
    for fam in SMALL:
        for j in range(per):
            rng = random.Random("%s/%s/%d" % (seed, fam, j))
            out.append((fam, "%s-%02d" % (fam, j), _prog(rng, fam)))
    for j in range(3):
        out.append(("wide", "wide-%d" % j, wide(random.Random("%s/wide/%d" % (seed, j)))))
    for j in range(3):
        out.append(("deep", "deep-%d" % j, deep(random.Random("%s/deep/%d" % (seed, j)))))
    return out
