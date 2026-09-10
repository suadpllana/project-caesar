"""An independent settlement of the same contract, written against blocks rather than claims.

The reference keeps an item as a list of claims and splices them; this keeps an item as one
entry per block, which makes every rule a question about a block and removes the splitting
logic entirely. The free map is indexed by a dictionary of length to starts instead of a
sorted list of pairs, the in-place test reads a per-span occupancy count instead of walking
the other claims, and the map is printed by running the blocks together. The charges are
still carried forward, because recounting them is the thing the execution limit forbids.

Only the trace is contract. Where the two disagree, one of them is wrong.
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


def _bad(cmd, who, code):
    if who is None:
        return "%s err=%s" % (cmd, code)
    return "%s %s err=%s" % (cmd, who, code)


def _pair(word):
    ln, _, nm = word.partition("/")
    return ln, nm


def step(w, parts, acc):
    cmd = parts[0]
    if cmd == "n":
        who = parts[1]
        res = do_fresh(w, who)
        acc.append(_bad(cmd, who, res) if res else "n %s" % who)
    elif cmd == "p":
        who = parts[2]
        res = do_stamp(w, parts[1], who)
        acc.append(_bad(cmd, who, res) if isinstance(res, str)
                   else "p %s items=%d" % (who, res[0]))
    elif cmd == "d":
        who = parts[1]
        res = do_drop(w, who)
        acc.append(_bad(cmd, who, res) if isinstance(res, str)
                   else "d %s rel=%d" % (who, res[0]))
    elif cmd == "w":
        who = parts[1]
        ln, nm = _pair(who)
        res = do_write(w, ln, nm, int(parts[2]), int(parts[3]))
        acc.append(_bad(cmd, who, res) if isinstance(res, str)
                   else "w %s new=%d keep=%d rel=%d" % (who, res[0], res[1], res[2]))
    elif cmd == "s":
        who = parts[4]
        sl, sn = _pair(parts[1])
        dl, dn = _pair(who)
        res = do_share(w, sl, sn, int(parts[2]), int(parts[3]), dl, dn, int(parts[5]))
        acc.append(_bad(cmd, who, res) if isinstance(res, str)
                   else "s %s rel=%d" % (who, res[0]))
    elif cmd == "t":
        who = parts[1]
        ln, nm = _pair(who)
        res = do_trim(w, ln, nm, int(parts[2]))
        acc.append(_bad(cmd, who, res) if isinstance(res, str)
                   else "t %s rel=%d" % (who, res[0]))
    elif cmd == "x":
        who = parts[1]
        ln, nm = _pair(who)
        res = do_erase(w, ln, nm)
        acc.append(_bad(cmd, who, res) if isinstance(res, str)
                   else "x %s rel=%d" % (who, res[0]))
    elif cmd == "v":
        who = parts[1]
        ln, nm = _pair(who)
        res = do_vac(w, ln, nm)
        acc.append(_bad(cmd, who, res) if isinstance(res, str)
                   else "v %s new=%d rel=%d" % (who, res[0], res[1]))
    elif cmd == "c":
        who = parts[1]
        res = do_charge(w, who)
        acc.append(_bad(cmd, who, res) if isinstance(res, str)
                   else "c %s ref=%d excl=%d" % (who, res[0], res[1]))
    elif cmd == "g":
        who = parts[1]
        res = do_gone(w, who.split(","))
        acc.append(_bad(cmd, who, res) if isinstance(res, str)
                   else "g %s rel=%d" % (who, res[0]))
    elif cmd == "f":
        res = do_stat(w)
        acc.append("f free=%d runs=%d big=%d" % res)
    elif cmd == "m":
        who = parts[1]
        ln, nm = _pair(who)
        res = do_chart(w, ln, nm)
        acc.append(_bad(cmd, who, res) if isinstance(res, str)
                   else _chartline(who, res[0], res[1]))
    else:
        acc.append(_bad(cmd, None, "form"))


def _chartline(who, size, bits):
    head = "m %s size=%d" % (who, size)
    if not bits:
        return head
    return head + " " + " ".join("%d:%d+%d:%d" % b for b in bits)


def expect(raw):
    rows = []
    for row in raw:
        row = row.split("#")[0].strip()
        if row:
            rows.append(row)
    blocks = int(rows[0].split()[1])
    w = World(blocks)
    acc = ["dev %d" % blocks]
    for row in rows[1:]:
        step(w, tuple(row.split()), acc)
    return acc
