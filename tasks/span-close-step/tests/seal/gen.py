"""Nonce run scripts, generated after the agent has finished.

Six shaped families rather than one uniform population, because the decisions this
task grades do not show up in proportion to their importance. A stream of short
documents and a generous batch settles everything inside the step that consumed
it, and every wrong reading of settlement, of the divisor and of the requeue rule
then agrees with the contract. Each family below concentrates one interaction:

  plain   nothing straddles a step and nothing is requeued - the side that must
          still work, so an over-cautious reading cannot pass by refusing to act
  span    documents long enough to be consumed over two or three steps
  loop    a low requeue threshold and repeated names, so chains form and the
          allowance has to be counted per occurrence
  hold    masked documents and documents wider than a whole batch, so steps that
          consume tokens and settle nothing occur
  shard   the accumulation and worker layout changes mid-run, with and without a
          change of global batch
  back    checkpoints taken and restored across steps that settle spanning work
  order   several short documents settling in one step under a worker layout whose
          micro-batch order is not the stream order

Every candidate is simulated by the sealed model before it is kept, and rejected
unless the two decisions taken on unrounded floats - whether the step clips, and
whether a document is requeued - stand clear of their boundaries, and no printed
number sits on a rounding edge.
"""
import random

import model

NAMES = ("ab", "cd", "ef", "gh", "ij", "kl")
FAMILIES = (("plain", 55), ("span", 65), ("loop", 65), ("hold", 45),
            ("shard", 45), ("back", 45), ("order", 65))
TIGHT = 1e-6
NEAR = 1e-3


def _pars(rnd):
    return " ".join("%.2f" % (rnd.randrange(-8, 9) / 8.0) for _ in range(4))


MAXLEN = 64


def _doc(rnd, name, lo, hi, masked=False):
    n = min(rnd.randint(lo, hi), MAXLEN)
    if masked:
        return "mdoc %s %d" % (name, n)
    return "doc %s %d %d" % (name, n, rnd.randrange(n))


def _head(rnd, fam):
    lim = rnd.randint(4, 9)
    if fam == "hold":
        grp, wrk, seq = 1, rnd.randint(1, 2), 1
    elif fam == "order":
        lim = rnd.randint(4, 6)
        grp, wrk, seq = 1, rnd.randint(2, 3), 2
    else:
        grp, wrk, seq = rnd.randint(1, 2), rnd.randint(1, 3), rnd.randint(1, 2)
    thr = {"loop": 0.7, "order": 0.7, "plain": 9.0}.get(fam, 1.2)
    cap = 2 if fam in ("loop", "order") else rnd.randint(1, 2)
    out = ["lim %d" % lim,
           "bat %d %d %d" % (grp, wrk, seq),
           "opt %.2f %d %d %.2f %.2f" % (rnd.choice((0.1, 0.2, 0.3)),
                                         rnd.randint(1, 3), rnd.randint(2, 4),
                                         rnd.choice((0.0, 0.4, 0.6)),
                                         rnd.choice((0.8, 1.2, 2.0))),
           "ema %.2f" % rnd.choice((0.7, 0.9)),
           "rep %.2f %d" % (thr, cap),
           "par " + _pars(rnd)]
    return out, lim, grp * wrk * seq


def _body(rnd, fam, lim, batch):
    span = lim * batch
    lines = []
    if fam == "plain":
        for _ in range(rnd.randint(5, 8)):
            lines.append(_doc(rnd, rnd.choice(NAMES), 2, max(3, span // 3)))
    elif fam == "span":
        for _ in range(rnd.randint(4, 7)):
            lines.append(_doc(rnd, rnd.choice(NAMES), max(2, span - 2), span + 8))
    elif fam == "loop":
        for _ in range(rnd.randint(5, 8)):
            lines.append(_doc(rnd, rnd.choice(NAMES[:3]), 2, span + 3,
                              masked=rnd.random() < 0.15))
    elif fam == "hold":
        for _ in range(rnd.randint(5, 9)):
            if rnd.random() < 0.45:
                lines.append(_doc(rnd, rnd.choice(NAMES), 2, span, masked=True))
            else:
                lines.append(_doc(rnd, rnd.choice(NAMES), span, span + 12))
    elif fam == "order":
        for _ in range(rnd.randint(8, 12)):
            lines.append(_doc(rnd, rnd.choice(NAMES[:3]), 2, max(3, lim - 1),
                              masked=rnd.random() < 0.15))
    elif fam == "shard":
        for _ in range(rnd.randint(5, 8)):
            lines.append(_doc(rnd, rnd.choice(NAMES), 2, span + 4))
    else:
        for _ in range(rnd.randint(5, 8)):
            lines.append(_doc(rnd, rnd.choice(NAMES), max(2, span - 3), span + 6,
                              masked=rnd.random() < 0.15))

    events = []
    steps = rnd.randint(5, 9)
    for j in range(steps):
        events.append("step")
        if fam == "shard" and j in (1, 3):
            events.append("resh %d %d %d" % (rnd.randint(1, 2), rnd.randint(1, 3),
                                             rnd.randint(1, 2)))
        if fam == "back" and j == 1:
            events.append("save")
        if fam == "back" and j == 2:
            events.append("resh %d %d %d" % (rnd.randint(1, 2), rnd.randint(1, 3),
                                             rnd.randint(1, 2)))
        if fam == "back" and j == 4:
            events.append("load")
        if rnd.random() < 0.2:
            events.append(_doc(rnd, rnd.choice(NAMES), 2, span + 2,
                               masked=rnd.random() < 0.2))
        if rnd.random() < 0.2:
            events.append("emit")
    events.append("emit")
    return lines + events


def one(rnd, fam):
    head, lim, batch = _head(rnd, fam)
    return head + _body(rnd, fam, lim, batch)


def programs(seed, per):
    """Return [(family, name, lines)] - deterministic in `seed` and `per`."""
    out = []
    for fam, share in FAMILIES:
        want = max(1, (share * per) // 55)
        made = 0
        tries = 0
        rnd = random.Random("%s/%s" % (seed, fam))
        while made < want and tries < want * 60:
            tries += 1
            lines = one(rnd, fam)
            got, tight, near = model.margins(lines)
            if tight < TIGHT or near < NEAR:
                continue
            if not any(ln.startswith("up ") for ln in got):
                continue
            if sum(1 for ln in lines if ln.startswith(("doc ", "mdoc "))) > 20:
                continue
            out.append((fam, "%s-%03d" % (fam, made), lines))
            made += 1
    return out
