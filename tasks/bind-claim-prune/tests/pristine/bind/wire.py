from bind import hold, place, prune, pull, want


class Link:
    def __init__(self, job):
        self.job = job
        self.keep = hold.Keep()
        self.names = want.Names()
        self.set = {}
        self.live = set()

    def load(self, uname):
        u = self.job.units.get(uname)
        if u is None or uname in self.keep.loaded:
            return
        self.keep.loaded.add(uname)
        ins, drop = hold.load(self.keep, u)
        for p in ins:
            want.enter(self.names, self.job, p)
        for p in drop:
            want.hint(self.names, p)
        want.spares(self.names, u)


def run(job, items):
    st = Link(job)
    job.link = st
    for kind, what in items:
        if kind == "u":
            st.load(what)
        elif kind == "b":
            pull.run(st, (what,))
        else:
            pull.run(st, what)
    st.set = place.run(st)
    st.live = prune.run(st)


def at(job, nm):
    st = job.link
    if st is None:
        return None
    p = want.bind(st.names, nm)
    if p is not None:
        return (p.unit, p.idx)
    if nm in st.set:
        who, size = st.set[nm]
        return ("spare", who, size)
    return None


def img(job):
    st = job.link
    if st is None:
        return (0, 0)
    return prune.count(st)
