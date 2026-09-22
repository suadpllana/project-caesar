class Bad(Exception):
    pass


class Cfg:
    __slots__ = ("budget",)

    def __init__(self, budget):
        self.budget = budget


class Goal:
    __slots__ = ("gid", "weight", "pre", "kind", "key", "val")

    def __init__(self, gid, weight, pre, kind, key, val):
        self.gid = gid
        self.weight = weight
        self.pre = pre
        self.kind = kind
        self.key = key
        self.val = val


class Bar:
    __slots__ = ("bid", "goal", "kind", "key")

    def __init__(self, bid, goal, kind, key):
        self.bid = bid
        self.goal = goal
        self.kind = kind
        self.key = key


class Ep:
    __slots__ = ("name", "goals", "bars", "steps")

    def __init__(self, name):
        self.name = name
        self.goals = []
        self.bars = []
        self.steps = []


GOAL_KINDS = {"at": 2, "up": 2, "off": 1}
BAR_KINDS = ("lost", "gain", "back")


def _ints(part, head):
    try:
        return [int(x) for x in part]
    except ValueError:
        raise Bad("%s takes numbers" % head)


def parse(text):
    cfg = None
    seeds = []
    eps = []
    step = None
    for raw in text.splitlines():
        part = raw.split()
        if not part:
            continue
        head = part[0]
        if head == "cfg":
            if cfg is not None:
                raise Bad("cfg given twice")
            if eps:
                raise Bad("cfg after ep")
            got = _ints(part[1:], "cfg")
            if len(got) != 1 or got[0] < 0:
                raise Bad("cfg takes one budget")
            cfg = Cfg(got[0])
        elif head == "rec":
            if cfg is None:
                raise Bad("rec before cfg")
            if eps:
                raise Bad("rec after ep")
            got = _ints(part[1:], "rec")
            if len(got) != 2 or got[0] < 0:
                raise Bad("rec takes a key and a value")
            seeds.append((got[0], got[1]))
        elif head == "ep":
            if cfg is None:
                raise Bad("ep before cfg")
            if len(part) != 2:
                raise Bad("ep takes one name")
            eps.append(Ep(part[1]))
            step = None
        elif head == "goal":
            if not eps:
                raise Bad("goal before ep")
            here = eps[-1]
            if here.steps:
                raise Bad("goal after step")
            if len(part) < 5:
                raise Bad("goal takes an id, a weight and a predicate")
            gid, weight, npre = _ints(part[1:4], "goal")
            if gid != len(here.goals):
                raise Bad("goal ids run up from zero")
            if weight < 1:
                raise Bad("goal takes a positive weight")
            if npre < 0 or len(part) < 4 + npre + 1:
                raise Bad("goal names fewer keys than it says")
            pre = _ints(part[4:4 + npre], "goal")
            for one in pre:
                if one < 0 or one >= gid:
                    raise Bad("a goal stands on goals before it")
            if len(set(pre)) != len(pre):
                raise Bad("a goal names a goal twice")
            rest = part[4 + npre:]
            kind = rest[0]
            if kind not in GOAL_KINDS:
                raise Bad("unknown goal predicate %s" % kind)
            args = _ints(rest[1:], "goal")
            if len(args) != GOAL_KINDS[kind]:
                raise Bad("%s takes %d numbers" % (kind, GOAL_KINDS[kind]))
            if args[0] < 0:
                raise Bad("goal takes a key")
            val = args[1] if len(args) > 1 else 0
            here.goals.append(Goal(gid, weight, tuple(pre), kind, args[0], val))
        elif head == "bar":
            if not eps:
                raise Bad("bar before ep")
            here = eps[-1]
            if here.steps:
                raise Bad("bar after step")
            if len(part) != 5:
                raise Bad("bar takes an id, a goal, a kind and a key")
            bid, goal = _ints(part[1:3], "bar")
            kind = part[3]
            key = _ints(part[4:5], "bar")[0]
            if bid != len(here.bars):
                raise Bad("bar ids run up from zero")
            if goal < 0 or goal >= len(here.goals):
                raise Bad("bar names a goal that is not there")
            if kind not in BAR_KINDS:
                raise Bad("unknown bar kind %s" % kind)
            if key < 0:
                raise Bad("bar takes a key")
            here.bars.append(Bar(bid, goal, kind, key))
        elif head == "step":
            if not eps:
                raise Bad("step before ep")
            if not eps[-1].goals:
                raise Bad("step before any goal")
            if step is not None:
                raise Bad("step before the one before it ended")
            step = []
            eps[-1].steps.append(step)
        elif head in ("put", "cut"):
            if step is None:
                raise Bad("%s outside a step" % head)
            want = 2 if head == "put" else 1
            got = _ints(part[1:], head)
            if len(got) != want or got[0] < 0:
                raise Bad("%s takes %d numbers" % (head, want))
            step.append((head, got[0], got[1] if want == 2 else 0))
        elif head in ("ok", "err"):
            if step is None:
                raise Bad("%s outside a step" % head)
            if len(part) != 1:
                raise Bad("%s takes nothing" % head)
            eps[-1].steps[-1] = (tuple(step), head == "ok")
            step = None
        else:
            raise Bad("unknown op %s" % head)
    if cfg is None:
        raise Bad("no cfg")
    if step is not None:
        raise Bad("a step never ended")
    for one in eps:
        if not one.goals:
            raise Bad("ep with no goal")
    return cfg, seeds, eps
