"""The contract, transcribed as literally as possible. Authoring only; never ships.

Every quantity is recomputed from scratch from the flat list of items whenever it is needed,
so this is O(items) per question and only usable on small documents. It is the third opinion:
the reference (solution/) and the sealed model (tests/seal/model.py) are each checked against
it on thousands of small documents before they are trusted with each other on large ones.
"""
MIX = 2654435761


def parse(lines):
    cfg = None
    decls = []
    evs = []
    for raw in lines:
        bits = raw.split()
        if not bits:
            continue
        head, vals = bits[0], [int(b) for b in bits[1:]]
        if head == "cfg":
            cfg = tuple(vals)
        elif head == "g":
            decls.append(tuple(vals))
        elif head in ("scroll", "go", "size"):
            evs.append((head, vals[0], 0, 0))
        else:
            evs.append((head, vals[0], vals[1], vals[2]))
    return cfg, decls, evs


class Pane:
    def __init__(self, cfg, decls):
        self.V, self.K, self.P, self.E, self.C = cfg
        self.gs = []
        self.nxt = 0
        for gid, hh, lo, hi, n in decls:
            self.gs.append({"gid": gid, "hh": hh, "lo": lo, "hi": hi,
                            "rows": list(range(self.nxt, self.nxt + n))})
            self.nxt += n
        self.rem = {}          # rid -> (pass stamp, item index at that pass)
        self.passno = 0
        self.meas = 0
        self.off = 0

    # --- the flow ------------------------------------------------------------------
    def items(self):
        out = []
        for gi, g in enumerate(self.gs):
            out.append(("H", gi, None))
            for rid in g["rows"]:
                out.append(("R", gi, rid))
        return out

    def real(self, gi, rid):
        g = self.gs[gi]
        return g["lo"] + (rid * MIX) % (g["hi"] - g["lo"] + 1)

    def heights(self, its):
        hs = []
        carry = self.E
        for kind, gi, rid in its:
            if kind == "H":
                hs.append(self.gs[gi]["hh"])
            elif rid in self.rem:
                h = self.real(gi, rid)
                hs.append(h)
                carry = h
            else:
                hs.append(carry)
        return hs

    def geo(self):
        its = self.items()
        hs = self.heights(its)
        tops = []
        y = 0
        for h in hs:
            tops.append(y)
            y += h
        return its, hs, tops, y

    def foot(self, total):
        return max(0, total - self.V)

    def clamp(self, off, total):
        return min(max(off, 0), self.foot(total))

    def at(self, tops, hs, total, y):
        if y >= total:
            return len(tops) - 1
        for i in range(len(tops)):
            if tops[i] <= y < tops[i] + hs[i]:
                return i
        return len(tops) - 1

    def band(self, off):
        its, hs, tops, total = self.geo()
        heads = [i for i, it in enumerate(its) if it[0] == "H"]
        pin = 0
        for j, i in enumerate(heads):
            if tops[i] <= off:
                pin = j
        nxt = tops[heads[pin + 1]] if pin + 1 < len(heads) else total
        return pin, min(self.gs[pin]["hh"], nxt - off)

    def window(self, off):
        its, hs, tops, total = self.geo()
        vis = [i for i in range(len(its)) if tops[i] < off + self.V and tops[i] + hs[i] > off]
        assert vis, "a pass began with nothing visible"
        return max(0, vis[0] - self.K), min(len(its) - 1, vis[-1] + self.K)

    def take(self, line):
        its, hs, tops, total = self.geo()
        i = self.at(tops, hs, total, line)
        while its[i][0] == "R" and its[i][2] not in self.rem:
            i -= 1
        return i, tops[i] - line

    def key(self, i):
        kind, gi, rid = self.items()[i]
        return "H%d" % self.gs[gi]["gid"] if kind == "H" else "R%d" % rid

    def top(self, i):
        return self.geo()[2][i]

    def remember(self, rid, idx):
        if len(self.rem) >= self.C:
            victim = min(self.rem, key=lambda r: self.rem[r])
            del self.rem[victim]
        self.rem[rid] = (self.passno, idx)
        self.meas += 1

    def frame(self, ev):
        kind = ev[0]
        total = self.geo()[3]
        if kind == "scroll":
            self.off += ev[1]
        elif kind == "go":
            self.off = ev[1]
        elif kind == "size":
            self.V = ev[1]
        self.off = self.clamp(self.off, total)
        following = self.off == self.foot(total)

        _pin, b = self.band(self.off)
        hi, gap = self.take(self.off + b)
        if kind in ("ins", "del"):
            hi, gap = self.edit(ev, hi, gap)
            self.off = self.clamp(self.off, self.geo()[3])
        hkey = self.key(hi)

        m = 0
        p = 0
        pin = b = w0 = w1 = 0
        while p < self.P:
            p += 1
            self.passno += 1
            pin, b = self.band(self.off)
            w0, w1 = self.window(self.off)
            its = self.items()
            for i in range(w0, w1 + 1):
                if its[i][0] == "R" and its[i][2] in self.rem:
                    self.rem[its[i][2]] = (self.passno, i)
            got = 0
            for i in range(w0, w1 + 1):
                if its[i][0] == "R" and its[i][2] not in self.rem:
                    self.remember(its[i][2], i)
                    got += 1
            m += got
            total = self.geo()[3]
            if following:
                nxt = self.foot(total)
            else:
                nxt = self.clamp(self.top(hi) - gap - b, total)
            if got == 0 and nxt == self.off:
                break
            self.off = nxt
        return "f %%d s %d g %d b %d w %d %d h %s %d m %d p %d" % (
            self.off, self.gs[pin]["gid"], b, w0, w1, hkey, gap, m, p)

    def edit(self, ev, hi, gap):
        kind, gid, pos, n = ev
        gi = [g["gid"] for g in self.gs].index(gid)
        g = self.gs[gi]
        first = sum(1 + len(x["rows"]) for x in self.gs[:gi]) + 1 + pos
        if kind == "ins":
            g["rows"][pos:pos] = list(range(self.nxt, self.nxt + n))
            self.nxt += n
            return (hi + n if hi >= first else hi), gap
        tops = self.geo()[2]
        count = len(tops)
        if first <= hi < first + n:
            if first + n < count:
                gap += tops[first + n] - tops[hi]
                nh = first
            else:
                gap += tops[first - 1] - tops[hi]
                nh = first - 1
        else:
            nh = hi - n if hi >= first + n else hi
        for rid in g["rows"][pos:pos + n]:
            self.rem.pop(rid, None)
        del g["rows"][pos:pos + n]
        return nh, gap


def expect(lines):
    cfg, decls, evs = parse(lines)
    pane = Pane(cfg, decls)
    out = []
    for n, ev in enumerate(evs):
        out.append(pane.frame(ev) % n)
    out.append("end s %d t %d m %d" % (pane.off, pane.geo()[3], pane.meas))
    return out
