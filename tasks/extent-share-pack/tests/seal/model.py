"""The sealed model: a second implementation of the same contract, written apart from the
reference under solution/ and from the engine the agent edits.

Where the reference hangs the bookkeeping off an extent object - a list of per-block tallies, a
dict of per-volume tallies, a set of the slots that point at it - this keeps everything in flat
dicts keyed by tuples, and rebuilds an extent's contribution to the three per-volume totals with
one generic pass over its volumes rather than by hand at every transition. The two agree on the
brute-force engine in authoring/, which answers the drop question by copying the store, dropping
the volume and measuring, instead of deriving anything.

What it computes, which is the frozen contract:

  * an extent takes its whole size for as long as any of its blocks is pointed at
  * it dies when no slot points into it, and the death is reported in ascending id
  * it is rewritten when slots of exactly one volume point into it and twice the blocks that
    are pointed at is less than its size; the surviving blocks keep their order and every
    pointer moves
  * use is the total size of the extents a volume is on, each counted once
  * own is how much smaller the store would be if that volume were dropped: the extents only it
    is on, plus, for each extent it shares with exactly one other volume, what the rewrite of
    that extent would give back once the other volume is the only one left
"""


class M:
    def __init__(self):
        self.slot = {}          # (vol, fil) -> list of None or (eid, blk)
        self.fils = {}          # vol -> list of file names, in creation order
        self.siz = {}           # eid -> size in blocks
        self.nid = 1
        self.out = []
        self.hot = set()
        self.held = 0
        self.use = {}
        self.solo = {}
        self.pair = {}
        self.bc = {}            # (eid, blk) -> pointers on that block
        self.vc = {}            # (eid, vol) -> pointers from that volume
        self.vbc = {}           # (eid, vol, blk) -> pointers from that volume on that block
        self.occ = {}           # eid -> blocks with at least one pointer
        self.vocc = {}          # (eid, vol) -> blocks that volume is on
        self.von = {}           # eid -> set of volumes on it
        self.ref = {}           # eid -> {(vol, fil, idx): blk}

    # --- the three per-volume totals ------------------------------------------------

    def parts(self, eid):
        """(volume, total, amount) triples for what eid currently contributes."""
        on = self.von[eid]
        siz = self.siz[eid]
        out = [(v, "use", siz) for v in on]
        if len(on) == 1:
            out.append((next(iter(on)), "solo", siz))
        elif len(on) == 2:
            a, b = tuple(on)
            for me, other in ((a, b), (b, a)):
                o = self.vocc[(eid, other)]
                out.append((me, "pair", siz - o if 2 * o < siz else 0))
        return out

    def shift(self, eid, sign):
        for v, which, amount in self.parts(eid):
            d = getattr(self, which)
            d[v] = d.get(v, 0) + sign * amount

    # --- pointers -------------------------------------------------------------------

    def attach(self, key, eid, blk):
        vol, fil, idx = key
        self.shift(eid, -1)
        self.slot[(vol, fil)][idx] = (eid, blk)
        self.bc[(eid, blk)] = self.bc.get((eid, blk), 0) + 1
        if self.bc[(eid, blk)] == 1:
            self.occ[eid] += 1
        self.vc[(eid, vol)] = self.vc.get((eid, vol), 0) + 1
        self.vbc[(eid, vol, blk)] = self.vbc.get((eid, vol, blk), 0) + 1
        if self.vbc[(eid, vol, blk)] == 1:
            self.vocc[(eid, vol)] = self.vocc.get((eid, vol), 0) + 1
        self.von[eid].add(vol)
        self.ref[eid][key] = blk
        self.shift(eid, 1)

    def detach(self, key):
        vol, fil, idx = key
        held = self.slot[(vol, fil)][idx]
        if held is None:
            return
        eid, blk = held
        self.shift(eid, -1)
        self.slot[(vol, fil)][idx] = None
        self.bc[(eid, blk)] -= 1
        if self.bc[(eid, blk)] == 0:
            del self.bc[(eid, blk)]
            self.occ[eid] -= 1
        self.vc[(eid, vol)] -= 1
        if self.vc[(eid, vol)] == 0:
            del self.vc[(eid, vol)]
            self.von[eid].discard(vol)
        self.vbc[(eid, vol, blk)] -= 1
        if self.vbc[(eid, vol, blk)] == 0:
            del self.vbc[(eid, vol, blk)]
            self.vocc[(eid, vol)] -= 1
            if self.vocc[(eid, vol)] == 0:
                del self.vocc[(eid, vol)]
        del self.ref[eid][key]
        self.shift(eid, 1)
        self.hot.add(eid)

    # --- extents --------------------------------------------------------------------

    def born(self, siz):
        eid = self.nid
        self.nid += 1
        self.siz[eid] = siz
        self.occ[eid] = 0
        self.von[eid] = set()
        self.ref[eid] = {}
        self.held += siz
        return eid

    def buried(self, eid):
        self.held -= self.siz[eid]
        for key in (eid,):
            del self.siz[key]
            del self.occ[key]
            del self.von[key]
            del self.ref[key]

    # --- the epilogue ---------------------------------------------------------------

    def after(self):
        hot = self.hot
        self.hot = set()
        for eid in sorted(hot):
            if eid in self.siz and self.occ[eid] == 0:
                self.buried(eid)
                self.out.append("gone %d" % eid)
        for eid in sorted(hot):
            if eid not in self.siz:
                continue
            if len(self.von[eid]) != 1 or 2 * self.occ[eid] >= self.siz[eid]:
                continue
            self.rewrite(eid)

    def rewrite(self, eid):
        vol = next(iter(self.von[eid]))
        at = {}
        for blk in range(self.siz[eid]):
            if (eid, blk) in self.bc:
                at[blk] = len(at)
        moving = list(self.ref[eid].items())
        new = self.born(len(at))
        for key, blk in moving:
            self.detach(key)
            self.attach(key, new, at[blk])
        self.hot.discard(new)
        self.buried(eid)
        self.out.append("pack %d %d %d" % (eid, new, self.siz[new]))

    # --- the ops --------------------------------------------------------------------

    def wr(self, vol, fil, lo, hi):
        eid = self.born(hi - lo + 1)
        self.out.append("put %d %d" % (eid, hi - lo + 1))
        for i in range(hi - lo + 1):
            key = (vol, fil, lo + i)
            self.detach(key)
            self.attach(key, eid, i)
        self.after()

    def cp(self, vol, fil, lo, hi, wvol, wfil, off):
        src = list(self.slot[(vol, fil)][lo:hi + 1])
        for i, held in enumerate(src):
            key = (wvol, wfil, off + i)
            self.detach(key)
            if held is not None:
                self.attach(key, held[0], held[1])
        self.after()

    def tr(self, vol, fil, lo, hi):
        for i in range(lo, hi + 1):
            self.detach((vol, fil, i))
        self.after()

    def sn(self, vol, wvol):
        self.fils[wvol] = list(self.fils[vol])
        for fil in self.fils[vol]:
            src = self.slot[(vol, fil)]
            self.slot[(wvol, fil)] = [None] * len(src)
            for i, held in enumerate(src):
                if held is not None:
                    self.attach((wvol, fil, i), held[0], held[1])
        self.after()

    def rm(self, vol):
        for fil in self.fils[vol]:
            src = self.slot[(vol, fil)]
            for i in range(len(src)):
                if src[i] is not None:
                    self.detach((vol, fil, i))
            del self.slot[(vol, fil)]
        del self.fils[vol]
        self.after()

    def bulk(self, vol, fil, n, w):
        self.fils[vol].append(fil)
        self.slot[(vol, fil)] = [None] * (n * w)
        for i in range(n):
            eid = self.born(w)
            for j in range(w):
                self.attach((vol, fil, i * w + j), eid, j)
        self.after()

    # --- the queries ----------------------------------------------------------------

    def ex(self, a):
        op = a[0]
        if op == "wr":
            self.wr(a[1], a[2], int(a[3]), int(a[4]))
        elif op == "cp":
            self.cp(a[1], a[2], int(a[3]), int(a[4]), a[5], a[6], int(a[7]))
        elif op == "tr":
            self.tr(a[1], a[2], int(a[3]), int(a[4]))
        elif op == "sn":
            self.sn(a[1], a[2])
        elif op == "rm":
            self.rm(a[1])
        elif op == "vol":
            self.fils[a[1]] = []
        elif op == "fil":
            self.fils[a[1]].append(a[2])
            self.slot[(a[1], a[2])] = [None] * int(a[3])
        elif op == "bulk":
            self.bulk(a[1], a[2], int(a[3]), int(a[4]))
        elif op == "use":
            self.out.append("use %s %d" % (a[1], self.use.get(a[1], 0)))
        elif op == "own":
            self.out.append("own %s %d" % (a[1], self.solo.get(a[1], 0) + self.pair.get(a[1], 0)))
        elif op == "tot":
            self.out.append("tot %d" % self.held)
        elif op == "at":
            held = self.slot[(a[1], a[2])][int(a[3])]
            if held is None:
                self.out.append("at %s %s %s none" % (a[1], a[2], a[3]))
            else:
                self.out.append("at %s %s %s %d %d" % (a[1], a[2], a[3], held[0], held[1]))
        else:
            raise ValueError(op)


def expect(lines):
    m = M()
    for line in lines:
        a = tuple(line.split())
        if a:
            m.ex(a)
    return m.out
