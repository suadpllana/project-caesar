"""An independent implementation of the pane's frame rules, used to say what is correct.

Written apart from the reference and decomposed differently on purpose. The reference keeps a
segment tree over the groups whose nodes compose three numbers each. This one keeps the groups
that remember at least one row - the breakpoints - in a sorted list, and three Fenwick trees over
the groups: what each group adds with no height carried into it, how many of its rows wait for a
carried height, and, at each breakpoint, the carried height it hands on times the rows that take
it. A group's top is those sums plus one partial stretch; an offset is found by first choosing the
stretch between two breakpoints and then descending the first two trees together at that
stretch's carried height. Inside a group heights are recomputed from its rows on demand. The only
thing the two share is the rule set below, so agreement between them is evidence about the rules.

The rules, in the order a frame applies them:

  1  a header is as tall as it declares; a row the pane remembers is as tall as its real height;
     any other row is as tall as the nearest remembered row above it in the flow, headers not
     counting, or as the document estimate when there is none
  2  the pinned group is the last one whose header top has reached the offset, and the band is
     the smaller of its header height and the distance from the offset to the next header
  3  the anchor line is the offset plus the band; the held item is the one lying across it, the
     last item when the line falls on the total, and when that is a row the pane does not
     remember, the nearest header or remembered row above it; the gap is its top less the line
  4  an item is visible when it starts before the bottom edge and ends after the top edge; the
     window adds the overscan on both sides and is clipped to the flow
  5  the event moves the offset or the viewport, the offset is clamped, and the foot flag is
     read from what the movement left behind
  6  the hold is taken before the edit and carried through it: when the edit removes it, it
     becomes the first surviving item after it, or the last surviving item before it when none
     follows, with the gap moved by the difference of the two tops as they stood before; after
     the edit the offset is clamped again; a deleted row is forgotten, an inserted one is new
  7  a pass lays out the band and the window from the offset it starts with; every row of the
     window counts as seen by that pass; then, in item order, a row the pane does not remember
     at that moment is measured, and when the memory is full the pane first forgets the row it
     saw least recently, the one nearer the start of the flow when two were last seen by the
     same pass; then the offset goes to the foot when the flag is set, and otherwise to the held
     item's top less the gap less that pass's band, clamped
  8  the frame settles when a pass measured nothing and left the offset alone, and stops at the
     pass cap however unsettled it is
  9  the line reports the offset the frame ended at, the last pass's pinned group, band and
     window, the hold as it stood after the edit, the rows this frame measured and the passes
"""

import heapq
from bisect import bisect_left, bisect_right, insort

MIX = 2654435761


class Tree:
    """A Fenwick tree; `walk` descends it, optionally beside a second tree scaled by c."""

    def __init__(self, n):
        self.n = n
        self.a = [0] * (n + 1)
        top = 1
        while top * 2 <= n:
            top *= 2
        self.top = top

    def bump(self, i, d):
        i += 1
        while i <= self.n:
            self.a[i] += d
            i += i & -i

    def upto(self, i):
        """Sum of slots 0..i-1."""
        s = 0
        while i > 0:
            s += self.a[i]
            i -= i & -i
        return s

    def span(self, i, j):
        """Sum of slots i..j inclusive (0 when j < i)."""
        if j < i:
            return 0
        return self.upto(j + 1) - self.upto(i)


def walk(one, two, c, target):
    """Largest G with one.upto(G) + c * two.upto(G) <= target (both trees the same size)."""
    pos = 0
    left = target
    bit = one.top
    while bit:
        nxt = pos + bit
        if nxt <= one.n:
            v = one.a[nxt] + c * two.a[nxt]
            if v <= left:
                pos = nxt
                left -= v
        bit >>= 1
    return pos


def walk_one(tree, target):
    """Largest G with tree.upto(G) <= target."""
    pos = 0
    left = target
    bit = tree.top
    while bit:
        nxt = pos + bit
        if nxt <= tree.n and tree.a[nxt] <= left:
            pos = nxt
            left -= tree.a[nxt]
        bit >>= 1
    return pos


class Doc:
    def __init__(self, cfg, decls):
        self.vh, self.over, self.pcap, self.est, self.cap = cfg
        self.gs = []
        self.where = {}
        nxt = 0
        for gid, hh, lo, hi, n in decls:
            self.where[gid] = len(self.gs)
            self.gs.append({"gid": gid, "hh": hh, "lo": lo, "hi": hi,
                            "rows": list(range(nxt, nxt + n))})
            nxt += n
        self.nxt = nxt
        n = len(self.gs)
        self.n = n
        self.mem = {}                 # rid -> [stamp, key, group index]
        self.heap = []
        self.measured = 0
        self.xs = [0] * n             # what a group adds with nothing carried in
        self.us = [0] * n             # its rows waiting for a carried height
        self.os = [0] * n             # the height it hands on (0: it remembers nothing)
        self.ws = {}                  # breakpoint -> weight stored in fw
        self.bps = []
        self.fx = Tree(n)
        self.fu = Tree(n)
        self.fw = Tree(n)
        self.fi = Tree(n)
        for gi, g in enumerate(self.gs):
            self.fi.bump(gi, 1 + len(g["rows"]))
            self.xs[gi] = g["hh"]
            self.us[gi] = len(g["rows"])
            self.fx.bump(gi, self.xs[gi])
            self.fu.bump(gi, self.us[gi])

    # --- rule 1: heights ----------------------------------------------------------------

    def real(self, gi, rid):
        g = self.gs[gi]
        return g["lo"] + (rid * MIX) % (g["hi"] - g["lo"] + 1)

    def row_heights(self, gi, carried):
        out = []
        c = carried
        for rid in self.gs[gi]["rows"]:
            if rid in self.mem:
                c = self.real(gi, rid)
            out.append(c)
        return out

    def summarise(self, gi):
        rows = self.gs[gi]["rows"]
        waiting = 0
        while waiting < len(rows) and rows[waiting] not in self.mem:
            waiting += 1
        added = self.gs[gi]["hh"]
        hands = 0
        c = 0
        for rid in rows[waiting:]:
            if rid in self.mem:
                c = self.real(gi, rid)
            added += c
        if waiting < len(rows):
            hands = c
        return added, waiting, hands

    # --- the breakpoint sums ------------------------------------------------------------

    def _next_bp(self, b):
        k = bisect_right(self.bps, b)
        return self.bps[k] if k < len(self.bps) else self.n - 1

    def _prev_bp(self, gi):
        k = bisect_left(self.bps, gi)
        return self.bps[k - 1] if k > 0 else -1

    def _weigh(self, b):
        if b < 0:
            return
        new = self.os[b] * self.fu.span(b + 1, self._next_bp(b)) if self.os[b] else 0
        old = self.ws.get(b, 0)
        if new != old:
            self.fw.bump(b, new - old)
        if new:
            self.ws[b] = new
        else:
            self.ws.pop(b, None)

    def refresh(self, gi):
        added, waiting, hands = self.summarise(gi)
        if added != self.xs[gi]:
            self.fx.bump(gi, added - self.xs[gi])
            self.xs[gi] = added
        if waiting != self.us[gi]:
            self.fu.bump(gi, waiting - self.us[gi])
            self.us[gi] = waiting
        was = self.os[gi]
        self.os[gi] = hands
        if was and not hands:
            self.bps.pop(bisect_left(self.bps, gi))
        elif hands and not was:
            insort(self.bps, gi)
        self._weigh(gi)
        self._weigh(self._prev_bp(gi))

    def top_of_group(self, gi):
        """(sum of the groups before gi, the height carried into gi)."""
        k = bisect_left(self.bps, gi)
        if k == 0:
            return self.fx.upto(gi) + self.est * self.fu.upto(gi), self.est
        first = self.bps[0]
        last = self.bps[k - 1]
        y = self.fx.upto(gi)
        y += self.est * self.fu.upto(first + 1)
        y += self.fw.upto(last)
        y += self.os[last] * self.fu.span(last + 1, gi - 1)
        return y, self.os[last]

    def total(self):
        return self.top_of_group(self.n)[0]

    def group_at(self, y):
        """Index of the group whose span holds offset y (y below the total)."""
        # Stretches start at group 0 and just after each breakpoint; take the last one whose
        # first group starts at or before y. Index -1 stands for the stretch starting at 0.
        lo, hi = -1, len(self.bps) - 1
        while lo < hi:
            mid = (lo + hi + 1) // 2
            s = self.bps[mid] + 1
            if s < self.n and self.top_of_group(s)[0] <= y:
                lo = mid
            else:
                hi = mid - 1
        s = 0 if lo < 0 else self.bps[lo] + 1
        ys, c = self.top_of_group(s)
        target = y - ys + self.fx.upto(s) + c * self.fu.upto(s)
        return walk(self.fx, self.fu, c, target)

    # --- items --------------------------------------------------------------------------

    def count(self):
        return self.fi.upto(self.n)

    def place(self, i):
        gi = walk_one(self.fi, i)
        if gi >= self.n:
            gi = self.n - 1
        return gi, i - self.fi.upto(gi) - 1

    def top(self, i):
        gi, k = self.place(i)
        y, c = self.top_of_group(gi)
        if k < 0:
            return y
        return y + self.gs[gi]["hh"] + sum(self.row_heights(gi, c)[:k])

    def at(self, y):
        if y >= self.total():
            return self.count() - 1
        gi = self.group_at(y)
        y0, c = self.top_of_group(gi)
        base = self.fi.upto(gi)
        run = y0 + self.gs[gi]["hh"]
        if y < run:
            return base
        hs = self.row_heights(gi, c)
        for k, h in enumerate(hs):
            if y < run + h:
                return base + 1 + k
            run += h
        return base + len(hs)

    def item(self, i):
        gi, k = self.place(i)
        if k < 0:
            return gi, None
        return gi, self.gs[gi]["rows"][k]

    def key(self, i):
        gi, rid = self.item(i)
        return "H%d" % self.gs[gi]["gid"] if rid is None else "R%d" % rid

    # --- rule 7: the memory -------------------------------------------------------------

    def forget_one(self):
        while True:
            stamp, key, rid = heapq.heappop(self.heap)
            slot = self.mem.get(rid)
            if slot is not None and slot[0] == stamp and slot[1] == key:
                del self.mem[rid]
                return slot[2]

    def sweep(self, w0, w1, stamp):
        touched = set()
        for i in range(w0, w1 + 1):
            gi, rid = self.item(i)
            if rid is not None and rid in self.mem:
                self.mem[rid][0] = stamp
                self.mem[rid][1] = i
                heapq.heappush(self.heap, (stamp, i, rid))
        got = 0
        for i in range(w0, w1 + 1):
            gi, rid = self.item(i)
            if rid is None or rid in self.mem:
                continue
            if len(self.mem) >= self.cap:
                touched.add(self.forget_one())
            self.mem[rid] = [stamp, i, gi]
            heapq.heappush(self.heap, (stamp, i, rid))
            touched.add(gi)
            got += 1
        self.measured += got
        for gi in sorted(touched):
            self.refresh(gi)
        if len(self.heap) > 8 * self.cap + 8192:
            self.heap = [(s[0], s[1], rid) for rid, s in self.mem.items()]
            heapq.heapify(self.heap)
        return got


# --- rules 2 and 3 --------------------------------------------------------------------

def band_of(doc, off):
    gi = doc.n - 1 if off >= doc.total() else doc.group_at(off)
    nxt = doc.top_of_group(gi + 1)[0] if gi + 1 < doc.n else doc.total()
    return gi, min(doc.gs[gi]["hh"], nxt - off)


def hold_of(doc, line):
    i = doc.at(line)
    while True:
        gi, rid = doc.item(i)
        if rid is None or rid in doc.mem:
            break
        i -= 1
    return i, doc.key(i), doc.top(i) - line


# --- rule 4 -----------------------------------------------------------------------------

def window_of(doc, off, vh, over):
    lo = doc.at(off) - over
    hi = doc.at(off + vh - 1) + over
    return max(0, lo), min(doc.count() - 1, hi)


# --- rule 5 -----------------------------------------------------------------------------

def foot_of(total, vh):
    return max(0, total - vh)


def clamped(off, total, vh):
    return min(max(off, 0), foot_of(total, vh))


# --- rule 6 -----------------------------------------------------------------------------

def carry(doc, held, ev):
    kind, gid, pos, n = ev
    i, _key, gap = held
    gi = doc.where[gid]
    g = doc.gs[gi]
    first = doc.fi.upto(gi) + 1 + pos
    if kind == "ins":
        g["rows"][pos:pos] = list(range(doc.nxt, doc.nxt + n))
        doc.nxt += n
        doc.fi.bump(gi, n)
        doc.refresh(gi)
        if i >= first:
            i += n
        return i, doc.key(i), gap
    if first <= i < first + n:
        if first + n < doc.count():
            gap += doc.top(first + n) - doc.top(i)
            nh = first
        else:
            gap += doc.top(first - 1) - doc.top(i)
            nh = first - 1
    else:
        nh = i - n if i >= first + n else i
    for rid in g["rows"][pos:pos + n]:
        doc.mem.pop(rid, None)
    del g["rows"][pos:pos + n]
    doc.fi.bump(gi, -n)
    doc.refresh(gi)
    return nh, doc.key(nh), gap


# --- the frame ------------------------------------------------------------------------

def expect(lines):
    cfg, decls, evs = read("\n".join(lines))
    doc = Doc(cfg, decls)
    vh = doc.vh
    off = 0
    stamp = 0
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
            off = clamped(off, doc.total(), vh)

        gi = b = w0 = w1 = 0
        got_all = 0
        p = 0
        while p < doc.pcap:
            p += 1
            stamp += 1
            gi, b = band_of(doc, off)
            w0, w1 = window_of(doc, off, vh, doc.over)
            got = doc.sweep(w0, w1, stamp)
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
    out.append("end s %d t %d m %d" % (off, doc.total(), doc.measured))
    return out


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
            cfg = tuple(vals)
        elif head == "g":
            decls.append(tuple(vals))
        elif head in ("scroll", "go", "size"):
            evs.append((head, vals[0], 0, 0))
        elif head in ("ins", "del"):
            evs.append((head, vals[0], vals[1], vals[2]))
        else:
            raise ValueError("unknown line %r" % head)
    return cfg, decls, evs
