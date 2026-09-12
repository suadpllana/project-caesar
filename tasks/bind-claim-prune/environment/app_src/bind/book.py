class Part:
    __slots__ = ("unit", "idx", "size", "key", "gives", "uses")

    def __init__(self, unit, idx, size, key):
        self.unit = unit
        self.idx = idx
        self.size = size
        self.key = key
        self.gives = []
        self.uses = []


class Unit:
    __slots__ = ("name", "parts", "spares")

    def __init__(self, name):
        self.name = name
        self.parts = []
        self.spares = []


class Job:
    def __init__(self):
        self.units = {}
        self.bundles = {}
        self.roots = []
        self.holds = []
        self.out = []
        self.link = None
        self.cur = None


def unit(job, name):
    u = Unit(name)
    job.units[name] = u
    job.cur = u
    return u


def part(job, size, key):
    u = job.cur
    p = Part(u.name, len(u.parts), size, None if key == "-" else key)
    u.parts.append(p)
    return p


def give(job, name, kind):
    job.cur.parts[-1].gives.append((name, kind == "s"))


def use(job, name, kind):
    job.cur.parts[-1].uses.append((name, kind == "s"))


def spare(job, name, size):
    job.cur.spares.append((name, int(size)))


def bundle(job, name, members):
    job.bundles[name] = tuple(members)


def root(job, name):
    job.roots.append(name)


def hold(job, uname, idx):
    job.holds.append((uname, idx))


def bulk(job, name, shape, n, arg):
    if shape != "chain":
        return
    mem = []
    for i in range(n):
        who = "%s%d" % (name, i)
        u = Unit(who)
        job.units[who] = u
        one = Part(who, 0, 8 + i % 5, None)
        one.gives.append(("%sx%d" % (name, i), True))
        far = i + arg
        if far < n:
            one.uses.append(("%sx%d" % (name, far), True))
        u.parts.append(one)
        two = Part(who, 1, 3 + i % 7, "%sk%d" % (name, i % 256))
        two.gives.append(("%sy%d" % (name, i), True))
        u.parts.append(two)
        mem.append(who)
    job.cur = None
    job.bundles[name] = tuple(mem)


def items(job, words):
    out = []
    i = 0
    while i < len(words):
        w = words[i]
        if w == "(":
            pack = []
            i += 1
            while i < len(words) and words[i] != ")":
                pack.append(words[i])
                i += 1
            out.append(("g", tuple(pack)))
        elif w in job.bundles:
            out.append(("b", w))
        else:
            out.append(("u", w))
        i += 1
    return tuple(out)
