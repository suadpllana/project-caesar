"""An independent implementation of the pane's frame rules, used to say what is correct.

Written apart from the reference and decomposed differently on purpose. The reference keeps the
flow partitioned the way the document is - a Fenwick over group heights, a Fenwick over group
item counts, a Fenwick inside each group - and moves those sums incrementally as rows are
measured and edited. This one flattens the whole flow into one array of item heights with a
block decomposition over it, rebuilt outright whenever the document changes shape, and answers
every search by walking blocks and then walking inside one. The only thing the two share is the
rule set below; nothing about the structure, the search or the edit handling carries over, so
agreement between them is evidence about the rules rather than about a shared implementation.

The rules, in the order a frame applies them:

  1  a header is as tall as it declares; a row is as tall as its group estimates until it has
     been measured, and as tall as its real height afterwards
  2  the pinned group is the last one whose header top has reached the offset, and the band is
     the smaller of its header height and the distance from the offset to the next header
  3  the anchor line is the offset plus the band; the held item is the one lying across it, the
     last item when the line falls on the total; the gap is the held item's top less the line
  4  an item is visible when it starts before the bottom edge and ends after the top edge; the
     window adds the overscan on both sides and is clipped to the flow
  5  the event moves the offset or the viewport, the offset is clamped, and the foot flag is
     read from what the movement left behind
  6  the hold is taken before the edit and carried through it: when the edit removes it, it
     becomes the first surviving item after it, or the last surviving item before it when none
     follows, with the gap moved by the difference of the two tops as they stood before
  7  a settle pass lays out the band and the window from the offset it starts with, measures
     what the window has not measured, then puts the offset at the foot when the flag is set
     and otherwise at the held item's top less the gap less that pass's band, clamped
  8  the frame settles when a pass measured nothing and left the offset alone, and stops at the
     pass cap however unsettled it is
  9  the line reports the offset the frame ended at, the last pass's pinned group, band and
     window, the hold as it stood after the edit, the rows this frame measured and the passes
"""

MIX = 2654435761


class Doc:
    """The document as a flat item array with block sums over it."""

    __slots__ = ("gs", "seen", "nxt", "meas", "kind", "owner", "rid", "hs",
                 "bsz", "bsum", "gpos")

    def __init__(self, decls):
        self.gs = []
        self.seen = {}
        self.nxt = 0
        self.meas = 0
        for gid, hh, est, lo, hi, n in decls:
            rows = list(range(self.nxt, self.nxt + n))
            self.nxt += n
            self.gs.append({"gid": gid, "hh": hh, "est": est, "lo": lo, "hi": hi,
                            "rows": rows})
        self.flatten()

    # --- rule 1: what an item is worth ------------------------------------------------

    def real(self, g, rid):
        return g["lo"] + (rid * MIX) % (g["hi"] - g["lo"] + 1)

    def rowh(self, g, rid):
        h = self.seen.get(rid)
        return g["est"] if h is None else h

    # --- the flat view, rebuilt whenever the document changes shape -------------------

    def flatten(self):
        kind = []
        owner = []
        rid = []
        hs = []
        gpos = []
        for gi, g in enumerate(self.gs):
            gpos.append(len(kind))
            kind.append(0)
            owner.append(gi)
            rid.append(-1)
            hs.append(g["hh"])
            for r in g["rows"]:
                kind.append(1)
                owner.append(gi)
                rid.append(r)
                hs.append(self.rowh(g, r))
        self.kind = kind
        self.owner = owner
        self.rid = rid
        self.hs = hs
        self.gpos = gpos
        n = len(hs)
        b = 1
        while b * b < n:
            b += 1
        self.bsz = max(b, 1)
        self.blocks()

    def blocks(self):
        bsz = self.bsz
        sums = []
        run = 0
        for i, h in enumerate(self.hs):
            run += h
            if (i + 1) % bsz == 0:
                sums.append(run)
                run = 0
        if run or not sums:
            sums.append(run)
        self.bsum = sums

    def bump(self, i, d):
        self.hs[i] += d
        self.bsum[i // self.bsz] += d

    # --- searches ---------------------------------------------------------------------

    def count(self):
        return len(self.hs)

    def total(self):
        return sum(self.bsum)

    def top(self, i):
        y = 0
        b = i // self.bsz
        for j in range(b):
            y += self.bsum[j]
        for k in range(b * self.bsz, i):
            y += self.hs[k]
        return y

    def at(self, y):
        run = 0
        b = 0
        while b < len(self.bsum) and run + self.bsum[b] <= y:
            run += self.bsum[b]
            b += 1
        i = b * self.bsz
        n = len(self.hs)
        while i < n:
            if run + self.hs[i] > y:
                return i
            run += self.hs[i]
            i += 1
        return n - 1

    def gtop(self, gi):
        return self.top(self.gpos[gi])

    def key(self, i):
        g = self.gs[self.owner[i]]
        if self.kind[i] == 0:
            return "H%d" % g["gid"]
        return "R%d" % self.rid[i]

    def mark(self, i):
        if self.kind[i] == 0:
            return 0
        r = self.rid[i]
        if r in self.seen:
            return 0
        g = self.gs[self.owner[i]]
        self.seen[r] = self.real(g, r)
        self.meas += 1
        self.bump(i, self.seen[r] - g["est"])
        return 1

    # --- edits ------------------------------------------------------------------------

    def gfind(self, gid):
        for gi, g in enumerate(self.gs):
            if g["gid"] == gid:
                return gi
        return -1

    def insert(self, gid, pos, n):
        g = self.gs[self.gfind(gid)]
        fresh = list(range(self.nxt, self.nxt + n))
        self.nxt += n
        g["rows"][pos:pos] = fresh
        self.flatten()

    def remove(self, gid, pos, n):
        g = self.gs[self.gfind(gid)]
        del g["rows"][pos:pos + n]
        self.flatten()


# --- rule 2 and 3 ---------------------------------------------------------------------

def band_of(doc, off):
    gi = 0
    lo = 0
    hi = len(doc.gs) - 1
    while lo <= hi:
        mid = (lo + hi) // 2
        if doc.gtop(mid) <= off:
            gi = mid
            lo = mid + 1
        else:
            hi = mid - 1
    nxt = doc.gtop(gi + 1) if gi + 1 < len(doc.gs) else doc.total()
    return gi, min(doc.gs[gi]["hh"], nxt - off)


def hold_of(doc, line):
    i = doc.at(line)
    return i, doc.key(i), doc.top(i) - line


# --- rule 4 ---------------------------------------------------------------------------

def window_of(doc, off, vh, over):
    lo = doc.at(off) - over
    hi = doc.at(off + vh - 1) + over
    return max(0, lo), min(doc.count() - 1, hi)


# --- rule 5 ---------------------------------------------------------------------------

def foot_of(total, vh):
    return max(0, total - vh)


def clamped(off, total, vh):
    return min(max(off, 0), foot_of(total, vh))


# --- the frame ------------------------------------------------------------------------

def expect(lines):
    cfg, decls, evs = read("\n".join(lines))
    vh, over, pcap = cfg
    doc = Doc(decls)
    off = 0
    out = []
    for n, ev in enumerate(evs):
        kind = ev[0]
        if kind == "scroll":
            off += ev[1]
        elif kind == "go":
            off = ev[1]
        elif kind == "size":
            vh = ev[1]
        off = clamped(off, doc.total(), vh)
        foot = off == foot_of(doc.total(), vh)

        _gi, b = band_of(doc, off)
        hi, hkey, hgap = hold_of(doc, off + b)
        if kind in ("ins", "del"):
            hi, hkey, hgap = carry(doc, (hi, hkey, hgap), ev)

        gi = b = w0 = w1 = 0
        got_all = 0
        p = 0
        while p < pcap:
            p += 1
            gi, b = band_of(doc, off)
            w0, w1 = window_of(doc, off, vh, over)
            got = 0
            for i in range(w0, w1 + 1):
                got += doc.mark(i)
            got_all += got
            if foot:
                nxt = foot_of(doc.total(), vh)
            else:
                nxt = clamped(doc.top(hi) - hgap - b, doc.total(), vh)
            if got == 0 and nxt == off:
                break
            off = nxt
        out.append("f %d s %d g %d b %d w %d %d h %s %d m %d p %d"
                   % (n, off, doc.gs[gi]["gid"], b, w0, w1, hkey, hgap, got_all, p))
    out.append("end s %d t %d m %d" % (off, doc.total(), doc.meas))
    return out


# --- rule 6 ---------------------------------------------------------------------------

def carry(doc, held, ev):
    kind, gid, pos, n = ev
    i, _key, gap = held
    gi = doc.gfind(gid)
    first = doc.gpos[gi] + 1 + pos
    if kind == "ins":
        doc.insert(gid, pos, n)
        if i >= first:
            i += n
        return i, doc.key(i), gap
    if first <= i < first + n:
        after = first + n
        if after < doc.count():
            gap += doc.top(after) - doc.top(i)
            doc.remove(gid, pos, n)
            return first, doc.key(first), gap
        back = first - 1
        gap += doc.top(back) - doc.top(i)
        doc.remove(gid, pos, n)
        return back, doc.key(back), gap
    doc.remove(gid, pos, n)
    if i >= first + n:
        i -= n
    return i, doc.key(i), gap


# --- the same grammar, read independently ---------------------------------------------

def read(text):
    cfg = None
    decls = []
    evs = []
    for raw in text.splitlines():
        bits = raw.split()
        if not bits:
            continue
        head = bits[0]
        vals = [int(b) for b in bits[1:]]
        if head == "cfg":
            cfg = (vals[0], vals[1], vals[2])
        elif head == "g":
            decls.append(tuple(vals))
        elif head in ("scroll", "go", "size"):
            evs.append((head, vals[0], 0, 0))
        elif head in ("ins", "del"):
            evs.append((head, vals[0], vals[1], vals[2]))
        else:
            raise ValueError("unknown line %r" % head)
    return cfg, decls, evs
