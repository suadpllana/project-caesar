"""A correct store built on blocks rather than claims.

Every item is one entry per block, so nothing has to be split, and the free map is indexed
by a dictionary from run length to starts. The other four modules hand their work to this
one. It settles the same contract by a different route.
"""
import bisect


class Span:
    __slots__ = ("at", "wide", "hits", "by", "live")

    def __init__(self, at, wide):
        self.at = at
        self.wide = wide
        self.hits = {}
        self.by = {}
        self.live = 0


class Item:
    __slots__ = ("line", "name", "cell")

    def __init__(self, line, name):
        self.line = line
        self.name = name
        self.cell = []


class World:
    def __init__(self, blocks):
        self.blocks = blocks
        self.at2w = {}
        self.starts = []
        self.w2at = {}
        self.widths = []
        self.spare = 0
        self.lines = {}
        self.ref = {}
        self.excl = {}
        self.own = {}
        if blocks:
            self._park(0, blocks)
            self.spare = blocks

    # --- free map -----------------------------------------------------------------

    def _park(self, at, wide):
        self.at2w[at] = wide
        bisect.insort(self.starts, at)
        seat = self.w2at.get(wide)
        if seat is None:
            self.w2at[wide] = [at]
            bisect.insort(self.widths, wide)
        else:
            bisect.insort(seat, at)

    def _unpark(self, at):
        wide = self.at2w.pop(at)
        self.starts.pop(bisect.bisect_left(self.starts, at))
        seat = self.w2at[wide]
        seat.pop(bisect.bisect_left(seat, at))
        if not seat:
            del self.w2at[wide]
            self.widths.pop(bisect.bisect_left(self.widths, wide))
        return wide

    def give(self, at, wide):
        self.spare += wide
        tail = at + wide
        if tail in self.at2w:
            wide += self._unpark(tail)
        i = bisect.bisect_left(self.starts, at)
        if i:
            head = self.starts[i - 1]
            if head + self.at2w[head] == at:
                wide += self._unpark(head)
                at = head
        self._park(at, wide)

    def take(self, want):
        if want > self.spare:
            return None
        self.spare -= want
        out = []
        left = want
        while left:
            i = bisect.bisect_left(self.widths, left)
            if i < len(self.widths):
                wide = self.widths[i]
                at = self.w2at[wide][0]
                self._unpark(at)
                out.append((at, left))
                if wide > left:
                    self._park(at + left, wide - left)
                left = 0
            else:
                wide = self.widths[-1]
                at = self.w2at[wide][0]
                self._unpark(at)
                out.append((at, wide))
                left -= wide
        return out

    # --- block references ---------------------------------------------------------

    def hook(self, line, sp, off):
        sp.live += 1
        sp.hits[off] = sp.hits.get(off, 0) + 1
        seen = sp.by.get(line, 0)
        sp.by[line] = seen + 1
        if seen:
            return
        self.ref[line] += sp.wide
        self.own[line].add(sp)
        if len(sp.by) == 1:
            self.excl[line] += sp.wide
        elif len(sp.by) == 2:
            for other in sp.by:
                if other != line:
                    self.excl[other] -= sp.wide

    def unhook(self, line, sp, off):
        sp.live -= 1
        left = sp.hits[off] - 1
        if left:
            sp.hits[off] = left
        else:
            del sp.hits[off]
        seat = sp.by[line] - 1
        if seat:
            sp.by[line] = seat
            return
        del sp.by[line]
        self.ref[line] -= sp.wide
        self.own[line].discard(sp)
        if not sp.by:
            self.excl[line] -= sp.wide
        elif len(sp.by) == 1:
            for other in sp.by:
                self.excl[other] += sp.wide

    def bury(self, seen):
        rel = 0
        for sp in seen:
            if not sp.live:
                self.give(sp.at, sp.wide)
                rel += sp.wide
        return rel

    def strip(self, it, lo, hi, seen):
        for i in range(lo, hi):
            cell = it.cell[i]
            if cell is None:
                continue
            self.unhook(it.line, cell[0], cell[1])
            seen.add(cell[0])
            it.cell[i] = None

    def doomed(self, it, spots):
        count = {}
        for i in spots:
            cell = it.cell[i]
            if cell is not None:
                count[cell[0]] = count.get(cell[0], 0) + 1
        return sum(sp.wide for sp, k in count.items() if k == sp.live)

    def fill(self, it, spots, parts):
        made = []
        for at, wide in parts:
            made.append(Span(at, wide))
        k = 0
        off = 0
        for i in spots:
            sp = made[k]
            it.cell[i] = (sp, off)
            self.hook(it.line, sp, off)
            off += 1
            if off == sp.wide:
                k += 1
                off = 0


def _spots(runs):
    out = []
    for lo, hi in runs:
        out.extend(range(lo, hi))
    return out


def _runs(lo, hi, flags):
    """Maximal stretches of [lo, hi) whose flag is False."""
    out = []
    open_at = None
    for i in range(lo, hi):
        if flags[i - lo]:
            if open_at is not None:
                out.append((open_at, i))
                open_at = None
        elif open_at is None:
            open_at = i
    if open_at is not None:
        out.append((open_at, hi))
    return out


def _item(w, ln, nm):
    kit = w.lines.get(ln)
    if kit is None:
        return None
    return kit.get(nm)


def do_write(w, ln, nm, at, n):
    kit = w.lines.get(ln)
    if kit is None:
        return "nosuch"
    if n < 1:
        return "range"
    it = kit.get(nm)
    size = len(it.cell) if it is not None else 0
    if at > size:
        return "gap"
    end = at + n
    over = end if end < size else size
    flags = []
    for i in range(at, over):
        sp, off = it.cell[i]
        flags.append(sp.hits[off] == 1)
    gaps = _runs(at, over, flags)
    kept = (over - at) - sum(b - a for a, b in gaps)
    if over < end:
        if gaps and gaps[-1][1] == over:
            gaps[-1] = (gaps[-1][0], end)
        else:
            gaps.append((over, end))
    if not gaps:
        return (0, kept, 0)
    need = n - kept
    if it is not None:
        spots = [i for i in _spots(gaps) if i < size]
        if w.spare + w.doomed(it, spots) < need:
            return "noroom"
    elif w.spare < need:
        return "noroom"
    if it is None:
        it = Item(ln, nm)
        kit[nm] = it
    seen = set()
    for lo, hi in gaps:
        if lo < size:
            w.strip(it, lo, hi if hi < size else size, seen)
    rel = w.bury(seen)
    if end > size:
        it.cell.extend([None] * (end - size))
    w.fill(it, _spots(gaps), w.take(need))
    return (need, kept, rel)


def do_share(w, sl, sn, at, n, dl, dn, to):
    src = _item(w, sl, sn)
    if src is None:
        return "nosuch"
    if n < 1 or at + n > len(src.cell):
        return "range"
    kit = w.lines.get(dl)
    if kit is None:
        return "nosuch"
    dst = kit.get(dn)
    if dst is None:
        if to:
            return "gap"
    elif to > len(dst.cell):
        return "gap"
    grab = list(src.cell[at:at + n])
    if dst is None:
        dst = Item(dl, dn)
        kit[dn] = dst
    size = len(dst.cell)
    end = to + n
    seen = set()
    if to < size:
        w.strip(dst, to, end if end < size else size, seen)
    if end > size:
        dst.cell.extend([None] * (end - size))
    for k, cell in enumerate(grab):
        dst.cell[to + k] = cell
        w.hook(dst.line, cell[0], cell[1])
    return (w.bury(seen),)


def do_trim(w, ln, nm, n):
    it = _item(w, ln, nm)
    if it is None:
        return "nosuch"
    size = len(it.cell)
    if n > size:
        return "range"
    seen = set()
    w.strip(it, n, size, seen)
    del it.cell[n:]
    return (w.bury(seen),)


def do_erase(w, ln, nm):
    kit = w.lines.get(ln)
    if kit is None:
        return "nosuch"
    it = kit.get(nm)
    if it is None:
        return "nosuch"
    seen = set()
    w.strip(it, 0, len(it.cell), seen)
    del kit[nm]
    return (w.bury(seen),)


def do_vac(w, ln, nm):
    it = _item(w, ln, nm)
    if it is None:
        return "nosuch"
    size = len(it.cell)
    if not size:
        return (0, 0)
    if w.spare + w.doomed(it, range(size)) < size:
        return "noroom"
    seen = set()
    w.strip(it, 0, size, seen)
    rel = w.bury(seen)
    w.fill(it, list(range(size)), w.take(size))
    return (size, rel)


def do_chart(w, ln, nm):
    it = _item(w, ln, nm)
    if it is None:
        return "nosuch"
    bits = []
    for i, cell in enumerate(it.cell):
        sp, off = cell
        if bits:
            a, base, o, wide = bits[-1]
            if base == sp.at and o + wide == off and a + wide == i:
                bits[-1] = (a, base, o, wide + 1)
                continue
        bits.append((i, sp.at, off, 1))
    return (len(it.cell), bits)


def do_fresh(w, name):
    if name in w.lines:
        return "dup"
    w.lines[name] = {}
    w.ref[name] = 0
    w.excl[name] = 0
    w.own[name] = set()
    return None


def do_stamp(w, src, dst):
    if src not in w.lines:
        return "nosuch"
    if dst in w.lines:
        return "dup"
    do_fresh(w, dst)
    kit = w.lines[dst]
    for nm, it in w.lines[src].items():
        twin = Item(dst, nm)
        twin.cell = list(it.cell)
        for sp, off in twin.cell:
            w.hook(dst, sp, off)
        kit[nm] = twin
    return (len(kit),)


def do_drop(w, name):
    if name not in w.lines:
        return "nosuch"
    seen = set()
    for it in w.lines[name].values():
        w.strip(it, 0, len(it.cell), seen)
        it.cell = []
    rel = w.bury(seen)
    del w.lines[name]
    del w.ref[name]
    del w.excl[name]
    del w.own[name]
    return (rel,)


def do_charge(w, name):
    if name not in w.ref:
        return "nosuch"
    return (w.ref[name], w.excl[name])


def do_gone(w, names):
    want = set()
    for name in names:
        if name not in w.own:
            return "nosuch"
        want.add(name)
    rel = 0
    seen = set()
    for name in want:
        for sp in w.own[name]:
            if sp in seen:
                continue
            seen.add(sp)
            if want.issuperset(sp.by):
                rel += sp.wide
    return (rel,)


def do_stat(w):
    if not w.widths:
        return (0, 0, 0)
    return (w.spare, len(w.at2w), w.widths[-1])

def setup(st):
    st.w = World(st.blocks)


def stat(st):
    return do_stat(st.w)
