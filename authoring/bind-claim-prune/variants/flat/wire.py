from bind import say

FIRM, SOFT, NEED, SPARE = 0, 1, 2, 3


class Link:
    def __init__(self, job):
        self.job = job
        self.loaded = set()
        self.parts = {}
        self.owner = {}
        self.stuck = set()
        self.name = {}
        self.want = set()
        self.order = 0
        self.set = {}
        self.live = set()
        self.lit = set()

    def row(self, nm):
        got = self.name.get(nm)
        if got is None:
            got = self.name[nm] = [[], [], 0, []]
        return got

    def touch(self, nm):
        got = self.name.get(nm)
        if got is None:
            return
        if not got[FIRM] and (got[NEED] > 0 or got[SPARE]):
            self.want.add(nm)
        else:
            self.want.discard(nm)

    def put(self, p):
        for nm, strong in p.gives:
            got = self.row(nm)
            if strong:
                if got[FIRM]:
                    say.dup(self.job, nm, p.unit)
                got[FIRM].append(p)
            else:
                got[SOFT].append(p)
            self.touch(nm)
        for nm, strong in p.uses:
            if strong:
                self.row(nm)[NEED] += 1
                self.touch(nm)

    def drop(self, p):
        for nm, strong in p.gives:
            got = self.row(nm)
            run = got[FIRM] if strong else got[SOFT]
            for i in range(len(run)):
                if run[i] is p:
                    del run[i]
                    break
            self.touch(nm)
        for nm, strong in p.uses:
            if strong:
                self.row(nm)[NEED] -= 1
                self.touch(nm)

    def load(self, who, direct):
        u = self.job.units.get(who)
        if u is None or who in self.loaded:
            return
        self.loaded.add(who)
        self.order += 1
        if direct:
            for p in u.parts:
                if p.key and p.key in self.owner and p.key not in self.stuck:
                    self.drop(self.parts.pop(self.owner.pop(p.key)))
        for p in u.parts:
            if p.key:
                if p.key in self.owner:
                    continue
                self.owner[p.key] = (p.unit, p.idx)
                if direct:
                    self.stuck.add(p.key)
            self.parts[(p.unit, p.idx)] = p
            self.put(p)
        for nm, size in u.spares:
            self.row(nm)[SPARE].append((size, self.order, u.name))
            self.touch(nm)

    def stands(self, nm):
        got = self.name.get(nm)
        if got is None:
            return None
        if got[FIRM]:
            return got[FIRM][0]
        if got[SOFT]:
            return got[SOFT][0]
        return None


def book(job, name):
    idx = {}
    mem = job.bundles.get(name, ())
    for pos, who in enumerate(mem):
        u = job.units.get(who)
        if u is None:
            continue
        for p in u.parts:
            for nm, strong in p.gives:
                if strong:
                    idx.setdefault(nm, set()).add(pos)
    return mem, dict((nm, sorted(v)) for nm, v in idx.items())


def scan(st, bundles):
    board = []
    for b in bundles:
        mem, idx = book(st.job, b)
        board.append([b, mem, idx, set(), {}])
    while True:
        moved = False
        for b, mem, idx, taken, cur in board:
            while True:
                best = None
                for nm in st.want:
                    run = idx.get(nm)
                    if not run:
                        continue
                    i = cur.get(nm, 0)
                    while i < len(run) and run[i] in taken:
                        i += 1
                    cur[nm] = i
                    if i < len(run) and (best is None or run[i] < best):
                        best = run[i]
                if best is None:
                    break
                taken.add(best)
                who = mem[best]
                if who in st.loaded:
                    continue
                say.take(st.job, b, who)
                st.load(who, False)
                moved = True
        if not moved:
            return


def settle(st):
    for nm, got in st.name.items():
        if not got[SPARE] or got[FIRM] or got[SOFT]:
            continue
        best = None
        for size, order, who in got[SPARE]:
            if best is None or size > best[0] or (size == best[0] and order < best[1]):
                best = (size, order, who)
        st.set[nm] = (best[2], best[0])


def sweep(st):
    stack = []
    for nm in st.job.roots:
        reach(st, nm, stack)
    for spot in st.job.holds:
        if spot in st.parts and spot not in st.live:
            st.live.add(spot)
            stack.append(st.parts[spot])
    while stack:
        p = stack.pop()
        for nm, strong in p.uses:
            if strong:
                reach(st, nm, stack)


def reach(st, nm, stack):
    p = st.stands(nm)
    if p is not None:
        spot = (p.unit, p.idx)
        if spot not in st.live:
            st.live.add(spot)
            stack.append(p)
    elif nm in st.set:
        st.lit.add(nm)


def run(job, items):
    st = Link(job)
    job.link = st
    for kind, what in items:
        if kind == "u":
            st.load(what, True)
        elif kind == "b":
            scan(st, (what,))
        else:
            scan(st, what)
    settle(st)
    sweep(st)


def at(job, nm):
    st = job.link
    if st is None:
        return None
    p = st.stands(nm)
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
    total = 0
    for spot in st.live:
        total += st.parts[spot].size
    for nm in st.lit:
        total += st.set[nm][1]
    return (len(st.live) + len(st.lit), total)
