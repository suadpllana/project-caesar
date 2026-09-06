"""An independent reading of the residency contract.

Written from the frozen contract in `test_outputs.py`, not from `hst/`. It shares no code
with the host: declarations are parallel dictionaries rather than objects, a view is rebuilt
by concatenation at every lookup rather than cached, and the kept set is found by relaxing a
claim graph until it stops growing rather than by a worklist. Where this file and the host
agree, two implementations of the same prose agree; where they differ, one of them is wrong
and the enumerated cases say which.
"""

TAGS = ("pv", "rq", "wk", "nd", "st")


def parse(path):
    dec = {}
    evs = []
    cur = None
    with open(path, "r", encoding="ascii") as fh:
        for ln in fh:
            w = ln.split()
            if not w:
                continue
            if w[0] == "pk":
                cur = w[1]
                dec[cur] = {t: [] for t in TAGS}
            elif w[0] in TAGS:
                dec[cur][w[0]].append(w[1])
            elif w[0] == "ld":
                evs.append(("ld", w[1], [w[2]]))
            elif w[0] == "us":
                evs.append(("us", w[1], list(w[2:])))
            elif w[0] == "dp":
                evs.append(("dp", w[1], []))
    return dec, evs


class World(object):
    def __init__(self, dec):
        self.dec = dec
        self.pk = {}
        self.fix = {}
        self.rec = {}
        self.stand = {}
        self.opn = []
        self.made = 0

    def alive(self, n):
        return n in self.pk

    def view(self, n):
        raw = [n]
        raw.extend(self.fix[n])
        raw.extend(self.opn)
        seq = []
        for m in raw:
            if self.alive(m) and m not in seq:
                seq.append(m)
        return seq

    def find(self, n, nm):
        for m in self.view(n):
            if nm in self.dec[self.pk[m]]["pv"]:
                return m
        return 0

    def use(self, n, nm):
        d = self.dec[self.pk[n]]
        if nm not in d["rq"] and nm not in d["wk"]:
            return ("bad", 0)
        if nm not in self.rec[n]:
            self.rec[n][nm] = self.find(n, nm)
        g = self.rec[n][nm]
        if g:
            return ("res", g)
        return ("none", 0)

    def needs_order(self, p):
        seq = []
        q = list(self.dec[p]["nd"])
        while q:
            x = q.pop(0)
            m = self.stand.get(x)
            if m is None or m in seq:
                continue
            seq.append(m)
            q.extend(self.dec[self.pk[m]]["nd"])
        return seq

    def bring(self, p, md, made):
        if p in self.stand:
            n = self.stand[p]
            if md == "open" and n not in self.opn:
                self.opn.append(n)
            return
        for d in self.dec[p]["nd"]:
            self.bring(d, "own", made)
        fix = self.needs_order(p)
        self.made += 1
        n = self.made
        self.pk[n] = p
        self.fix[n] = fix
        self.rec[n] = {}
        self.stand[p] = n
        made.append(n)
        if md == "open":
            self.opn.append(n)
        for s in self.dec[p]["st"]:
            self.use(n, s)

    def claims(self, n):
        out = []
        for nm in self.dec[self.pk[n]]["rq"]:
            g = self.rec[n][nm] if nm in self.rec[n] else self.find(n, nm)
            if g and self.alive(g):
                out.append(g)
        return out

    def kept(self):
        keep = []
        for n in self.stand.values():
            if self.alive(n) and n not in keep:
                keep.append(n)
        grew = True
        while grew:
            grew = False
            for n in list(keep):
                for g in self.claims(n):
                    if g not in keep:
                        keep.append(g)
                        grew = True
        return keep

    def sweep(self):
        keep = self.kept()
        gone = [n for n in sorted(self.pk) if n not in keep]
        for n in gone:
            del self.pk[n]
            del self.fix[n]
            del self.rec[n]
        return sorted(gone, reverse=True)

    def drop(self, p):
        n = self.stand.get(p)
        if n is None:
            return 0
        del self.stand[p]
        if n in self.opn:
            self.opn.remove(n)
        return n


def ledger(name, path):
    dec, evs = parse(path)
    w = World(dec)
    rows = []
    step = 0
    for kind, who, arg in evs:
        step += 1
        if kind == "ld":
            made = []
            w.bring(who, arg[0], made)
            rows.append("%s %d ld %s %s" % (name, step, who,
                                            " ".join(str(n) for n in made) if made else "-"))
        elif kind == "us":
            n = w.stand.get(who)
            if n is None or not w.alive(n):
                rows.append("%s %d us %s %s off" % (name, step, who, arg[0]))
            else:
                for nm in arg:
                    kind2, got = w.use(n, nm)
                    if kind2 != "res":
                        rows.append("%s %d us %s %s %s" % (name, step, w.pk[n], nm, kind2))
                        break
                    rows.append("%s %d us %s %s %d" % (name, step, w.pk[n], nm, got))
                    if not w.alive(got):
                        break
                    n = got
        else:
            n = w.drop(who)
            rows.append("%s %d dp %s %s" % (name, step, who, n if n else "bad"))
        gone = w.sweep()
        rows.append("%s %d rl %s" % (name, step, " ".join(str(n) for n in gone) if gone else "-"))
    return rows
