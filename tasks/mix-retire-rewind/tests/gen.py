"""Plans generated inside the verifier, from a seed drawn after the agent's container is gone.

Eleven families, each shaped around one thing a wrong feeder gets wrong rather than sampled
from the whole space, because an unshaped population does not reach the mechanism:

  plain    every sample inside the cap, no allowance, no resume - the ordinary side of the
           fence, which an overcautious feeder fails
  hot      two samples in five over the cap, so a slot is filled after several are passed over
  heavy    all but one or two over the cap, so a source's epoch turns over almost every time
           it delivers and its delivered count is nearly its epoch count
  wrap     sources of two to five samples with a one-slot step, so an epoch boundary lands on
           almost every printed line
  retire   one allowance spent inside the plan, with lines printed on both sides of it
  cascade  two or three allowances, so the first retirement moves where the second one lands
  resume   the feeder run ahead of the trainer, then saved and loaded under a new geometry
  chain    a load of a run that was itself loaded, saved again in between
  edge     one-slot steps around a retirement, so a rewind lands on the retirement slot itself
           and a save's state sits on the far side of it from the load's
  wide     the scale family: 780000 steps of 256 slots over four sources
  deep     the same with a source that retires two thirds of the way in
"""
import random

FAMILIES = (
    ("plain", False),
    ("hot", False),
    ("heavy", False),
    ("wrap", False),
    ("retire", False),
    ("cascade", False),
    ("resume", False),
    ("chain", False),
    ("edge", False),
    ("wide", True),
    ("deep", True),
)

BIG = 3
NAMES = ("a", "b", "c", "d", "e", "f")


def corpus(rng, n, cap, over):
    out = [rng.randint(24, cap) for _ in range(n)]
    if over:
        for i in rng.sample(range(n), min(over, n)):
            out[i] = cap + rng.randint(1, 900)
    # A sample exactly at the cap is kept, and one sample past it is not; a population that
    # never lands on the boundary leaves that reading to chance.
    if rng.random() < 0.4:
        out[rng.randrange(n)] = cap
    if rng.random() < 0.3:
        out[rng.randrange(n)] = cap + 1
    if not any(v <= cap for v in out):
        out[rng.randrange(n)] = rng.randint(24, cap)
    return out


def fits(vals, cap):
    return sum(1 for v in vals if v <= cap)


def tally(pat, j, wide):
    whole, rest = divmod(wide, len(pat))
    return whole * pat.count(j) + pat[:rest].count(j)


def mixture(rng, k, span):
    pat = [rng.randrange(k) for _ in range(span)]
    for j in range(k):
        if j not in pat:
            pat[rng.randrange(span)] = j
    return pat


def geometry(rng, tiny=False):
    if tiny:
        return 1, 1, rng.choice([1, 1, 2])
    return rng.choice([1, 2, 4]), rng.choice([1, 2, 3]), rng.choice([1, 2, 4])


def head(rng, kinds, cap, seed):
    """The config lines: a seed, a cap, one src line per source, and the mix."""
    k = len(kinds)
    lines = ["seed %d" % seed, "cap %d" % cap]
    fit = []
    for j, (n, over, hold) in enumerate(kinds):
        vals = corpus(rng, n, cap, over)
        fit.append(fits(vals, cap))
        lines.append("src %s %d %s" % (NAMES[j], hold, ",".join(str(v) for v in vals)))
    pat = mixture(rng, k, rng.randint(max(2, k), k + 3))
    lines.append("mix " + " ".join(NAMES[j] for j in pat))
    return lines, pat, fit


def limits(rng, pat, fit, kinds, slots, how_many):
    """Pick allowances that retire `how_many` sources inside `slots` slots."""
    hold = [0] * len(kinds)
    live = sorted(set(pat))
    rng.shuffle(live)
    for j in live[:how_many]:
        at = rng.randint(max(2, slots // 4), max(3, slots))
        hold[j] = max(1, tally(pat, j, at) // max(1, fit[j]))
    if all(hold[j] for j in set(pat)):
        hold[sorted(set(pat))[-1]] = 0
    return hold


def restate(lines, hold):
    """Put the chosen allowances into the src lines."""
    out = []
    j = 0
    for line in lines:
        if line.startswith("src "):
            part = line.split(" ", 3)
            part[2] = str(hold[j])
            j += 1
            out.append(" ".join(part))
        else:
            out.append(line)
    return out


def shows(rng, run, steps, world, micro, accum, many):
    out = []
    for _ in range(many):
        out.append("show %s %d %d %d" % (run, rng.randrange(steps), rng.randrange(world),
                                         rng.randrange(accum)))
    return out


def small(fam, rng):
    cap = rng.choice([256, 512, 1024])
    if fam == "plain":
        kinds = [(rng.randint(3, 9), 0, 0) for _ in range(rng.randint(2, 4))]
    elif fam == "hot":
        kinds = [(rng.randint(4, 10), rng.randint(1, 4), 0) for _ in range(rng.randint(2, 4))]
    elif fam == "heavy":
        kinds = []
        for _ in range(rng.randint(2, 4)):
            n = rng.randint(3, 8)
            kinds.append((n, n - rng.choice([1, 1, 2]), 0))
    elif fam == "wrap":
        kinds = [(rng.randint(2, 5), rng.choice([0, 1]), 0) for _ in range(rng.randint(2, 4))]
    else:
        kinds = [(rng.randint(3, 9), rng.choice([0, 1, 2]), 0) for _ in range(rng.randint(2, 5))]

    tiny = fam in ("wrap", "edge")
    world, micro, accum = geometry(rng, tiny)
    wide = world * micro * accum
    steps = rng.randint(3, 14) if not tiny else rng.randint(6, 40)
    lines, pat, fit = head(rng, kinds, cap, rng.getrandbits(30))

    how_many = {"retire": 1, "cascade": rng.choice([2, 3]), "edge": 1}.get(fam, 0)
    if fam in ("resume", "chain") and rng.random() < 0.5:
        how_many = 1
    if how_many:
        hold = limits(rng, pat, fit, kinds, steps * wide, how_many)
        lines = restate(lines, hold)

    lines.append("open r %d %d %d" % (world, micro, accum))
    lines.append("take r %d" % steps)
    if how_many:
        # Where a retirement lands inside a printed step, a feeder that settles the mix once
        # per step is wrong; printing every step of the run is what reaches that.
        lines += ["show r %d 0 0" % s for s in range(steps)]
    lines += shows(rng, "r", steps, world, micro, accum, rng.randint(1, 3))
    if fam in ("resume", "chain", "edge") or rng.random() < 0.35:
        lines.append("feed r %d" % rng.randint(1, 6))
        lines.append("save r k0")
        w2, m2, a2 = geometry(rng, tiny)
        steps2 = rng.randint(2, 10)
        lines.append("load q k0 %d %d %d" % (w2, m2, a2))
        lines.append("take q %d" % steps2)
        lines += shows(rng, "q", steps2, w2, m2, a2, rng.randint(1, 2))
        if fam == "chain" or rng.random() < 0.3:
            lines.append("feed q %d" % rng.randint(1, 5))
            lines.append("save q k1")
            w3, m3, a3 = geometry(rng, tiny)
            steps3 = rng.randint(2, 8)
            lines.append("load p k1 %d %d %d" % (w3, m3, a3))
            lines.append("take p %d" % steps3)
            lines += shows(rng, "p", steps3, w3, m3, a3, rng.randint(1, 2))
    return lines


def scale(fam, rng):
    cap = 2048
    n = 400
    kinds = [(n, rng.randint(90, 150), 0) for _ in range(4)]
    lines, pat, fit = head(rng, kinds, cap, rng.getrandbits(30))
    world, micro, accum = 8, 4, 8
    wide = world * micro * accum
    steps = rng.randint(680000, 800000)
    if fam == "deep":
        hold = [0] * 4
        j = rng.choice(sorted(set(pat)))
        at = rng.randint(steps * wide // 3, steps * wide * 2 // 3)
        hold[j] = max(1, tally(pat, j, at) // fit[j])
        lines = restate(lines, hold)
    lines.append("open r %d %d %d" % (world, micro, accum))
    lines.append("take r %d" % steps)
    lines += shows(rng, "r", steps, world, micro, accum, 2)
    lines.append("feed r %d" % rng.randint(1, 9))
    lines.append("save r k0")
    lines.append("load q k0 4 4 8")
    lines.append("take q 3")
    lines += shows(rng, "q", 3, 4, 4, 8, 2)
    lines.append("feed q 4")
    lines.append("save q k1")
    lines.append("load p k1 8 2 4")
    lines.append("take p 2")
    lines += shows(rng, "p", 2, 8, 2, 4, 1)
    return lines


def programs(seed, per):
    """[(family, name, lines)] for the whole nonce population."""
    out = []
    for fam, big in FAMILIES:
        count = BIG if big else per
        for i in range(count):
            rng = random.Random("%s|%s|%d" % (seed, fam, i))
            lines = scale(fam, rng) if big else small(fam, rng)
            out.append((fam, "%s-%04d" % (fam, i), lines))
    return out
