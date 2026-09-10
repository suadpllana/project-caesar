"""Programs generated inside the verifier from a seed drawn after the agent's container is gone.

The enumerated set in `cases.py` pins each rule with a program small enough to read. This is
the other half of the grading: programs a submission cannot have seen, in families shaped
around the readings that a per-rule set does not separate.

  plain     ordinary proposals pushed at the head they were planned at
  stagger   several proposals open at once, so bases fall behind the head
  era       a put lands inside a range and is then re-packed together with older slabs, so a
            proposal planned before the put meets a slab holding both eras
  unmix     the same, with a cut or a put earlier in the proposal taking the newer keys back
            out before the fold looks
  twofold   two fold parts in one proposal, the later one forcing the second attempt after the
            earlier one has already re-packed
  steal     appends over ranges that are partly live, so keys move between slabs
  holes     re-packs that leave a slab holding several runs, then queries into the gaps
  astride   slabs holding both eras that sit partly outside the fold's range, or wholly in a
            different one, and therefore force nothing
  floor     folds reaching one slab or none, and cuts that remove nothing
  buckets   proposals whose parts fall in two buckets
  wide      the scale family: one bulk import, then narrow proposals against it
  deep      one bulk import re-packed into a single slab, then narrow proposals against that

`wide` and `deep` are the families the execution limit is about. Everything else is small.
"""
import random

FAMILIES = (
    ("plain", False),
    ("stagger", False),
    ("era", False),
    ("unmix", False),
    ("twofold", False),
    ("steal", False),
    ("holes", False),
    ("astride", False),
    ("floor", False),
    ("buckets", False),
    ("wide", True),
    ("deep", True),
)

SLOT = 20
WIDE = 10
SLOTS = 12
BUCKS = ("v", "w")


def _slot(i):
    return i * SLOT, i * SLOT + WIDE - 1


class Site:
    def __init__(self, r):
        self.r = r
        self.lines = []
        self.n = 0

    def plan(self):
        self.n += 1
        tag = "q%d" % self.n
        self.lines.append("plan %s" % tag)
        return tag

    def part(self, kind, tag, buck, lo, hi):
        self.lines.append("%s %s %s %d %d" % (kind, tag, buck, lo, hi))

    def push(self, tag):
        self.lines.append("push %s" % tag)

    def ask(self, buck):
        if self.r.random() < 0.5:
            self.lines.append("rows %s" % buck)
        else:
            self.lines.append("at %s %d" % (buck, self.r.randrange(0, SLOTS * SLOT)))


def _seed_bucket(s, buck, how_many):
    """A few ordinary slabs to work on."""
    for i in s.r.sample(range(SLOTS), how_many):
        tag = s.plan()
        lo, hi = _slot(i)
        s.part("put", tag, buck, lo, hi)
        s.push(tag)


def _range(r, wide=3):
    i = r.randrange(0, SLOTS - wide)
    return i * SLOT, (i + wide) * SLOT - 1, i, i + wide - 1


def _one_part(s, tag, buck):
    pick = s.r.random()
    if pick < 0.4:
        i = s.r.randrange(0, SLOTS)
        lo, hi = _slot(i)
        if s.r.random() < 0.4:
            lo += s.r.randrange(0, WIDE // 2)
            hi += s.r.randrange(0, SLOT - WIDE)
        s.part("put", tag, buck, lo, hi)
    elif pick < 0.7:
        i = s.r.randrange(0, SLOTS)
        lo, hi = _slot(i)
        if s.r.random() < 0.5:
            lo += s.r.randrange(0, WIDE)
        s.part("cut", tag, buck, lo, hi)
    else:
        lo, hi, _a, _b = _range(s.r, s.r.randrange(2, 5))
        s.part("fold", tag, buck, lo, hi)


def fam_plain(s):
    _seed_bucket(s, "v", 6)
    for _ in range(s.r.randrange(6, 12)):
        tag = s.plan()
        for _ in range(s.r.randrange(1, 3)):
            _one_part(s, tag, "v")
        s.push(tag)
        if s.r.random() < 0.6:
            s.ask("v")
    s.ask("v")


def fam_stagger(s):
    _seed_bucket(s, "v", 6)
    live = []
    for _ in range(s.r.randrange(8, 16)):
        if live and s.r.random() < 0.45:
            s.push(live.pop(s.r.randrange(len(live))))
            if s.r.random() < 0.5:
                s.ask("v")
            continue
        tag = s.plan()
        for _ in range(s.r.randrange(1, 3)):
            _one_part(s, tag, "v")
        live.append(tag)
    for tag in live:
        s.push(tag)
    s.ask("v")


def _era_piece(s, early_parts):
    """A slab holding keys from both sides of an early proposal's base.

    The early proposal is planned first. A put then lands inside its range and a second
    proposal re-packs that put together with older slabs, which is the only way one slab
    comes to hold keys from both sides of the early base. One slot is held back and filled
    only after that re-pack: whether the early proposal reaches that slab is the whole
    difference between a second attempt and none, so a program without it cannot tell the
    two apart.
    """
    lo, hi, a, b = _range(s.r, s.r.randrange(4, 6))
    spare = s.r.randrange(a, b + 1)
    for i in range(a, b + 1):
        if i != spare:
            tag = s.plan()
            s.part("put", tag, "v", *_slot(i))
            s.push(tag)
    early = s.plan()
    fresh = spare
    while fresh == spare:
        fresh = s.r.randrange(a, b + 1)
    for kind in early_parts:
        if kind == "fold":
            s.part("fold", early, "v", lo, hi)
        elif kind == "cut":
            s.part("cut", early, "v", *_slot(fresh))
        else:
            s.part("put", early, "v", *_slot(fresh))
    late = s.plan()
    s.part("put", late, "v", *_slot(fresh))
    s.push(late)
    packer = s.plan()
    s.part("fold", packer, "v", lo, hi)
    s.push(packer)
    newer = s.plan()
    s.part("put", newer, "v", *_slot(spare))
    s.push(newer)
    return early, lo, hi, a, b


def fam_era(s):
    early, lo, _hi, a, b = _era_piece(s, ["fold"])
    for _ in range(s.r.randrange(0, 3)):
        tag = s.plan()
        _one_part(s, tag, "v")
        s.push(tag)
    s.push(early)
    for i in range(a, b + 1):
        s.lines.append("at v %d" % (i * SLOT + 1))
    s.ask("v")


def fam_unmix(s):
    order = ["cut", "fold"] if s.r.random() < 0.5 else ["put", "fold"]
    early, lo, _hi, a, b = _era_piece(s, order)
    s.push(early)
    for i in range(a, b + 1):
        s.lines.append("at v %d" % (i * SLOT + 1))
    s.ask("v")


def fam_twofold(s):
    """Two folds in one proposal: the second forces the attempt the first already ran under."""
    left = 0
    right = 6
    for i in range(left, left + 3):
        tag = s.plan()
        s.part("put", tag, "v", *_slot(i))
        s.push(tag)
    for i in range(right, right + 3):
        tag = s.plan()
        s.part("put", tag, "v", *_slot(i))
        s.push(tag)
    early = s.plan()
    s.part("fold", early, "v", left * SLOT, (left + 3) * SLOT - 1)
    s.part("fold", early, "v", right * SLOT, (right + 3) * SLOT - 1)
    late = s.plan()
    s.part("put", late, "v", *_slot(left + s.r.randrange(0, 3)))
    s.push(late)
    other = s.plan()
    s.part("put", other, "v", *_slot(right + s.r.randrange(0, 3)))
    s.push(other)
    packer = s.plan()
    s.part("fold", packer, "v", right * SLOT, (right + 3) * SLOT - 1)
    s.push(packer)
    s.push(early)
    for i in list(range(left, left + 3)) + list(range(right, right + 3)):
        s.lines.append("at v %d" % (i * SLOT + 1))
    s.ask("v")


def fam_steal(s):
    _seed_bucket(s, "v", 5)
    for _ in range(s.r.randrange(6, 12)):
        tag = s.plan()
        i = s.r.randrange(0, SLOTS - 2)
        lo = i * SLOT + s.r.randrange(0, WIDE)
        hi = lo + s.r.randrange(1, 2 * SLOT)
        s.part("put", tag, "v", lo, hi)
        if s.r.random() < 0.4:
            s.part("cut", tag, "v", lo + 1, lo + 1 + s.r.randrange(0, WIDE))
        s.push(tag)
        s.lines.append("at v %d" % lo)
        if s.r.random() < 0.5:
            s.ask("v")
    s.ask("v")


def fam_holes(s):
    picks = sorted(s.r.sample(range(SLOTS), 6))
    for i in picks:
        tag = s.plan()
        s.part("put", tag, "v", *_slot(i))
        s.push(tag)
    tag = s.plan()
    s.part("fold", tag, "v", 0, SLOTS * SLOT - 1)
    s.push(tag)
    for i in range(SLOTS):
        s.lines.append("at v %d" % (i * SLOT + WIDE + 1))
        s.lines.append("at v %d" % (i * SLOT + 1))
    for _ in range(s.r.randrange(2, 5)):
        tag = s.plan()
        _one_part(s, tag, "v")
        s.push(tag)
        s.ask("v")


def fam_astride(s):
    """The slab holding both eras sits partly outside the fold's range, or in another one."""
    lo, hi, a, b = _range(s.r, 3)
    for i in range(a, b + 1):
        tag = s.plan()
        s.part("put", tag, "v", *_slot(i))
        s.push(tag)
    far = b + 2 + s.r.randrange(0, 2)
    if far >= SLOTS:
        far = SLOTS - 1
    tag = s.plan()
    s.part("put", tag, "v", *_slot(far))
    s.push(tag)
    early = s.plan()
    s.part("fold", early, "v", lo, hi)
    late = s.plan()
    s.part("put", late, "v", *_slot(far))
    s.push(late)
    packer = s.plan()
    s.part("fold", packer, "v", b * SLOT, SLOTS * SLOT - 1)
    s.push(packer)
    s.push(early)
    for i in range(a, min(SLOTS, far + 1)):
        s.lines.append("at v %d" % (i * SLOT + 1))
    s.ask("v")


def fam_floor(s):
    _seed_bucket(s, "v", 3)
    for _ in range(s.r.randrange(6, 12)):
        tag = s.plan()
        pick = s.r.random()
        if pick < 0.4:
            i = s.r.randrange(0, SLOTS)
            s.part("fold", tag, "v", i * SLOT, i * SLOT + SLOT - 1)
        elif pick < 0.7:
            i = s.r.randrange(0, SLOTS)
            s.part("cut", tag, "v", i * SLOT + WIDE, i * SLOT + SLOT - 1)
        else:
            _one_part(s, tag, "v")
        s.push(tag)
        s.ask("v")


def fam_buckets(s):
    _seed_bucket(s, "v", 4)
    _seed_bucket(s, "w", 4)
    for _ in range(s.r.randrange(6, 12)):
        tag = s.plan()
        for _ in range(s.r.randrange(1, 4)):
            _one_part(s, tag, s.r.choice(BUCKS))
        s.push(tag)
        if s.r.random() < 0.6:
            s.ask(s.r.choice(BUCKS))
    s.ask("v")
    s.ask("w")


def fam_wide(s):
    slabs = 60000
    wid = 400
    gap = 100
    step = wid + gap
    top = slabs * step
    s.lines.append("bulk W v %d 0 %d %d" % (slabs, wid, gap))
    late = []
    for i in range(20000):
        tag = "r%d" % i
        a = s.r.randrange(0, top - 6 * step)
        base = a - a % step
        s.lines.append("plan %s" % tag)
        pick = s.r.random()
        if pick < 0.32:
            s.lines.append("cut %s v %d %d" % (tag, a, a + s.r.randrange(1, wid)))
        elif pick < 0.64:
            s.lines.append("put %s v %d %d" % (tag, a, a + s.r.randrange(1, wid)))
        else:
            s.lines.append("fold %s v %d %d" % (tag, base, base + 3 * step - 1))
        s.lines.append("push %s" % tag)
        if i % 7 == 3:
            # An open proposal whose base falls behind while a put lands inside its range
            # and a later fold re-packs that put together with the slabs around it.
            hold = "h%d" % i
            spot = base + 4 * step
            s.lines.append("plan %s" % hold)
            s.lines.append("fold %s v %d %d" % (hold, spot, spot + 3 * step - 1))
            late.append((hold, spot))
            fill = "f%d" % i
            s.lines.append("plan %s" % fill)
            s.lines.append("put %s v %d %d" % (fill, spot + step, spot + step + wid - 1))
            s.lines.append("push %s" % fill)
            pack = "k%d" % i
            s.lines.append("plan %s" % pack)
            s.lines.append("fold %s v %d %d" % (pack, spot, spot + 3 * step - 1))
            s.lines.append("push %s" % pack)
        if late and s.r.random() < 0.6:
            hold, spot = late.pop(0)
            s.lines.append("push %s" % hold)
            s.lines.append("at v %d" % (spot + step))
        if i % 500 == 0:
            s.lines.append("at v %d" % s.r.randrange(0, top))
    for hold, spot in late:
        s.lines.append("push %s" % hold)
    s.lines.append("rows v")


def fam_deep(s):
    slabs = 40000
    wid = 300
    gap = 100
    step = wid + gap
    top = slabs * step
    s.lines.append("bulk W v %d 0 %d %d" % (slabs, wid, gap))
    s.lines.append("plan G")
    s.lines.append("fold G v 0 %d" % (top - 1))
    s.lines.append("push G")
    for i in range(12000):
        tag = "r%d" % i
        a = s.r.randrange(0, top - 4 * step)
        s.lines.append("plan %s" % tag)
        pick = s.r.random()
        if pick < 0.4:
            s.lines.append("cut %s v %d %d" % (tag, a, a + s.r.randrange(1, wid)))
        elif pick < 0.8:
            s.lines.append("put %s v %d %d" % (tag, a, a + s.r.randrange(1, wid)))
        else:
            # The one slab the bulk was re-packed into is never wholly inside a narrow
            # range, so every one of these asks that question of a slab holding tens of
            # thousands of runs.
            base = a - a % step
            s.lines.append("fold %s v %d %d" % (tag, base, base + 4 * step - 1))
        s.lines.append("push %s" % tag)
        if i % 400 == 0:
            s.lines.append("at v %d" % s.r.randrange(0, top))
    s.lines.append("rows v")


MAKE = {
    "plain": fam_plain,
    "stagger": fam_stagger,
    "era": fam_era,
    "unmix": fam_unmix,
    "twofold": fam_twofold,
    "steal": fam_steal,
    "holes": fam_holes,
    "astride": fam_astride,
    "floor": fam_floor,
    "buckets": fam_buckets,
    "wide": fam_wide,
    "deep": fam_deep,
}


def one(fam, seed):
    s = Site(random.Random(seed))
    MAKE[fam](s)
    return s.lines


def programs(seed, per):
    out = []
    for fam, big in FAMILIES:
        how = max(1, per // 15) if big else per
        for i in range(how):
            name = "%s-%d" % (fam, i)
            out.append((fam, name, one(fam, "%s/%s" % (seed, name))))
    return out
