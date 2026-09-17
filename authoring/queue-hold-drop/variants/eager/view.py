from . import bind, lay, say

OVER = "_eager_over"


class Over:
    """The view as an overlay on the confirmed records: nothing is copied until it changes."""

    def __init__(self, base):
        self.base = base
        self.mine = {}
        self.dead = set()

    def touch(self, name):
        r = self.mine.get(name)
        if r is None:
            r = self.mine[name] = self.base[name].copy()
        return r

    def __contains__(self, name):
        if name in self.dead:
            return False
        return name in self.mine or name in self.base

    def get(self, name):
        if name in self.dead:
            return None
        r = self.mine.get(name)
        return r if r is not None else self.base.get(name)

    def __setitem__(self, name, r):
        self.dead.discard(name)
        self.mine[name] = r

    def __delitem__(self, name):
        self.mine.pop(name, None)
        self.dead.add(name)

    def __iter__(self):
        for name in self.base:
            if name not in self.dead:
                yield name
        for name in self.mine:
            if name not in self.base and name not in self.dead:
                yield name

    def __len__(self):
        return sum(1 for _ in self)

    def items(self):
        for name in self:
            yield name, self.get(name)


def fresh(st):
    setattr(st, OVER, None)


def push(st, c):
    over = getattr(st, OVER, None)
    if over is not None:
        lay.one(over, c)


def of(st):
    over = getattr(st, OVER, None)
    if over is None:
        over = Over(st.base)
        for c in st.q:
            lay.one(over, c)
        setattr(st, OVER, over)
    return over


def land(st, c):
    if c.kind == "new":
        bind.arrive(st, c.a)
    lay.one(st.base, c)
    fresh(st)


def ask(st, name):
    r = of(st).get(name)
    if r is None:
        st.out.append("none")
    else:
        st.out.append(say.shelf("rec", bind.show(st, name),
                                "-" if r.up is None else bind.show(st, r.up), r.fld))


def all(st):
    for name, r in of(st).items():
        st.out.append(say.shelf("row", bind.show(st, name),
                                "-" if r.up is None else bind.show(st, r.up), r.fld))
