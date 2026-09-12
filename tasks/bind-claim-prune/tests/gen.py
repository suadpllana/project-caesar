"""The graded population, built from a seed the submission never saw.

Ten small families and two large ones. The small families are not random programs with the
ordinary case made rare: each is shaped around a wrong reading, because a reading that moves
one program in three hundred is a reading the population does not test.

The skeleton is the same everywhere - head units off the input list, then bundles chained so
each one pulls from the next - and the families move the knobs that decide which reading it
separates. A unit off the input list is planted on a key a member of the bundle before it
actually claimed, so a displacement happens rather than being hoped for; heads take their keys
from a pool of their own, since a key a head claims can never change hands and a population
where the heads have claimed everything tests nothing. Members reach backwards as well as
forwards, so a take wants a name an earlier member of the same bundle gives and a group needs
more than one pass. Spares name what bundles give, so a spare pulls a member, and their sizes
come from four values, so ties on size are ordinary rather than rare.

The two large families are the same chained bundle at the sizes the brief states, and exist
for the execution limit rather than for a rule.
"""
import random

FAMILIES = (
    ("plain", False),
    ("claim", False),
    ("shift", False),
    ("again", False),
    ("order", False),
    ("pack", False),
    ("soft", False),
    ("spare", False),
    ("twice", False),
    ("cut", False),
    ("wide", True),
    ("deep", True),
)

BIG = 3
SIZES = (8, 16, 24, 40)


class Prog:
    def __init__(self):
        self.lines = []
        self.units = []
        self.count = {}

    def unit(self, name):
        self.lines.append("u %s" % name)
        self.units.append(name)
        self.count[name] = 0
        return name

    def part(self, size, key=None):
        who = self.units[-1]
        self.lines.append("p %d %s" % (size, key if key else "-"))
        i = self.count[who]
        self.count[who] = i + 1
        return i

    def give(self, nm, how):
        self.lines.append("g %s %s" % (nm, how))

    def use(self, nm, how):
        self.lines.append("r %s %s" % (nm, how))

    def spare(self, nm, size):
        self.lines.append("t %s %d" % (nm, size))

    def bundle(self, name, members):
        self.lines.append("b %s %s" % (name, " ".join(members)))

    def root(self, nm):
        self.lines.append("root %s" % nm)

    def hold(self, who, i):
        self.lines.append("hold %s %d" % (who, i))

    def link(self, items):
        self.lines.append("link %s" % " ".join(items))

    def ask(self, nm):
        self.lines.append("at %s" % nm)

    def img(self):
        self.lines.append("img")


def how(rng, weak):
    return "w" if rng.random() < weak else "s"


def shape(rng, cfg):
    p = Prog()
    nb = cfg["bundles"]
    weak = cfg["weak"]
    wide = cfg["names"]
    keys = ["k%d" % i for i in range(cfg["keys"])]
    hkeys = ("hk0", "hk1")
    lay = [["n%d_%d" % (t, i) for i in range(wide)] for t in range(nb + 2)]
    seat = {}
    made = []
    every = []
    for row in lay:
        every.extend(row)

    def pick(t):
        return lay[t][rng.randrange(wide)]

    tie = lay[nb + 1][0]
    tied = list(SIZES[:cfg["tiesizes"]])

    def sparename(j):
        if rng.random() < cfg["sparehit"]:
            return pick(rng.randint(1, nb))
        return pick(nb + 1)

    def sparing(j):
        """Some spares are planted on one name at sizes drawn from a short list, so the
        largest of them, and the tie between two units that spared the largest, both land."""
        if rng.random() < cfg["twinspare"]:
            p.spare(tie, rng.choice(tied))
        elif rng.random() < cfg["spares"]:
            p.spare(sparename(j), rng.choice(SIZES))

    heads = []
    for h in range(cfg["heads"]):
        who = p.unit("h%d" % h)
        heads.append(who)
        made.append(who)
        seat[who] = 0
        for _ in range(rng.randint(1, 2)):
            why = None
            if rng.random() < cfg["keyrate"]:
                why = rng.choice(hkeys)
            elif rng.random() < 0.15:
                why = rng.choice(keys)
            seat[who] = p.part(rng.randint(4, 24), why) + 1
            p.give(pick(0), how(rng, weak * 0.5))
            for _ in range(rng.randint(1, 3)):
                p.use(pick(1), how(rng, weak))
            if rng.random() < cfg["tieuse"]:
                p.use(tie, "s")
        sparing(0)

    packs = []
    emitted = {}
    for j in range(nb):
        mem = []
        emitted[j] = []
        for m in range(rng.randint(2, cfg["members"])):
            who = p.unit("m%d_%d" % (j, m))
            mem.append(who)
            made.append(who)
            seat[who] = 0
            for _ in range(rng.randint(1, cfg["parts"])):
                why = None
                if rng.random() < cfg["keyrate"]:
                    why = rng.choice(keys)
                    emitted[j].append(why)
                seat[who] = p.part(rng.randint(3, 18), why) + 1
                for _ in range(rng.randint(1, 2)):
                    p.give(pick(j + 1), how(rng, weak * 0.5))
                for _ in range(rng.randint(0, 2)):
                    p.use(pick(j + 2), how(rng, weak))
                if rng.random() < cfg["back"]:
                    p.use(pick(j + 1), how(rng, weak * 0.4))
                if j and rng.random() < cfg["back"]:
                    p.use(pick(j), how(rng, weak * 0.4))
                if rng.random() < cfg["tieuse"]:
                    p.use(tie, "s")
                if rng.random() < cfg["ballast"]:
                    seat[who] = p.part(rng.randint(3, 12)) + 1
                    p.give("z%d_%d" % (j, m), "s")
            sparing(j)
        if cfg["jumble"]:
            rng.shuffle(mem)
        p.bundle("b%d" % j, mem)
        packs.append("b%d" % j)

    late = {}
    for j in cfg["over"]:
        if j >= nb:
            continue
        who = p.unit("d%d" % j)
        late[j] = who
        made.append(who)
        seat[who] = 0
        why = rng.choice(emitted[j]) if emitted[j] else rng.choice(keys)
        seat[who] = p.part(rng.randint(6, 30), why) + 1
        for _ in range(rng.randint(0, 2)):
            p.give(pick(j + 1), how(rng, weak * 0.5))
        for _ in range(rng.randint(0, 2)):
            p.use(pick(j + 2), how(rng, weak))
        if rng.random() < cfg["twin"]:
            seat[who] = p.part(rng.randint(4, 20)) + 1
            p.give(pick(j + 1), "s")

    for nm in rng.sample(lay[0], min(wide, cfg["roots"])):
        p.root(nm)
    if cfg["holds"] and made:
        who = rng.choice(made)
        if seat.get(who):
            p.hold(who, rng.randrange(seat[who]))

    items = list(heads)
    if cfg["group"] and len(packs) > 1:
        items.append("(")
        items.extend(packs)
        items.append(")")
        for j in sorted(late):
            items.append(late[j])
    else:
        for j, name in enumerate(packs):
            items.append(name)
            if j in late:
                items.append(late[j])
    p.link(items)

    for j in range(nb):
        every.append("z%d_0" % j)
    for nm in rng.sample(every, min(len(every), cfg["asks"])):
        p.ask(nm)
    p.img()
    return p.lines


BASE = {
    "heads": 2, "bundles": 2, "members": 4, "parts": 2, "names": 4, "keys": 3,
    "keyrate": 0.35, "weak": 0.2, "spares": 0.15, "sparehit": 0.5, "ballast": 0.2,
    "back": 0.25, "twin": 0.3, "roots": 2, "holds": True, "group": False,
    "twinspare": 0.1, "tiesizes": 2, "tieuse": 0.12,
    "jumble": False, "over": (), "asks": 6,
}


def cfg(**over):
    out = dict(BASE)
    out.update(over)
    return out


def plain(rng):
    return shape(rng, cfg(keyrate=0.1, weak=0.15, back=0.15))


def claim(rng):
    return shape(rng, cfg(keys=2, keyrate=0.85, parts=3))


def shift(rng):
    return shape(rng, cfg(keys=2, keyrate=0.7, over=(0,), members=5, back=0.35))


def again(rng):
    return shape(rng, cfg(keys=2, keyrate=0.8, over=(0, 1), bundles=3, members=5, names=3,
                          back=0.4, twin=0.1))


def order(rng):
    return shape(rng, cfg(jumble=True, members=6, names=2, keyrate=0.2, back=0.8))


def pack(rng):
    return shape(rng, cfg(group=True, bundles=3, members=6, names=5, keyrate=0.25,
                          jumble=True, back=0.85))


def soft(rng):
    return shape(rng, cfg(weak=0.55, keyrate=0.3, names=3, members=5, back=0.35))


def spare(rng):
    return shape(rng, cfg(spares=0.85, sparehit=0.55, twinspare=0.75, tiesizes=3, names=3,
                          tieuse=0.55, keyrate=0.3, members=5, over=(0,)))


def twice(rng):
    return shape(rng, cfg(names=2, keys=2, keyrate=0.7, members=5, parts=3, over=(0,),
                          twin=0.9))


def cut(rng):
    return shape(rng, cfg(ballast=0.85, weak=0.45, roots=1, keyrate=0.25, members=5,
                          asks=8, back=0.3))


SMALL = {
    "plain": plain, "claim": claim, "shift": shift, "again": again, "order": order,
    "pack": pack, "soft": soft, "spare": spare, "twice": twice, "cut": cut,
}


def chain(tag, n, step, ask):
    return [
        "bulk %s chain %d %d" % (tag, n, step),
        "u top",
        "p 16 -",
        "g start s",
        "r %sx0 s" % tag,
        "root start",
        "link top %s" % tag,
        "at %sx%d" % (tag, ask),
        "img",
    ]


def programs(seed, per):
    """Every graded program, in a fixed order, from one seed."""
    out = []
    for fam, big in FAMILIES:
        if big:
            for i in range(BIG):
                if fam == "wide":
                    lines = chain("wide", 60000, 2, 40000 + 2 * i)
                else:
                    lines = chain("deep", 60000, 1, 100 + i)
                out.append((fam, "%s-%02d" % (fam, i), lines))
            continue
        make = SMALL[fam]
        for i in range(per):
            rng = random.Random("%s:%s:%d" % (seed, fam, i))
            out.append((fam, "%s-%02d" % (fam, i), make(rng)))
    return out
