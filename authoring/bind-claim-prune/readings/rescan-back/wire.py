from bind import hold, place, prune, pull, want


class Link:
    """One pass down the input list, then placement, then the prune.

    The take list and the table are different kinds of thing and are kept apart here: a take
    is printed when it happens and is never unsaid, while the table loses a part the moment a
    unit off the input list takes its key. Which is why the prune cannot run until the list is
    finished, and why the list cannot be settled by asking what the prune would keep.
    """

    def __init__(self, job):
        self.job = job
        self.keep = hold.Keep()
        self.names = want.Names()
        self.seen = 0
        self.set = {}
        self.live = set()
        self.lit = set()

    def load(self, uname, direct):
        u = self.job.units.get(uname)
        if u is None or uname in self.keep.loaded:
            return
        self.keep.loaded.add(uname)
        self.seen += 1
        ins, out = hold.load(self.keep, u, direct)
        for p in out:
            want.leave(self.names, p)
        for p in ins:
            want.enter(self.names, self.job, p)
        want.spares(self.names, u, self.seen)


def run(job, items):
    st = Link(job)
    job.link = st
    behind = []
    for kind, what in items:
        if kind == "u":
            before = len(st.keep.parts)
            st.load(what, True)
            if len(st.keep.parts) <= before:
                for old in behind:
                    pull.run(st, old)
        elif kind == "b":
            behind.append((what,))
            pull.run(st, (what,))
        else:
            behind.append(what)
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
