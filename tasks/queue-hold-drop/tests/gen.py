"""Programs generated inside the verifier from a seed drawn after the agent's container is gone.

`cases.py` pins one rule at a time with programs short enough to read. This is the other half:
programs a submission cannot have seen, in families shaped around the mechanisms rather than
drawn uniformly, because a population that is not shaped around a mechanism does not exercise
it.

  plain     changes made against records the server has already confirmed, sent and answered in
            step, so nothing is ever held back and nothing is ever taken away
  chain     creations under records whose own creations are still on the queue, so holding runs
            several changes deep
  spread    moves and creations naming two records at once, so holding reaches records that do
            carry an id
  refuse    refusals with dependents at varying distance, including changes that had already
            gone out
  cancel    removals of records the server has never confirmed, with children, moves and
            further changes queued behind them
  remote    arrivals from another client that move records into and out of the reach of a
            removal already on the queue
  stale     arrivals that take away records the queue still has changes for
  count     fields added to over a base that moves underneath them
  order     acceptances and arrivals between listings, so records change the group they are
            printed in
  idle      answers with nothing to answer, and refusals that empty the queue
  wide      the scale family: a long queue with a question after every change
  deep      the scale family: a large confirmed tree with a removal standing over it

`wide` and `deep` are what the execution limit is about. Every other family is small.
"""
import random

FAMILIES = (
    ("plain", False),
    ("chain", False),
    ("spread", False),
    ("refuse", False),
    ("cancel", False),
    ("remote", False),
    ("stale", False),
    ("count", False),
    ("order", False),
    ("idle", False),
    ("wide", True),
    ("deep", True),
)

FIELDS = ("w", "h", "n", "k")
BIG = 3


class Site:
    """A program under construction, with just enough bookkeeping to shape it."""

    def __init__(self, r):
        self.r = r
        self.lines = []
        self.mine = []          # records the user made
        self.far = []           # records that arrived from another client
        self.up = {}            # the parent each record was made under
        self.nm = 0
        self.nf = 0

    def say(self, line):
        self.lines.append(line)

    def mint(self):
        self.nm += 1
        return "a%d" % self.nm

    def arrive(self, parent="-"):
        self.nf += 1
        name = "q%d" % self.nf
        self.say("oth new %s %s" % (name, parent))
        self.far.append(name)
        self.up[name] = parent
        return name

    def make(self, parent="-"):
        name = self.mint()
        self.say("new %s %s" % (name, parent))
        self.mine.append(name)
        self.up[name] = parent
        return name

    def known(self):
        return self.mine + self.far

    def pick(self, pool=None):
        pool = pool if pool is not None else self.known()
        return self.r.choice(pool) if pool else "-"

    def field(self):
        return self.r.choice(FIELDS)

    def poke(self, name):
        """One ordinary change to a record that already exists."""
        roll = self.r.random()
        if roll < 0.45:
            self.say("set %s %s %d" % (name, self.field(),
                                       0 if self.r.random() < 0.2 else self.r.randint(-9, 99)))
        elif roll < 0.8:
            self.say("add %s %s %d" % (name, self.field(), self.r.randint(-5, 20)))
        else:
            self.say("mov %s %s" % (name, self.pick(self.known() + ["-"])))

    def drain(self, most=4):
        """Send, then answer some of what went out."""
        self.say("snd")
        for _ in range(self.r.randint(1, most)):
            self.say("ok" if self.r.random() < 0.82 else "no")

    def look(self, many=3):
        for _ in range(self.r.randint(1, many)):
            if self.r.random() < 0.85 and self.known():
                self.say("ask %s" % self.pick())
            else:
                self.say("all")


def _plain(s):
    root = s.arrive()
    for _ in range(s.r.randint(3, 6)):
        s.make(root)
        s.say("snd")
        s.say("ok")
    for _ in range(s.r.randint(4, 10)):
        s.poke(s.pick(s.mine))
        s.say("snd")
        s.say("ok")
    s.look(4)


def _chain(s):
    root = s.arrive()
    at = root
    for _ in range(s.r.randint(3, 7)):
        at = s.make(at)
        if s.r.random() < 0.6:
            s.poke(at)
    s.say("snd")
    s.look(2)
    for _ in range(s.r.randint(2, 6)):
        s.say("ok")
        if s.r.random() < 0.5:
            s.say("snd")
        if s.r.random() < 0.5:
            s.look(2)
    s.say("snd")
    s.look(3)


def _spread(s):
    """Holding that reaches records which do carry an id, two and three changes out."""
    one = s.arrive()
    two = s.arrive()
    three = s.arrive()
    held = s.make(one)
    s.say("mov %s %s" % (two, held))
    for _ in range(s.r.randint(1, 3)):
        roll = s.r.random()
        if roll < 0.35:
            s.say("mov %s %s" % (three, two))
        elif roll < 0.6:
            s.poke(two)
        elif roll < 0.8:
            s.poke(three)
        else:
            s.make(held)
    s.poke(one)
    s.say("snd")
    s.look(2)
    for _ in range(s.r.randint(1, 3)):
        s.say("ok")
        s.say("snd")
        s.look(2)


def _refuse(s):
    """Refusals whose take-away has to spread outward, and one that must not reach backwards."""
    root = s.arrive()
    side = s.arrive()
    if s.r.random() < 0.45:
        top = s.make(root)
        s.say("snd")
        s.say("mov %s %s" % (top, root))
        s.poke(root)
        s.say("snd")
        s.say("ok")
        s.say("no")
        s.say("snd")
        s.look(2)
        return
    top = s.make(root)
    kid = s.make(top)
    s.say("mov %s %s" % (side, kid))
    s.poke(side)
    if s.r.random() < 0.5:
        s.poke(s.pick([top, kid]))
    s.say("snd")
    s.say("no")
    s.look(2)
    for _ in range(s.r.randint(1, 3)):
        s.say("snd")
        s.say("ok" if s.r.random() < 0.6 else "no")
    s.look(3)


def _cancel(s):
    """Cancelled creations with work queued behind them, some of it on records that survive."""
    root = s.arrive()
    side = s.arrive()
    top = s.make(root)
    kid = s.make(top)
    s.say("mov %s %s" % (side, top))
    s.say("set %s w %d" % (side, s.r.randint(1, 30)))
    for _ in range(s.r.randint(0, 2)):
        s.poke(s.pick([kid, top, side]))
    if s.r.random() < 0.4:
        s.make(root)
    s.say("cut %s" % (top if s.r.random() < 0.7 else kid))
    s.say("snd")
    s.look(3)
    for _ in range(s.r.randint(1, 3)):
        s.say("ok")
        s.say("snd")
    s.look(2)


def _remote(s):
    """A removal standing over a tree that arrivals keep rearranging underneath it."""
    root = s.arrive()
    side = s.arrive()
    mid = s.arrive(root)
    low = s.arrive(mid)
    bed = s.arrive(low)
    s.say("cut %s" % (root if s.r.random() < 0.6 else mid))
    s.look(3)
    for _ in range(s.r.randint(3, 6)):
        roll = s.r.random()
        if roll < 0.5:
            s.say("oth mov %s %s" % (s.pick([side, low, bed, mid]),
                                     s.pick([root, mid, low, side, "-"])))
        elif roll < 0.7:
            s.arrive(s.pick([root, mid, low, bed, "-"]))
        elif roll < 0.85:
            s.say("oth set %s %s %d" % (s.pick(s.far), s.field(), s.r.randint(0, 40)))
        else:
            s.say("oth cut %s" % s.pick([low, bed, side]))
        s.look(2)
    s.say("mov %s %s" % (side, bed))
    s.look(3)


def _stale(s):
    root = s.arrive()
    one = s.arrive(root)
    two = s.arrive(root)
    for _ in range(s.r.randint(2, 5)):
        s.poke(s.pick([one, two, root]))
    s.say("oth cut %s" % s.pick([one, two, root]))
    s.look(3)
    s.say("snd")
    for _ in range(s.r.randint(1, 3)):
        s.say("ok" if s.r.random() < 0.7 else "no")
    s.look(3)


def _count(s):
    root = s.arrive()
    for _ in range(s.r.randint(2, 4)):
        field = s.field()
        s.say("add %s %s %d" % (root, field, s.r.randint(1, 9)))
        s.look(1)
        if s.r.random() < 0.6:
            s.say("oth set %s %s %d" % (root, field, s.r.randint(0, 50)))
        s.look(1)
        s.say("snd")
        s.say("ok")
        s.look(1)
    kid = s.make(root)
    s.say("add %s %s %d" % (kid, s.field(), 7))
    s.say("snd")
    s.say("ok")
    s.say("snd")
    s.say("ok")
    s.look(2)


def _order(s):
    s.arrive()
    for _ in range(s.r.randint(2, 4)):
        s.make(s.pick(s.far + ["-"]))
    s.say("all")
    for _ in range(s.r.randint(2, 5)):
        if s.r.random() < 0.5:
            s.arrive(s.pick(s.far + ["-"]))
        else:
            s.say("snd")
            s.say("ok")
        s.say("all")


def _idle(s):
    root = s.arrive()
    s.say("ok")
    s.say("no")
    top = s.make(root)
    s.say("snd")
    s.say("no")
    s.say("ok")
    s.look(2)
    for _ in range(s.r.randint(1, 3)):
        s.poke(root)
        s.say("snd")
        s.say("ok")
        s.say("ok")
    s.say("cut %s" % top)
    s.look(2)


def _wide(s, span):
    root = s.arrive()
    made = []
    for i in range(span):
        name = s.make(root)
        made.append(name)
        if i % 3 == 1:
            s.say("set %s w %d" % (name, i))
        s.say("ask %s" % made[s.r.randrange(len(made))])
    s.say("snd")
    for _ in range(4):
        s.say("ok")
        s.say("ask %s" % made[s.r.randrange(len(made))])
    s.say("ask %s" % root)


def _deep(s, span, asks):
    root = s.arrive()
    tier = [root]
    made = [root]
    while len(made) < span:
        parent = tier[s.r.randrange(len(tier))]
        name = s.arrive(parent)
        made.append(name)
        if len(tier) < 40 or s.r.random() < 0.2:
            tier.append(name)
    s.say("cut %s" % tier[1])
    s.say("mov %s %s" % (tier[2], tier[3]))
    for i in range(asks):
        s.say("ask %s" % made[s.r.randrange(len(made))])
        if i % (asks // 8) == 0:
            s.say("oth mov %s %s" % (tier[4 + (i % 9)], tier[1] if i % 2 else root))
    s.say("snd")
    s.say("ok")
    s.say("ask %s" % tier[2])


def build(fam, r, small=True):
    s = Site(r)
    if fam == "plain":
        _plain(s)
    elif fam == "chain":
        _chain(s)
    elif fam == "spread":
        _spread(s)
    elif fam == "refuse":
        _refuse(s)
    elif fam == "cancel":
        _cancel(s)
    elif fam == "remote":
        _remote(s)
    elif fam == "stale":
        _stale(s)
    elif fam == "count":
        _count(s)
    elif fam == "order":
        _order(s)
    elif fam == "idle":
        _idle(s)
    elif fam == "wide":
        _wide(s, 4000 if small else 20000)
    elif fam == "deep":
        _deep(s, 3000 if small else 12000, 1500 if small else 8000)
    return s.lines


def programs(seed, per):
    """Every graded program: `per` of each small family and BIG of each scale family."""
    out = []
    for fam, big in FAMILIES:
        for i in range(BIG if big else per):
            r = random.Random("%s|%s|%d" % (seed, fam, i))
            out.append((fam, "%s-%d" % (fam, i), build(fam, r, small=False)))
    return out
