"""Additional generated input families for retained source reconciliation.

This is additive: retain all original families and their input programs in the final grader.
The dormant family defaults are a calibration candidate, not a claimed performance gate.
All randomness comes from the supplied seed. Ranges always have ordered inclusive ends.
"""
import random

import new_cases


FAMILIES = (
    ("source_stagger", False),
    ("source_replay", False),
    ("source_components", False),
    ("source_nested", False),
    ("source_history", False),
    ("source_dormant", True),
)


class Site:
    def __init__(self, rng):
        self.r = rng
        self.lines = []
        self.serial = 0

    def plan(self):
        self.serial += 1
        tag = "s%d" % self.serial
        self.lines.append("plan " + tag)
        return tag

    def part(self, op, tag, bucket, lo, hi):
        self.lines.append("%s %s %s %d %d" % (op, tag, bucket, lo, hi))

    def push(self, tag):
        self.lines.append("push " + tag)

    def commit(self, op, bucket, lo, hi):
        tag = self.plan()
        self.part(op, tag, bucket, lo, hi)
        self.push(tag)

    def query(self, bucket, keys=()):
        self.lines.append("rows " + bucket)
        for key in keys:
            self.lines.append("at %s %d" % (bucket, key))


def _part(s, tag):
    bucket = s.r.choice(("v", "w", "z"))
    lo = s.r.randrange(-10, 25) * 3
    hi = lo + s.r.randrange(0, 24)
    op = s.r.choices(("put", "cut", "fold"), (3, 2, 5))[0]
    s.part(op, tag, bucket, lo, hi)


def fam_stagger(s):
    for bucket in ("v", "w", "z"):
        tag = s.plan()
        for key in range(0, 61, 10):
            s.part("put", tag, bucket, key, key + 4)
        s.push(tag)
    pending = []
    for _ in range(s.r.randrange(30, 65)):
        # Parts may be appended long after plan, so capturing when the fold is added fails.
        if pending and s.r.random() < 0.35:
            tag = s.r.choice(pending)
            _part(s, tag)
            if s.r.random() < 0.5:
                s.push(tag)
                pending.remove(tag)
        else:
            tag = s.plan()
            for _ in range(s.r.randrange(1, 5)):
                _part(s, tag)
            if s.r.random() < 0.55:
                s.push(tag)
            else:
                pending.append(tag)
        if s.r.random() < 0.2:
            s.query(s.r.choice(("v", "w", "z")), (0, 10, 30, 60))
    s.r.shuffle(pending)
    for tag in pending:
        s.push(tag)
    for bucket in ("v", "w", "z"):
        s.query(bucket, range(-10, 90, 3))


def fam_replay(s):
    # Every independently mixed region can require a new replay. Prefix effects and earlier
    # folds must be rerun, while unrelated material that landed later remains unselected.
    regions = s.r.randrange(2, 7)
    seed = s.plan()
    for i in range(regions):
        for delta in (0, 10, 30):
            s.part("put", seed, "v", 100 * i + delta, 100 * i + delta + 4)
    s.part("put", seed, "w", 0, 9)
    s.push(seed)
    early = s.plan()
    s.part("cut", early, "w", 2, 5)
    s.part("put", early, "w", 100, 104)
    order = list(range(regions))
    s.r.shuffle(order)
    for i in order:
        s.part("fold", early, "v", 100 * i, 100 * i + 39)
    for i in range(regions):
        base = 100 * i
        # With some probability replacing part of an old source makes coordinate and
        # incarnation overlap disagree inside the connected source component.
        if s.r.random() < 0.5:
            s.commit("put", "v", base + 2, base + 6)
        else:
            s.commit("put", "v", base + 5, base + 9)
        s.commit("fold", "v", base, base + 19)
        s.commit("put", "v", base + 20, base + 24)
        if s.r.random() < 0.3:
            s.commit("cut", "v", base, base)
    s.push(early)
    for i in range(regions):
        s.query("v", (100 * i + j for j in (0, 2, 5, 10, 20, 30)))
    s.query("w", (0, 2, 6, 100))


def transform(lines, rng):
    """Scale whole key cells, preserving geometry, gaps, incarnation equality and order."""
    scale = rng.randrange(1, 9)
    shift = rng.randrange(-500, 501)
    bucket_map = {"v": rng.choice(("v", "x", "other")), "w": "second", "z": "third"}
    transformed = []
    for line in lines:
        w = line.split()
        op = w[0]
        if op in ("put", "cut", "fold"):
            w[2] = bucket_map.get(w[2], w[2])
            w[3] = str(shift + scale * int(w[3]))
            w[4] = str(shift + scale * (int(w[4]) + 1) - 1)
        elif op == "bulk":
            w[2] = bucket_map.get(w[2], w[2])
            w[4] = str(shift + scale * int(w[4]))
            w[5] = str(scale * int(w[5]))
            w[6] = str(scale * int(w[6]))
        elif op == "at":
            w[1] = bucket_map.get(w[1], w[1])
            w[2] = str(shift + scale * int(w[2]) + rng.randrange(scale))
        elif op == "rows":
            w[1] = bucket_map.get(w[1], w[1])
        transformed.append(" ".join(w))
    return transformed


def fam_components(s):
    # These paired structures differ by one real held key, not a label or a special flag.
    # One traverses source -> head -> source; the other must preserve the source spanning a hole.
    names = ("source-closure-holes", "source-closure-two-way", "source-selective-replay",
             "source-bucket-isolation", "source-retired-extreme")
    s.lines.extend(transform(new_cases.PROGS[s.r.choice(names)], s.r))


def fam_nested(s):
    bucket = "v"
    count = s.r.randrange(3, 9)
    seed = s.plan()
    for i in range(count):
        s.part("put", seed, bucket, 10 * i, 10 * i + 3)
    s.push(seed)
    early = s.plan()
    if s.r.random() < 0.5:
        s.part("cut", early, bucket, 10 * (count - 1), 10 * (count - 1) + 1)
    s.part("put", early, "w", 0, 3)
    s.part("fold", early, bucket, 0, 10 * count)
    # Selecting a strict subset of the original sources conflicts with the own wide slab.
    # A preceding cut may retire a selected source, and every tentative effect still rolls back.
    pick = s.r.randrange(count)
    s.part("fold", early, bucket, 10 * pick, 10 * pick + 3)
    if s.r.random() < 0.5:
        s.commit("put", bucket, 10 * s.r.randrange(count), 10 * s.r.randrange(count) + 10 * count)
    s.push(early)
    s.commit("put", "w", 20, 20)
    s.query(bucket, range(0, 10 * count, 2))
    s.query("w", (0, 20))


def fam_history(s):
    seed = s.plan()
    for i in range(5):
        s.part("put", seed, "v", 30 * i, 30 * i + 19)
    s.push(seed)
    pending = []
    for turn in range(s.r.randrange(8, 20)):
        tag = s.plan()
        pending.append(tag)
        i = s.r.randrange(5)
        left = 30 * i + s.r.randrange(0, 10)
        right = min(149, left + s.r.randrange(1, 65))
        s.part("fold", tag, "v", left, right)
        if s.r.random() < 0.3:
            _part(s, tag)
        op = s.r.choice(("put", "cut", "fold"))
        lo = 30 * s.r.randrange(5) + s.r.randrange(0, 8)
        hi = lo + s.r.randrange(1, 20)
        s.commit(op, "v", lo, hi)
        if turn % 4 == 3:
            s.push(pending.pop(s.r.randrange(len(pending))))
    s.r.shuffle(pending)
    for tag in pending:
        s.push(tag)
    s.query("v", range(0, 151, 3))


def dormant_program(seed, slabs=40000, proposals=8000, width=64, gap=16):
    """Retain many different source roots while each committed update touches one small region.

    A plan-time whole-store copy expands with slabs*proposals. A persistent or block-sharing
    implementation should retain the original roots plus the paths changed by narrow updates.
    Exact defaults must be measured with the final reference before they become graded bounds.
    """
    rng = random.Random(seed)
    step = width + gap
    lines = ["bulk import v %d 0 %d %d" % (slabs, width, gap)]
    held = []
    for i in range(proposals):
        spot = rng.randrange(slabs - 2)
        lo = spot * step
        tag = "d%d" % i
        held.append((tag, lo))
        lines.extend(("plan " + tag, "fold %s v %d %d" % (tag, lo, lo + 2 * step - 1)))
        change = "c%d" % i
        lines.extend(("plan " + change,
                      "cut %s v %d %d" % (change, lo, lo + width // 4 - 1),
                      "put %s v %d %d" % (change, lo + width // 2, lo + width - 1),
                      "push " + change))
    rng.shuffle(held)
    for i, (tag, lo) in enumerate(held):
        lines.append("push " + tag)
        if i % 200 == 0:
            lines.append("at v %d" % (lo + width // 2))
    lines.append("rows v")
    return lines


def fam_dormant(s):
    s.lines.extend(dormant_program(s.r.getrandbits(128)))


MAKE = {
    "source_stagger": fam_stagger,
    "source_replay": fam_replay,
    "source_components": fam_components,
    "source_nested": fam_nested,
    "source_history": fam_history,
    "source_dormant": fam_dormant,
}


def one(fam, seed):
    site = Site(random.Random(seed))
    MAKE[fam](site)
    return site.lines


def programs(seed, per):
    result = []
    for fam, big in FAMILIES:
        for i in range(1 if big else per):
            name = "%s-%d" % (fam, i)
            result.append((fam, name, one(fam, "%s/%s" % (seed, name))))
    return result
