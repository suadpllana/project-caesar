"""A from-scratch engine for the same contract, written to be obviously right, never fast.

Nothing here is shared with the reference under solution/ or with the sealed model. Every
question is answered by looking at the slots: which blocks of an extent are pointed at, which
volumes are on it, what dies, what is rewritten. The `own` query is answered by copying the
whole store, dropping the volume, running the same epilogue with its printing turned off, and
reporting how much smaller the store came out - the definition itself rather than a derivation
of it. That makes this the differential check for both the reference and the sealed model, and
the naive family the execution limit is aimed at.
"""
import copy


class B:
    def __init__(self):
        self.v = {}          # volume -> {file: [slot]}, slot None or (eid, blk)
        self.siz = {}        # extent id -> size
        self.nid = 1
        self.out = []
        self.quiet = False

    # --- reading the state by walking it ------------------------------------------

    def hits(self, eid):
        """Every pointer at extent eid, as (volume, file, index, block)."""
        out = []
        for vn, fs in self.v.items():
            for fn, s in fs.items():
                for i, p in enumerate(s):
                    if p is not None and p[0] == eid:
                        out.append((vn, fn, i, p[1]))
        return out

    def occ(self, eid):
        return len({h[3] for h in self.hits(eid)})

    def vols(self, eid):
        return {h[0] for h in self.hits(eid)}

    def held(self):
        return sum(self.siz.values())

    def say(self, line):
        if not self.quiet:
            self.out.append(line)

    # --- the ops ------------------------------------------------------------------

    def wr(self, vn, fn, lo, hi):
        eid = self.nid
        self.nid += 1
        self.siz[eid] = hi - lo + 1
        self.say("put %d %d" % (eid, hi - lo + 1))
        for i in range(hi - lo + 1):
            self.v[vn][fn][lo + i] = (eid, i)
        self.after()

    def cp(self, vn, fn, lo, hi, wn, gn, off):
        src = list(self.v[vn][fn][lo:hi + 1])
        for i, p in enumerate(src):
            self.v[wn][gn][off + i] = p
        self.after()

    def tr(self, vn, fn, lo, hi):
        for i in range(lo, hi + 1):
            self.v[vn][fn][i] = None
        self.after()

    def sn(self, vn, wn):
        self.v[wn] = {fn: list(s) for fn, s in self.v[vn].items()}
        self.after()

    def rm(self, vn):
        del self.v[vn]
        self.after()

    def bulk(self, vn, fn, n, w):
        self.v[vn][fn] = [None] * (n * w)
        for i in range(n):
            eid = self.nid
            self.nid += 1
            self.siz[eid] = w
            for j in range(w):
                self.v[vn][fn][i * w + j] = (eid, j)
        self.after()

    # --- the epilogue: every extent is looked at, every time ----------------------

    def after(self):
        for eid in sorted(self.siz):
            if not self.hits(eid):
                del self.siz[eid]
                self.say("gone %d" % eid)
        for eid in sorted(self.siz):
            on = self.hits(eid)
            if len({h[0] for h in on}) != 1:
                continue
            blks = sorted({h[3] for h in on})
            if 2 * len(blks) >= self.siz[eid]:
                continue
            at = {b: k for k, b in enumerate(blks)}
            new = self.nid
            self.nid += 1
            self.siz[new] = len(blks)
            for vn, fn, i, b in on:
                self.v[vn][fn][i] = (new, at[b])
            del self.siz[eid]
            self.say("pack %d %d %d" % (eid, new, len(blks)))

    # --- the queries --------------------------------------------------------------

    def use(self, vn):
        n = 0
        for eid in self.siz:
            if vn in self.vols(eid):
                n += self.siz[eid]
        return n

    def own(self, vn):
        was = self.held()
        shadow = B()
        shadow.v = copy.deepcopy(self.v)
        shadow.siz = dict(self.siz)
        shadow.nid = self.nid
        shadow.quiet = True
        shadow.rm(vn)
        return was - shadow.held()

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
            self.v[a[1]] = {}
        elif op == "fil":
            self.v[a[1]][a[2]] = [None] * int(a[3])
        elif op == "bulk":
            self.bulk(a[1], a[2], int(a[3]), int(a[4]))
        elif op == "use":
            self.say("use %s %d" % (a[1], self.use(a[1])))
        elif op == "own":
            self.say("own %s %d" % (a[1], self.own(a[1])))
        elif op == "tot":
            self.say("tot %d" % self.held())
        elif op == "at":
            p = self.v[a[1]][a[2]][int(a[3])]
            if p is None:
                self.say("at %s %s %s none" % (a[1], a[2], a[3]))
            else:
                self.say("at %s %s %s %d %d" % (a[1], a[2], a[3], p[0], p[1]))
        else:
            raise ValueError(op)


def expect(lines):
    b = B()
    for line in lines:
        a = tuple(line.split())
        if a:
            b.ex(a)
    return b.out
