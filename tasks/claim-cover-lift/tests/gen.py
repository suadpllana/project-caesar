"""The graded population, built from a seed drawn after the agent's container is gone.

Eight small families and three wide ones. Each small family is shaped around one place where a
wrong reading of the rules moves the trace: claims that cross the box and slot boundary, a job
covering its own request, the lift and what it frees, two boxes owed grants at once, jobs that
come to wait for each other, repeated acquires, and lines naming jobs that are waiting, stopped
or finished. The wide families exist for the execution limit: one box holding twelve thousand
slot claims, standing lines in five hundred boxes, and a line of readers behind every holder.
"""
import random

FAMILIES = (
    ("plain", False),
    ("cross", False),
    ("cover", False),
    ("lift", False),
    ("order", False),
    ("ring", False),
    ("again", False),
    ("dead", False),
    ("big", True),
    ("busy", True),
    ("lines", True),
)

WIDE = 2


def _slot(box, num):
    return "%s:s%d" % (box, num)


def plain(rng):
    boxes = ["b%d" % n for n in range(1, rng.choice((2, 3, 4)) + 1)]
    jobs = ["j%d" % n for n in range(1, rng.choice((4, 5, 6, 7)) + 1)]
    out = []
    for _ in range(rng.randint(18, 40)):
        job = rng.choice(jobs)
        box = rng.choice(boxes)
        node = box if rng.random() < 0.25 else _slot(box, rng.randint(1, 4))
        roll = rng.random()
        if roll < 0.62:
            out.append("take %s %s %s" % (job, node, rng.choice("rrw")))
        elif roll < 0.78:
            out.append("drop %s %s" % (job, node))
        elif roll < 0.88:
            out.append("show %s" % node)
        else:
            out.append("end %s" % job)
    out.append("show %s" % rng.choice(boxes))
    return out


def cross(rng):
    box = "b1"
    jobs = ["j%d" % n for n in range(1, rng.choice((3, 4, 5)) + 1)]
    out = []
    for _ in range(rng.randint(12, 26)):
        job = rng.choice(jobs)
        roll = rng.random()
        if roll < 0.4:
            out.append("take %s %s %s" % (job, box, rng.choice("rw")))
        elif roll < 0.8:
            out.append("take %s %s %s" % (job, _slot(box, rng.randint(1, 3)), rng.choice("rw")))
        elif roll < 0.9:
            out.append("drop %s %s" % (job, rng.choice([box, _slot(box, rng.randint(1, 3))])))
        else:
            out.append("end %s" % job)
    out.append("show %s" % box)
    out.append("show %s" % _slot(box, 1))
    return out


def cover(rng):
    box = "b1"
    out = ["take j1 %s %s" % (box, rng.choice("rw"))]
    for n in range(2, rng.choice((3, 4, 5))):
        out.append("take j%d %s %s" % (n, _slot(box, n), rng.choice("rw")))
    for n in range(2, 6):
        out.append("take j1 %s %s" % (_slot(box, rng.randint(1, 5)), rng.choice("rw")))
    if rng.random() < 0.5:
        out.append("drop j1 %s" % box)
        out.append("take j1 %s %s" % (_slot(box, rng.randint(1, 5)), "w"))
    out.append("take j9 %s:s7 r" % box)
    out.append("take j9 %s r" % box)
    out.append("show %s" % box)
    out.append("show %s" % _slot(box, 2))
    if rng.random() < 0.5:
        out.append("end j1")
        out.append("show %s" % box)
    return out


def lift(rng):
    box = "b1"
    out = []
    if rng.random() < 0.55:
        out.append("take j2 %s %s" % (_slot(box, rng.randint(9, 12)), rng.choice("rw")))
    picks = rng.sample(range(1, 8), rng.choice((4, 5, 6)))
    modes = [rng.choice("rrw") for _ in picks]
    for num, mode in zip(picks, modes):
        out.append("take j1 %s %s" % (_slot(box, num), mode))
    if rng.random() < 0.3:
        out.append("drop j1 %s" % _slot(box, picks[0]))
        out.append("drop j1 %s" % _slot(box, picks[1]))
    out.append("take j1 %s %s" % (_slot(box, 20), rng.choice("rw")))
    out.append("show %s" % box)
    out.append("show %s" % _slot(box, picks[0]))
    if rng.random() < 0.5:
        out.append("drop j2 %s" % _slot(box, rng.randint(9, 12)))
        out.append("show %s" % box)
    out.append("take j1 %s r" % _slot(box, 21))
    out.append("end j1")
    out.append("show %s" % box)
    return out


def order(rng):
    boxes = ["b%d" % n for n in range(1, rng.choice((2, 3, 4)) + 1)]
    out = []
    for box in boxes:
        out.append("take j1 %s %s" % (_slot(box, 1), "w"))
    askers = 2
    for box in reversed(boxes):
        for _ in range(rng.choice((1, 2))):
            out.append("take j%d %s %s" % (askers, _slot(box, 1), rng.choice("rw")))
            askers += 1
    if rng.random() < 0.4:
        out.append("take j%d %s r" % (askers, boxes[0]))
        askers += 1
    out.append(rng.choice(["end j1", "drop j1 %s" % _slot(boxes[0], 1)]))
    for box in boxes:
        out.append("show %s" % _slot(box, 1))
    return out


def ring(rng):
    size = rng.choice((2, 2, 3, 4))
    jobs = ["j%d" % n for n in range(1, size + 1)]
    boxes = ["b%d" % n for n in range(1, size + 1)]
    out = []
    for n, job in enumerate(jobs):
        for _ in range(rng.choice((1, 1, 2))):
            out.append("take %s %s w" % (job, _slot(boxes[n], 1)))
    if rng.random() < 0.45:
        out.append("take j%d %s r" % (size + 1, _slot(boxes[0], 1)))
        out.append("take j%d %s r" % (size + 2, _slot(boxes[0], 1)))
    for n, job in enumerate(jobs):
        out.append("take %s %s %s" % (job, _slot(boxes[(n + 1) % size], 1), rng.choice("rww")))
    for box in boxes:
        out.append("show %s" % _slot(box, 1))
    out.append("end j1")
    out.append("show %s" % _slot(boxes[0], 1))
    return out


def again(rng):
    box = "b1"
    node = _slot(box, 1)
    out = []
    for _ in range(rng.randint(2, 4)):
        out.append("take j1 %s %s" % (node, rng.choice("rrw")))
    out.append("take j2 %s %s" % (node, rng.choice("rw")))
    out.append("show %s" % node)
    for _ in range(rng.randint(1, 3)):
        out.append("drop j1 %s" % node)
        out.append("show %s" % node)
    if rng.random() < 0.5:
        out.append("take j1 %s r" % box)
        out.append("take j1 %s r" % node)
        out.append("show %s" % box)
    out.append("drop j1 %s" % node)
    out.append("drop j1 %s" % node)
    out.append("show %s" % node)
    out.append("end j1")
    out.append("show %s" % node)
    return out


def dead(rng):
    out = ["take j1 b1:s1 w", "take j2 b2:s1 w", "take j1 b2:s1 w", "take j2 b1:s1 w"]
    rng.shuffle(out[:0])
    out.append("take j2 b3:s1 r")
    out.append("take j1 b3:s1 r")
    out.append("show b3:s1")
    out.append("end j1")
    out.append("take j1 b4:s1 r")
    out.append("drop j1 b1:s1")
    out.append("show b1:s1")
    for n in range(3, 3 + rng.choice((1, 2))):
        out.append("take j%d b%d:s2 %s" % (n, rng.randint(1, 3), rng.choice("rw")))
        out.append("end j%d" % n)
        out.append("take j%d b%d:s2 w" % (n, rng.randint(1, 3)))
    out.append("show b2:s1")
    return out


def big(rng, idx):
    slots = 40000 + 500 * idx
    askers = 1200 + 40 * idx
    out = ["take j1 b1 w", "fill j1 b1 %d r" % slots]
    for k in range(2, 2 + askers):
        out.append("take j%d b1 r" % k)
    out.append("show b1")
    out.append("end j1")
    return out


def busy(rng, idx):
    boxes = 500
    rounds = 40 + 4 * idx
    out = []
    job = 1000
    for b in range(1, boxes + 1):
        out.append("take j%d b%d:s1 w" % (b, b))
        for _ in range(4):
            out.append("take j%d b%d:s1 r" % (job, b))
            job += 1
    for r in range(rounds):
        for b in range(1, boxes + 1):
            out.append("take j%d b%d:s9 r" % (900000 + r, b))
        for b in range(1, boxes + 1):
            out.append("drop j%d b%d:s9" % (900000 + r, b))
    out.append("show b7:s1")
    return out


def lines(rng, idx):
    boxes = 250 + 10 * idx
    per = 6
    out = []
    job = 2
    for b in range(1, boxes + 1):
        out.append("take j1 b%d:s1 w" % b)
    for b in range(1, boxes + 1):
        for _ in range(per):
            out.append("take j%d b%d:s1 r" % (job, b))
            job += 1
    out.append("end j1")
    out.append("show b3:s1")
    return out


SMALL = {"plain": plain, "cross": cross, "cover": cover, "lift": lift,
         "order": order, "ring": ring, "again": again, "dead": dead}
LARGE = {"big": big, "busy": busy, "lines": lines}


def programs(seed, per):
    """Every graded program for this seed: (family, name, lines)."""
    out = []
    for name, wide in FAMILIES:
        count = WIDE if wide else per
        for idx in range(count):
            rng = random.Random("%s/%s/%d" % (seed, name, idx))
            body = LARGE[name](rng, idx) if wide else SMALL[name](rng)
            out.append((name, "%s-%d" % (name, idx), body))
    return out
