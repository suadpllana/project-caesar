from bind import say


class Scan:
    """One bundle, indexed once by name to the members that give it, in member order.

    A member gives a fixed set of names whatever the table happens to hold, so the index is
    built once and never rebuilt. What changes is which names are wanted, and a cursor per
    name walks past the members already taken, so the member a restart would have found is
    the smallest live position over the names wanted at that moment.
    """

    def __init__(self, job, name):
        self.name = name
        self.mem = job.bundles.get(name, ())
        self.taken = set()
        self.idx = {}
        for pos, who in enumerate(self.mem):
            u = job.units.get(who)
            if u is None:
                continue
            for p in u.parts:
                for nm, strong in p.gives:
                    if strong:
                        row = self.idx.get(nm)
                        if row is None:
                            self.idx[nm] = [pos]
                        elif row[-1] != pos:
                            row.append(pos)
        self.cur = {}


def pick(st, sc):
    """The position a restart from the first member would stop at, or None."""
    best = None
    for nm in st.names.want:
        row = sc.idx.get(nm)
        if not row:
            continue
        at = sc.cur.get(nm, 0)
        while at < len(row) and row[at] in sc.taken:
            at += 1
        sc.cur[nm] = at
        if at < len(row) and (best is None or row[at] < best):
            best = row[at]
    return best


def run(st, bundles):
    """Scan a bundle, or a group of them, until a whole pass takes nothing."""
    scans = [Scan(st.job, b) for b in bundles]
    while True:
        moved = False
        for sc in scans:
            while True:
                pos = pick(st, sc)
                if pos is None:
                    break
                sc.taken.add(pos)
                who = sc.mem[pos]
                if who in st.keep.loaded:
                    continue
                say.take(st.job, sc.name, who)
                st.load(who, False)
                moved = True
        return
