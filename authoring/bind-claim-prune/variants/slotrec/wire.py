from bind import hold, place, prune, pull, want


class Link:
    def __init__(self, job):
        self.job = job
        self.keep = hold.Keep()
        self.names = want.Names()
        self.order = 0
        self.set = {}
        self.live = set()
        self.lit = set()

    def load(self, who, direct):
        u = self.job.units.get(who)
        if u is None or who in self.keep.loaded:
            return
        self.keep.loaded.add(who)
        self.order += 1
        took, gone = hold.load(self.keep, u, direct)
        for p in gone:
            want.leave(self.names, p)
        for p in took:
            want.enter(self.names, self.job, p)
        want.spares(self.names, u, self.order)


def run(job, items):
    st = Link(job)
    job.link = st
    for kind, what in items:
        if kind == "u":
            st.load(what, True)
        elif kind == "b":
            pull.run(st, (what,))
        else:
            pull.run(st, what)
    st.set = place.run(st)
    st.live, st.lit = prune.run(st)


def at(job, nm):
    st = job.link
    if st is None:
        return None
    p = want.bind(st.names, nm)
    if p is not None:
        spot = (p.unit, p.idx)
        return spot if spot in st.live else None
    if nm in st.lit:
        who, size = st.set[nm]
        return ("spare", who, size)
    return None


def img(job):
    st = job.link
    if st is None:
        return (0, 0)
    return prune.count(st)
