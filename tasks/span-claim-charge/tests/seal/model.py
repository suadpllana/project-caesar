"""An independent settlement of the same contract, written against blocks rather than claims.

The reference keeps an item as a list of claims and splices them; this keeps an item as one
entry per block, which makes every rule a question about a block and removes the splitting
logic entirely. The free map is indexed by a dictionary of length to starts instead of a
sorted list of pairs, the in-place test reads a per-block occupancy count instead of walking
the other claims, and the map is printed by running the blocks together. The charges are
still carried forward, because recounting them is the thing the execution limit forbids.

The family questions are settled from a different derivation than the reference's. Every
line carries a stamp path - the serials of the lines above it - so the paths of the lines
standing on a span sort in tree order. The deepest line every standing line descends from is
the longest common prefix of the first and last of those paths, shortened past any line that
has since been dropped, and what a family stands on follows from an identity over that
order: the lines whose families reach a span are the union of the root paths of its standing
lines, and that union is the sum of the paths minus the sum of the paths of the common
ancestors of neighbouring pairs. Both numbers are then sums over the lines of a family. The
reference keeps a count per ancestor on each span instead and moves totals up the tree when a
line goes; where the two disagree, one of them is wrong.

Only the trace is contract.
"""
import bisect


class Span:
    __slots__ = ("at", "wide", "hits", "by", "live", "paths", "lca")

    def __init__(self, at, wide):
        self.at = at
        self.wide = wide
        self.hits = {}
        self.by = {}
        self.live = 0
        self.paths = []
        self.lca = None


class Item:
    __slots__ = ("line", "name", "cell")

    def __init__(self, line, name):
        self.line = line
        self.name = name
        self.cell = []


class Line:
    __slots__ = ("name", "path", "kit", "alive", "ref", "excl", "own", "lcat", "pair")

    def __init__(self, name, path):
        self.name = name
        self.path = path
        self.kit = {}
        self.alive = True
        self.ref = 0
        self.excl = 0
        self.own = set()
        self.lcat = 0
        self.pair = 0


class World:
    def __init__(self, blocks):
        self.blocks = blocks
        self.at2w = {}
        self.starts = []
        self.w2at = {}
        self.widths = []
        self.spare = 0
        self.lines = {}
        self.bypath = {}
        self.serial = 0
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

    # --- the stamp tree -----------------------------------------------------------

    def mint(self, name, up):
        self.serial += 1
        path = (self.serial,) if up is None else up.path + (self.serial,)
        line = Line(name, path)
        self.lines[name] = line
        self.bypath[path] = line
        return line

    def deepest(self, path):
        """The deepest line still standing whose path is a prefix of `path`."""
        for k in range(len(path), 0, -1):
            line = self.bypath.get(path[:k])
            if line is not None and line.alive:
                return line
        return None

    def meet(self, pa, pb):
        """The deepest standing line both paths descend from."""
        k = 0
        n = min(len(pa), len(pb))
        while k < n and pa[k] == pb[k]:
            k += 1
        return self.deepest(pa[:k]) if k else None

    def _relca(self, sp):
        new = self.meet(sp.paths[0], sp.paths[-1]) if sp.paths else None
        if new is sp.lca:
            return
        if sp.lca is not None:
            old = self.deepest(sp.lca.path)
            if old is not None:
                old.lcat -= sp.wide
        if new is not None:
            new.lcat += sp.wide
        sp.lca = new

    def _pair(self, pa, pb, delta):
        z = self.meet(pa, pb)
        if z is not None:
            z.pair += delta

    def _enter(self, sp, line):
        paths = sp.paths
        j = bisect.bisect_left(paths, line.path)
        if 0 < j < len(paths):
            self._pair(paths[j - 1], paths[j], -sp.wide)
        paths.insert(j, line.path)
        if j:
            self._pair(paths[j - 1], line.path, sp.wide)
        if j + 1 < len(paths):
            self._pair(line.path, paths[j + 1], sp.wide)
        self._relca(sp)

    def _leave(self, sp, line):
        paths = sp.paths
        j = bisect.bisect_left(paths, line.path)
        if j:
            self._pair(paths[j - 1], line.path, -sp.wide)
        if j + 1 < len(paths):
            self._pair(line.path, paths[j + 1], -sp.wide)
        paths.pop(j)
        if 0 < j < len(paths):
            self._pair(paths[j - 1], paths[j], sp.wide)
        self._relca(sp)

    def retire(self, line):
        """A dropped line hands what it carried to the deepest line above it still standing."""
        up = self.deepest(line.path[:-1]) if len(line.path) > 1 else None
        if up is not None:
            up.lcat += line.lcat
            up.pair += line.pair
        line.lcat = 0
        line.pair = 0
        line.alive = False
        del self.lines[line.name]

    def kin(self, line):
        n = len(line.path)
        return [z for z in self.lines.values() if z.path[:n] == line.path]

    # --- block references ---------------------------------------------------------

    def hook(self, line, sp, off):
        sp.live += 1
        sp.hits[off] = sp.hits.get(off, 0) + 1
        seen = sp.by.get(line, 0)
        sp.by[line] = seen + 1
        if seen:
            return
        line.ref += sp.wide
        line.own.add(sp)
        if len(sp.by) == 1:
            line.excl += sp.wide
        elif len(sp.by) == 2:
            for other in sp.by:
                if other is not line:
                    other.excl -= sp.wide
        self._enter(sp, line)

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
        line.ref -= sp.wide
        line.own.discard(sp)
        if not sp.by:
            line.excl -= sp.wide
        elif len(sp.by) == 1:
            for other in sp.by:
                other.excl += sp.wide
        self._leave(sp, line)

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
    line = w.lines.get(ln)
    if line is None:
        return None
    return line.kit.get(nm)


def do_fresh(w, name):
    if name in w.lines:
        return "dup"
    w.mint(name, None)
    return None


def do_stamp(w, src, dst):
    origin = w.lines.get(src)
    if origin is None:
        return "nosuch"
    if dst in w.lines:
        return "dup"
    line = w.mint(dst, origin)
    for nm, it in origin.kit.items():
        twin = Item(line, nm)
        twin.cell = list(it.cell)
        line.kit[nm] = twin
        for cell in twin.cell:
            if cell is not None:
                w.hook(line, cell[0], cell[1])
    return (len(line.kit),)


def do_drop(w, name):
    line = w.lines.get(name)
    if line is None:
        return "nosuch"
    seen = set()
    for it in line.kit.values():
        w.strip(it, 0, len(it.cell), seen)
    rel = w.bury(seen)
    w.retire(line)
    return (rel,)


def do_write(w, ln, nm, at, n):
    line = w.lines.get(ln)
    if line is None:
        return "nosuch"
    if n < 1:
        return "range"
    it = line.kit.get(nm)
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
        it = Item(line, nm)
        line.kit[nm] = it
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
    line = w.lines.get(dl)
    if line is None:
        return "nosuch"
    dst = line.kit.get(dn)
    if dst is None:
        if to:
            return "gap"
    elif to > len(dst.cell):
        return "gap"
    grab = list(src.cell[at:at + n])
    if dst is None:
        dst = Item(line, dn)
        line.kit[dn] = dst
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
    line = w.lines.get(ln)
    if line is None:
        return "nosuch"
    it = line.kit.get(nm)
    if it is None:
        return "nosuch"
    seen = set()
    w.strip(it, 0, len(it.cell), seen)
    del line.kit[nm]
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


def do_charge(w, name):
    line = w.lines.get(name)
    if line is None:
        return "nosuch"
    return (line.ref, line.excl)


def do_gone(w, names):
    want = set()
    for name in names:
        line = w.lines.get(name)
        if line is None:
            return "nosuch"
        want.add(line)
    rel = 0
    seen = set()
    for line in want:
        for sp in line.own:
            if sp in seen:
                continue
            seen.add(sp)
            if want.issuperset(sp.by):
                rel += sp.wide
    return (rel,)


def do_family(w, name):
    line = w.lines.get(name)
    if line is None:
        return "nosuch"
    ref = 0
    excl = 0
    for z in w.kin(line):
        ref += z.ref - z.pair
        excl += z.lcat
    return (ref, excl)


def do_stat(w):
    if not w.widths:
        return (0, 0, 0)
    return (w.spare, len(w.starts), w.widths[-1])


def do_chart(w, ln, nm):
    it = _item(w, ln, nm)
    if it is None:
        return "nosuch"
    bits = []
    for i, cell in enumerate(it.cell):
        sp, off = cell
        if bits:
            at, base, boff, wide = bits[-1]
            if base == sp.at and boff + wide == off and at + wide == i:
                bits[-1] = (at, base, boff, wide + 1)
                continue
        bits.append((i, sp.at, off, 1))
    return (len(it.cell), bits)


def _pair_name(word):
    ln, _, nm = word.partition("/")
    return ln, nm


def _bad(cmd, who, code):
    if who is None:
        return "%s err=%s" % (cmd, code)
    return "%s %s err=%s" % (cmd, who, code)


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
        ln, nm = _pair_name(who)
        res = do_write(w, ln, nm, int(parts[2]), int(parts[3]))
        acc.append(_bad(cmd, who, res) if isinstance(res, str)
                   else "w %s new=%d keep=%d rel=%d" % (who, res[0], res[1], res[2]))
    elif cmd == "s":
        who = parts[4]
        sl, sn = _pair_name(parts[1])
        dl, dn = _pair_name(who)
        res = do_share(w, sl, sn, int(parts[2]), int(parts[3]), dl, dn, int(parts[5]))
        acc.append(_bad(cmd, who, res) if isinstance(res, str)
                   else "s %s rel=%d" % (who, res[0]))
    elif cmd == "t":
        who = parts[1]
        ln, nm = _pair_name(who)
        res = do_trim(w, ln, nm, int(parts[2]))
        acc.append(_bad(cmd, who, res) if isinstance(res, str)
                   else "t %s rel=%d" % (who, res[0]))
    elif cmd == "x":
        who = parts[1]
        ln, nm = _pair_name(who)
        res = do_erase(w, ln, nm)
        acc.append(_bad(cmd, who, res) if isinstance(res, str)
                   else "x %s rel=%d" % (who, res[0]))
    elif cmd == "v":
        who = parts[1]
        ln, nm = _pair_name(who)
        res = do_vac(w, ln, nm)
        acc.append(_bad(cmd, who, res) if isinstance(res, str)
                   else "v %s new=%d rel=%d" % (who, res[0], res[1]))
    elif cmd == "c":
        who = parts[1]
        res = do_charge(w, who)
        acc.append(_bad(cmd, who, res) if isinstance(res, str)
                   else "c %s ref=%d excl=%d" % (who, res[0], res[1]))
    elif cmd == "u":
        who = parts[1]
        res = do_family(w, who)
        acc.append(_bad(cmd, who, res) if isinstance(res, str)
                   else "u %s ref=%d excl=%d" % (who, res[0], res[1]))
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
        ln, nm = _pair_name(who)
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
