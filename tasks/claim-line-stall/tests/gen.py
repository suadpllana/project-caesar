"""Graded programs, generated from a seed drawn after the agent's container is gone.

Seven families. Five are small and shaped at one part of the contract each: general traffic,
one unit fought over by writers, jobs that accumulate cell claims until an ask is raised,
heavy dropping and ending so jobs are forgotten and start again under new numbers, and long
lines where the job holding an ask up holds no claim at all. Two are wide and exist for the
execution limit rather than for a rule.

Nothing here is shipped to the agent, and the seed is drawn in `test.sh` after the agent's
container is gone, so a submission cannot have seen a single one of these programs.
"""
import random

FAMILIES = (
    ("mix", False),
    ("hot", False),
    ("rise", False),
    ("churn", False),
    ("line", False),
    ("flip", False),
    ("wide", True),
    ("tall", True),
)

BIG = 3


def _scope(rng, unit, cells, unitodds=0.18):
    if rng.random() < unitodds:
        return unit
    return "%s/c%d" % (unit, rng.randrange(1, cells + 1))


def _mix(rng):
    jobs = rng.choice([2, 3, 4, 5, 6])
    units = rng.choice([1, 1, 2, 3])
    cells = rng.choice([2, 3, 4, 6])
    out = []
    for _ in range(rng.choice([14, 22, 30, 44])):
        job = "j%d" % rng.randrange(1, jobs + 1)
        unit = "u%d" % rng.randrange(1, units + 1)
        roll = rng.random()
        if roll < 0.58:
            out.append("take %s %s %s" % (job, _scope(rng, unit, cells),
                                          "w" if rng.random() < 0.45 else "r"))
        elif roll < 0.76:
            out.append("drop %s %s" % (job, _scope(rng, unit, cells)))
        elif roll < 0.86:
            out.append("end %s" % job)
        else:
            out.append("show %s" % unit)
    return out


def _hot(rng):
    jobs = rng.choice([3, 4, 5])
    cells = rng.choice([2, 3])
    out = []
    for _ in range(rng.choice([16, 24, 34])):
        job = "j%d" % rng.randrange(1, jobs + 1)
        roll = rng.random()
        if roll < 0.72:
            out.append("take %s %s %s" % (job, _scope(rng, "u1", cells, 0.25),
                                          "w" if rng.random() < 0.7 else "r"))
        elif roll < 0.84:
            out.append("drop %s %s" % (job, _scope(rng, "u1", cells, 0.25)))
        elif roll < 0.9:
            out.append("end %s" % job)
        else:
            out.append("show u1")
    return out


def _rise(rng):
    """Cell claims gathered until the next ask is raised, with someone to be refused by."""
    out = []
    cells = rng.choice([6, 7, 8])
    order = list(range(1, cells + 1))
    rng.shuffle(order)
    if rng.random() < 0.45:
        out.append("take j2 u1/c%d %s" % (order[-1], "w" if rng.random() < 0.6 else "r"))
    for i in order[:rng.choice([3, 4, 5, 6])]:
        out.append("take j1 u1/c%d %s" % (i, "w" if rng.random() < 0.5 else "r"))
    for i in order[:rng.choice([1, 2, 3])]:
        out.append("take j1 u2/c%d %s" % (i, "w" if rng.random() < 0.5 else "r"))
    for _ in range(rng.choice([8, 14, 20])):
        roll = rng.random()
        job = "j%d" % rng.randrange(1, 4)
        unit = "u1" if rng.random() < 0.75 else "u2"
        if roll < 0.6:
            out.append("take %s %s %s" % (job, _scope(rng, unit, cells, 0.15),
                                          "w" if rng.random() < 0.5 else "r"))
        elif roll < 0.7:
            out.append("drop %s %s" % (job, _scope(rng, unit, cells, 0.15)))
        elif roll < 0.76:
            out.append("end %s" % job)
        else:
            out.append("show %s" % unit)
    out.append("show u1")
    out.append("show u2")
    return out


def _churn(rng):
    """Dropping and ending often enough that jobs are forgotten and come back younger."""
    jobs = rng.choice([3, 4, 5])
    units = rng.choice([1, 2])
    cells = rng.choice([2, 3, 4])
    out = []
    for _ in range(rng.choice([20, 30, 40])):
        job = "j%d" % rng.randrange(1, jobs + 1)
        unit = "u%d" % rng.randrange(1, units + 1)
        roll = rng.random()
        if roll < 0.42:
            out.append("take %s %s %s" % (job, _scope(rng, unit, cells),
                                          "w" if rng.random() < 0.5 else "r"))
        elif roll < 0.66:
            out.append("drop %s %s" % (job, _scope(rng, unit, cells)))
        elif roll < 0.8:
            out.append("end %s" % job)
        else:
            out.append("show %s" % unit)
    for n in range(1, jobs + 1):
        out.append("take j%d u1/c%d r" % (n, n % cells + 1))
    out.append("show u1")
    out.append("show u2")
    return out


def _line(rng):
    """Long lines, where most of the jobs standing in them hold nothing at all."""
    cells = rng.choice([2, 3, 4])
    out = ["take j1 u1/c1 %s" % ("w" if rng.random() < 0.5 else "r")]
    nxt = 2
    for _ in range(rng.choice([10, 16, 22])):
        roll = rng.random()
        if roll < 0.44:
            out.append("take j%d %s %s" % (nxt, _scope(rng, "u1", cells, 0.35),
                                           "w" if rng.random() < 0.5 else "r"))
            nxt += 1
        elif roll < 0.6:
            who = rng.randrange(1, nxt)
            cell = rng.randrange(1, cells + 1)
            out.append("take j%d u1/c%d r" % (who, cell))
            out.append("take j%d u1 %s" % (who, "w" if rng.random() < 0.5 else "r"))
            if rng.random() < 0.5:
                out.append("drop j%d u1/c%d" % (who, cell))
        elif roll < 0.72:
            out.append("take j%d %s %s" % (rng.randrange(1, nxt), _scope(rng, "u1", cells, 0.3),
                                           "w" if rng.random() < 0.5 else "r"))
        elif roll < 0.84:
            out.append("drop j%d %s" % (rng.randrange(1, nxt), _scope(rng, "u1", cells, 0.3)))
        elif roll < 0.93:
            out.append("end j%d" % rng.randrange(1, nxt))
        else:
            out.append("show u1")
    out.append("show u1")
    return out


def _flip(rng):
    """A job holding a claim asks for the unit and then gives that claim up while it waits."""
    cells = rng.choice([3, 4, 5])
    a = rng.randrange(1, cells + 1)
    b = rng.randrange(1, cells + 1)
    out = [
        "take j1 u1/c%d w" % a,
        "take j2 u1/c%d %s" % (b, "w" if rng.random() < 0.5 else "r"),
        "take j3 u1 %s" % ("w" if rng.random() < 0.5 else "r"),
        "take j2 u1 %s" % ("w" if rng.random() < 0.5 else "r"),
    ]
    if rng.random() < 0.75:
        out.append("drop j2 u1/c%d" % b)
    for _ in range(rng.choice([6, 10, 16])):
        roll = rng.random()
        job = "j%d" % rng.randrange(1, 5)
        if roll < 0.4:
            out.append("take %s %s %s" % (job, _scope(rng, "u1", cells, 0.3),
                                          "w" if rng.random() < 0.5 else "r"))
        elif roll < 0.64:
            out.append("drop %s %s" % (job, _scope(rng, "u1", cells, 0.3)))
        elif roll < 0.78:
            out.append("end %s" % job)
        else:
            out.append("show u1")
    out.append("show u1")
    return out


def _wide(rng):
    """Many units held, a long line standing on them, and steady traffic beside it."""
    units, waiters, rounds = 1600, 3000, 26000
    out = []
    for i in range(1, units + 1):
        out.append("take h%d u%d/c1 w" % (i, i))
    for k in range(1, waiters + 1):
        out.append("take b%d u%d w" % (k, rng.randrange(1, units + 1)))
    for step in range(rounds):
        job = "t%d" % (step % 800 + 1)
        unit = units + 1 + step % 600
        out.append("take %s u%d/c1 %s" % (job, unit, "r" if step % 2 else "w"))
        out.append("drop %s u%d/c1" % (job, unit))
        if step % 20 == 9:
            out.append("show u%d" % rng.randrange(1, units + 1))
    return out


def _tall(rng):
    """Asks raised to the whole unit while the line beside them stays long."""
    held, waiters, cycles = 700, 2000, 1500
    out = []
    for i in range(1, held + 1):
        out.append("take m%d u%d/c1 w" % (i, i))
    for k in range(1, waiters + 1):
        out.append("take p%d u%d w" % (k, rng.randrange(1, held + 1)))
    base = held + 1
    for cyc in range(cycles):
        unit = base + cyc
        who = ["g%d" % (cyc * 3 + n) for n in (1, 2, 3)]
        for n, job in enumerate(who):
            for c in range(1, 5):
                out.append("take %s u%d/c%d %s" % (job, unit, n * 4 + c,
                                                   "w" if (n + c) % 3 else "r"))
        for job in who:
            out.append("take %s u%d/c%d r" % (job, unit, 13 + cyc % 3))
        out.append("show u%d" % unit)
        for job in who:
            out.append("end %s" % job)
        for job in who:
            out.append("take %s u%d/c1 r" % (job, unit))
            out.append("drop %s u%d/c1" % (job, unit))
    return out


MAKERS = {
    "mix": _mix,
    "hot": _hot,
    "rise": _rise,
    "churn": _churn,
    "line": _line,
    "flip": _flip,
    "wide": _wide,
    "tall": _tall,
}


def programs(seed, per):
    out = []
    for fam, big in FAMILIES:
        count = BIG if big else per
        for i in range(count):
            rng = random.Random("%s/%s/%d" % (seed, fam, i))
            out.append((fam, "%s-%03d" % (fam, i), MAKERS[fam](rng)))
    return out
