"""The nonce population: programs generated from a seed drawn after the agent is gone.

Eight families, each shaped at one part of the contract rather than sampled uniformly and hoped
over. A population that is not deliberately bent at a mechanism does not exercise it: the plain
family alone moves none of the resume readings, because it never resumes.

  plain   one rank count from end to end, no preemption. The everyday side of every fence:
          the window chunking, the tail drop, the cadence and the epoch roll with nothing
          unusual happening around them.
  stall   enough non-finite ids that skips outnumber applied steps. Separates the position
          from the applied count, walks the scale down onto its floor, and pushes the
          checkpoint cadence out of step with the windows.
  rewind  preemptions on an unchanged rank count. What the checkpoint has to hold, and that
          a restore goes back to a position rather than to the top of the epoch.
  resize  preemption followed by a return on a different rank count, which is the case the
          order is redrawn for and the one a per-rank cursor cannot express.
  edge    rows chosen just above and just below a whole window, resizes that leave an epoch
          with no room for a step, and datasets smaller than one window.
  swing   many legs: a return without a preemption, a preemption with no checkpoint behind
          it, and rank counts that go up and down inside one epoch.
  wide    a dataset of sixty million rows. Every answer is the same as it would be at any
          other size; building the epoch order to get it is what the limit forbids.
  deep    four hundred legs across one run, where rebuilding the state by replaying the run
          on each return costs the run length once per leg.
"""

import random

FAMILIES = (
    ("plain", False),
    ("stall", False),
    ("rewind", False),
    ("resize", False),
    ("edge", False),
    ("swing", False),
    ("wide", True),
    ("deep", True),
)


def _head(rng, rows, rank, micro, accum, epochs, ckpt, grow, scale, seed):
    return ["rows %d" % rows, "seed %d" % seed, "rank %d" % rank,
            "micro %d" % micro, "accum %d" % accum, "ckpt %d" % ckpt,
            "grow %d" % grow, "scale %d" % scale, "epochs %d" % epochs]


def _nf(rng, rows, many):
    n = rng.randint(many[0], many[1])
    return ["nf %d" % i for i in rng.sample(range(rows), min(n, rows))]


def _plain(rng, seed):
    rank = rng.randint(1, 4)
    micro = rng.randint(1, 3)
    accum = rng.randint(1, 4)
    wide = rank * micro * accum
    rows = wide * rng.randint(2, 7) + rng.randint(0, wide - 1 if wide > 1 else 0)
    epochs = rng.randint(1, 3)
    head = _head(rng, rows, rank, micro, accum, epochs,
                 rng.randint(1, 3), rng.randint(1, 4), rng.randint(0, 3), seed)
    return head + _nf(rng, rows, (0, 2)) + ["run %d" % rng.randint(4, 16)]


def _stall(rng, seed):
    rank = rng.randint(1, 3)
    micro = rng.randint(1, 2)
    accum = rng.randint(1, 3)
    wide = rank * micro * accum
    rows = wide * rng.randint(3, 8)
    head = _head(rng, rows, rank, micro, accum, rng.randint(1, 2),
                 rng.randint(1, 2), rng.randint(1, 3), rng.randint(0, 2), seed)
    return head + _nf(rng, rows, (rows // 3, rows // 2)) + ["run %d" % rng.randint(6, 18)]


def _legs(rng, kinds, ranks, rounds, budget):
    out = []
    for _ in range(rounds):
        out.append("run %d" % rng.randint(*budget))
        kind = rng.choice(kinds)
        if kind in ("kill", "both"):
            out.append("kill")
        if kind in ("back", "both"):
            out.append("back %d" % rng.choice(ranks))
    out.append("run %d" % rng.randint(*budget))
    return out


def _rewind(rng, seed):
    rank = rng.randint(1, 3)
    micro = rng.randint(1, 3)
    accum = rng.randint(1, 3)
    wide = rank * micro * accum
    rows = wide * rng.randint(4, 9) + rng.randint(0, wide - 1 if wide > 1 else 0)
    head = _head(rng, rows, rank, micro, accum, rng.randint(1, 3),
                 rng.randint(1, 3), rng.randint(1, 3), rng.randint(0, 3), seed)
    return head + _nf(rng, rows, (0, 3)) + _legs(
        rng, ["kill"], [rank], rng.randint(1, 3), (2, 7))


def _resize(rng, seed):
    rank = rng.randint(1, 4)
    micro = rng.randint(1, 3)
    accum = rng.randint(1, 3)
    rows = rank * micro * accum * rng.randint(4, 10)
    head = _head(rng, rows, rank, micro, accum, rng.randint(1, 3),
                 rng.randint(1, 3), rng.randint(1, 3), rng.randint(0, 3), seed)
    return head + _nf(rng, rows, (1, 4)) + _legs(
        rng, ["both"], [1, 2, 3, 4, 6], rng.randint(1, 3), (2, 8))


def _edge(rng, seed):
    rank = rng.randint(1, 3)
    micro = rng.randint(1, 2)
    accum = rng.randint(1, 3)
    wide = rank * micro * accum
    slack = rng.choice([-1, 0, 1, 2])
    rows = max(1, wide * rng.randint(1, 3) + slack)
    head = _head(rng, rows, rank, micro, accum, rng.randint(2, 4),
                 rng.randint(1, 2), rng.randint(1, 3), rng.randint(0, 2), seed)
    return head + _nf(rng, rows, (0, 2)) + _legs(
        rng, ["both", "back"], [2, 3, 4, 5, 8], rng.randint(1, 3), (1, 5))


def _swing(rng, seed):
    rank = rng.randint(1, 3)
    micro = rng.randint(1, 2)
    accum = rng.randint(1, 3)
    rows = rank * micro * accum * rng.randint(3, 8) + rng.randint(0, 3)
    head = _head(rng, rows, rank, micro, accum, rng.randint(1, 3),
                 rng.randint(1, 4), rng.randint(1, 3), rng.randint(0, 2), seed)
    return head + _nf(rng, rows, (0, 3)) + _legs(
        rng, ["kill", "back", "both"], [1, 2, 3, 4], rng.randint(3, 6), (0, 5))


def _wide(rng, seed):
    rank = rng.choice([2, 4])
    micro = rng.choice([4, 8])
    accum = rng.choice([2, 4])
    rows = 60000000 + rng.randint(0, 999)
    head = _head(rng, rows, rank, micro, accum, 1,
                 rng.randint(2, 4), rng.randint(2, 4), rng.randint(0, 2), seed)
    nf = ["nf %d" % rng.randrange(rows) for _ in range(3)]
    legs = ["run 300", "kill", "back %d" % rng.choice([1, 3, 8]), "run 300"]
    return head + nf + legs


def _deep(rng, seed):
    rank = rng.randint(2, 4)
    micro = 2
    accum = 2
    rows = rank * micro * accum * 900
    head = _head(rng, rows, rank, micro, accum, 30, 2, 3, rng.randint(0, 2), seed)
    nf = ["nf %d" % rng.randrange(rows) for _ in range(40)]
    legs = []
    for i in range(400):
        legs.append("run 25")
        legs.append("kill" if i % 3 else "back %d" % (1 + (i % 4)))
    legs.append("run 25")
    return head + nf + legs


MAKE = {"plain": _plain, "stall": _stall, "rewind": _rewind, "resize": _resize,
        "edge": _edge, "swing": _swing, "wide": _wide, "deep": _deep}


def programs(nonce, per, big=3):
    """Every generated program, as (family, name, lines). Deterministic in `nonce`."""
    out = []
    for fam, heavy in FAMILIES:
        count = big if heavy else per
        for i in range(count):
            rng = random.Random("%s/%s/%d" % (nonce, fam, i))
            lines = MAKE[fam](rng, rng.randrange(1, 1 << 20))
            out.append((fam, "%s-%03d" % (fam, i), lines))
    return out


def one(fam, nonce):
    """A single program of one family, for authoring reports that do not want the whole set."""
    rng = random.Random(nonce)
    return MAKE[fam](rng, rng.randrange(1, 1 << 20))
