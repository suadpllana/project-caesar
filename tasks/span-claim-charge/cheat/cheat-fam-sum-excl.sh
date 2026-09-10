#!/bin/bash
# reports a family's exclusive space as the sum of its members'
set -euo pipefail

cat > /app/store/dev.py <<'PYEOF'
import bisect


def setup(st):
    st.spot = {}
    st.atlist = []
    st.szlist = []
    st.spare = 0
    if st.blocks:
        _put(st, 0, st.blocks)
        st.spare = st.blocks


def _put(st, at, wide):
    st.spot[at] = wide
    bisect.insort(st.atlist, at)
    bisect.insort(st.szlist, (wide, at))


def _lift(st, at, wide):
    del st.spot[at]
    st.atlist.pop(bisect.bisect_left(st.atlist, at))
    st.szlist.pop(bisect.bisect_left(st.szlist, (wide, at)))


def total(st):
    return st.spare


def give(st, at, wide):
    """Return a span's blocks and merge with a free run on either side."""
    st.spare += wide
    tail = at + wide
    if tail in st.spot:
        w = st.spot[tail]
        _lift(st, tail, w)
        wide += w
    i = bisect.bisect_left(st.atlist, at)
    if i:
        head = st.atlist[i - 1]
        w = st.spot[head]
        if head + w == at:
            _lift(st, head, w)
            at = head
            wide += w
    _put(st, at, wide)


def take(st, want):
    """Best fit, ties to the lowest address; when nothing fits, largest run first."""
    if want > st.spare:
        return None
    st.spare -= want
    out = []
    left = want
    while left:
        i = bisect.bisect_left(st.szlist, (left, -1))
        if i < len(st.szlist):
            wide, at = st.szlist[i]
            _lift(st, at, wide)
            out.append((at, left))
            if wide > left:
                _put(st, at + left, wide - left)
            left = 0
        else:
            big = st.szlist[-1][0]
            wide, at = st.szlist[bisect.bisect_left(st.szlist, (big, -1))]
            _lift(st, at, wide)
            out.append((at, wide))
            left -= wide
    return out


def stat(st):
    if not st.szlist:
        return (0, 0, 0)
    return (st.spare, len(st.szlist), st.szlist[-1][0])
PYEOF

cat > /app/store/hold.py <<'PYEOF'
from store import dev, tally


class Span:
    __slots__ = ("at", "wide", "on", "by", "cover", "lca")

    def __init__(self, at, wide):
        self.at = at
        self.wide = wide
        self.on = {}
        self.by = {}
        self.cover = {}
        self.lca = None


class Claim:
    __slots__ = ("own", "at", "sp", "off", "wide")

    def __init__(self, own, at, sp, off, wide):
        self.own = own
        self.at = at
        self.sp = sp
        self.off = off
        self.wide = wide


def setup(st):
    return None


def add(st, cl):
    sp = cl.sp
    sp.on[cl] = True
    ln = cl.own.line
    seen = sp.by.get(ln, 0)
    sp.by[ln] = seen + 1
    if not seen:
        tally.gain(st, ln, sp)


def rip(st, cl):
    sp = cl.sp
    del sp.on[cl]
    ln = cl.own.line
    left = sp.by[ln] - 1
    if left:
        sp.by[ln] = left
    else:
        del sp.by[ln]
        tally.lose(st, ln, sp)
    return sp


def sweep(st, touched):
    """Give back every span the caller just emptied, once each."""
    rel = 0
    done = set()
    for sp in touched:
        if sp in done:
            continue
        done.add(sp)
        if not sp.on:
            dev.give(st, sp.at, sp.wide)
            rel += sp.wide
    return rel


def doomed(claims):
    """How many blocks the spans under these claims would return if all were ripped."""
    count = {}
    for cl in claims:
        count[cl.sp] = count.get(cl.sp, 0) + 1
    return sum(sp.wide for sp, k in count.items() if k == len(sp.on))


def bare(cl, lo, hi):
    """The stretches of [lo, hi) in span coordinates that no other claim covers."""
    sp = cl.sp
    marks = []
    for other in sp.on:
        if other is cl:
            continue
        a = other.off
        b = a + other.wide
        if b > lo and a < hi:
            marks.append((a if a > lo else lo, b if b < hi else hi))
    if not marks:
        return [(lo, hi)]
    marks.sort()
    out = []
    at = lo
    for a, b in marks:
        if a > at:
            out.append((at, a))
        if b > at:
            at = b
            if at >= hi:
                break
    if at < hi:
        out.append((at, hi))
    return out
PYEOF

cat > /app/store/item.py <<'PYEOF'
import bisect

from store import dev, hold


class Item:
    __slots__ = ("line", "size", "cl", "ats")

    def __init__(self, line):
        self.line = line
        self.size = 0
        self.cl = []
        self.ats = []


def setup(st):
    return None


def _get(st, ln, nm):
    line = st.lines.get(ln)
    if line is None:
        return None
    return line.kit.get(nm)


def _cut(st, it, at):
    """Force a claim boundary at item offset at, splitting the claim that straddles it."""
    i = bisect.bisect_right(it.ats, at) - 1
    cl = it.cl[i]
    if cl.at == at:
        return
    left = at - cl.at
    tail = hold.Claim(it, at, cl.sp, cl.off + left, cl.wide - left)
    cl.wide = left
    it.cl.insert(i + 1, tail)
    it.ats.insert(i + 1, at)
    hold.add(st, tail)


def _pull(st, it, lo, hi, touched):
    """Drop the item's coverage of [lo, hi); the caller decides when to sweep."""
    if lo >= hi:
        return
    if lo:
        _cut(st, it, lo)
    if hi < it.size:
        _cut(st, it, hi)
    i = bisect.bisect_left(it.ats, lo)
    j = bisect.bisect_left(it.ats, hi)
    for cl in it.cl[i:j]:
        touched.append(hold.rip(st, cl))
    del it.cl[i:j]
    del it.ats[i:j]


def _lay(st, it, gaps, spans):
    """Spread one allocation over the fresh stretches, in item order."""
    made = []
    k = 0
    off = 0
    for lo, hi in gaps:
        left = hi - lo
        cur = lo
        while left:
            sp = spans[k]
            step = sp.wide - off
            if step > left:
                step = left
            cl = hold.Claim(it, cur, sp, off, step)
            made.append(cl)
            hold.add(st, cl)
            cur += step
            off += step
            left -= step
            if off == sp.wide:
                k += 1
                off = 0
    for cl in made:
        i = bisect.bisect_left(it.ats, cl.at)
        it.cl.insert(i, cl)
        it.ats.insert(i, cl.at)


def _holes(at, end, keep):
    out = []
    pos = at
    for a, b in keep:
        if a > pos:
            out.append((pos, a))
        pos = b
    if pos < end:
        out.append((pos, end))
    return out


def _sole(it, at, over):
    """The stretches of [at, over) whose blocks carry no claim but this item's own."""
    keep = []
    i = bisect.bisect_right(it.ats, at) - 1
    j = bisect.bisect_left(it.ats, over)
    for cl in it.cl[i:j]:
        lo = cl.at if cl.at > at else at
        tail = cl.at + cl.wide
        hi = tail if tail < over else over
        for a, b in hold.bare(cl, cl.off + lo - cl.at, cl.off + hi - cl.at):
            keep.append((cl.at + a - cl.off, cl.at + b - cl.off))
    return keep


def _victims(it, gaps):
    out = []
    for lo, hi in gaps:
        if lo >= it.size:
            break
        stop = hi if hi < it.size else it.size
        i = bisect.bisect_left(it.ats, lo)
        j = bisect.bisect_left(it.ats, stop)
        for cl in it.cl[i:j]:
            if cl.at + cl.wide <= hi:
                out.append(cl)
    return out


def write(st, ln, nm, at, n):
    line = st.lines.get(ln)
    if line is None:
        return "nosuch"
    if n < 1:
        return "range"
    it = line.kit.get(nm)
    size = it.size if it is not None else 0
    if at > size:
        return "gap"
    end = at + n
    over = end if end < size else size
    keep = _sole(it, at, over) if it is not None and at < over else []
    gaps = _holes(at, end, keep)
    kept = sum(b - a for a, b in keep)
    if not gaps:
        return (0, kept, 0)
    need = n - kept
    if it is not None and dev.total(st) + hold.doomed(_victims(it, gaps)) < need:
        return "noroom"
    if it is None:
        if dev.total(st) < need:
            return "noroom"
        it = Item(line)
        line.kit[nm] = it
    touched = []
    for lo, hi in gaps:
        if lo < it.size:
            _pull(st, it, lo, hi if hi < it.size else it.size, touched)
    rel = hold.sweep(st, touched)
    spans = [hold.Span(a, w) for a, w in dev.take(st, need)]
    _lay(st, it, gaps, spans)
    if end > it.size:
        it.size = end
    return (need, kept, rel)


def share(st, sl, sn, at, n, dl, dn, to):
    src = _get(st, sl, sn)
    if src is None:
        return "nosuch"
    if n < 1 or at + n > src.size:
        return "range"
    line = st.lines.get(dl)
    if line is None:
        return "nosuch"
    dst = line.kit.get(dn)
    if dst is None:
        if to:
            return "gap"
    elif to > dst.size:
        return "gap"
    stop = at + n
    grab = []
    i = bisect.bisect_right(src.ats, at) - 1
    j = bisect.bisect_left(src.ats, stop)
    for cl in src.cl[i:j]:
        lo = cl.at if cl.at > at else at
        tail = cl.at + cl.wide
        hi = tail if tail < stop else stop
        grab.append((lo - at, cl.sp, cl.off + lo - cl.at, hi - lo))
    if dst is None:
        dst = Item(line)
        line.kit[dn] = dst
    end = to + n
    touched = []
    if to < dst.size:
        _pull(st, dst, to, end if end < dst.size else dst.size, touched)
    for rel_at, sp, off, wide in grab:
        cl = hold.Claim(dst, to + rel_at, sp, off, wide)
        hold.add(st, cl)
        i = bisect.bisect_left(dst.ats, cl.at)
        dst.cl.insert(i, cl)
        dst.ats.insert(i, cl.at)
    if end > dst.size:
        dst.size = end
    return (hold.sweep(st, touched),)


def trim(st, ln, nm, n):
    it = _get(st, ln, nm)
    if it is None:
        return "nosuch"
    if n > it.size:
        return "range"
    touched = []
    _pull(st, it, n, it.size, touched)
    it.size = n
    return (hold.sweep(st, touched),)


def erase(st, ln, nm):
    line = st.lines.get(ln)
    if line is None:
        return "nosuch"
    it = line.kit.get(nm)
    if it is None:
        return "nosuch"
    touched = []
    _pull(st, it, 0, it.size, touched)
    del line.kit[nm]
    return (hold.sweep(st, touched),)


def vac(st, ln, nm):
    it = _get(st, ln, nm)
    if it is None:
        return "nosuch"
    if not it.size:
        return (0, 0)
    if dev.total(st) + hold.doomed(it.cl) < it.size:
        return "noroom"
    touched = []
    _pull(st, it, 0, it.size, touched)
    rel = hold.sweep(st, touched)
    spans = [hold.Span(a, w) for a, w in dev.take(st, it.size)]
    _lay(st, it, [(0, it.size)], spans)
    return (it.size, rel)


def chart(st, ln, nm):
    """The coverage as maximal stretches, so the picture does not show where claims were cut."""
    it = _get(st, ln, nm)
    if it is None:
        return "nosuch"
    bits = []
    for cl in it.cl:
        if bits:
            at, base, off, wide = bits[-1]
            if base == cl.sp.at and off + wide == cl.off and at + wide == cl.at:
                bits[-1] = (at, base, off, wide + cl.wide)
                continue
        bits.append((cl.at, cl.sp.at, cl.off, cl.wide))
    return (it.size, bits)
PYEOF

cat > /app/store/line.py <<'PYEOF'
from store import hold, item, tally


class Line:
    __slots__ = ("name", "kit", "up", "kids",
                 "ref", "excl", "own", "lcat", "deep", "reach", "lcaof", "covers")

    def __init__(self, name, up):
        self.name = name
        self.kit = {}
        self.up = up
        self.kids = set()


def setup(st):
    st.lines = {}


def fresh(st, name):
    if name in st.lines:
        return "dup"
    ln = Line(name, None)
    st.lines[name] = ln
    tally.start(st, ln)
    return None


def stamp(st, src, dst):
    origin = st.lines.get(src)
    if origin is None:
        return "nosuch"
    if dst in st.lines:
        return "dup"
    ln = Line(dst, origin)
    origin.kids.add(ln)
    st.lines[dst] = ln
    tally.start(st, ln)
    for nm, it in origin.kit.items():
        twin = item.Item(ln)
        twin.size = it.size
        for cl in it.cl:
            copy = hold.Claim(twin, cl.at, cl.sp, cl.off, cl.wide)
            twin.cl.append(copy)
            twin.ats.append(cl.at)
            hold.add(st, copy)
        ln.kit[nm] = twin
    return (len(ln.kit),)


def drop(st, name):
    """Rip every claim, give back what that empties, then hand the stamps up the tree."""
    ln = st.lines.get(name)
    if ln is None:
        return "nosuch"
    touched = []
    for it in ln.kit.values():
        for cl in it.cl:
            touched.append(hold.rip(st, cl))
        it.cl = []
        it.ats = []
    rel = hold.sweep(st, touched)
    tally.retire(st, ln)
    del st.lines[name]
    return (rel,)
PYEOF

cat > /app/store/tally.py <<'PYEOF'
def setup(st):
    return None


def start(st, ln):
    ln.ref = 0
    ln.excl = 0
    ln.own = set()
    ln.lcat = 0
    ln.deep = 0
    ln.reach = 0
    ln.lcaof = set()
    ln.covers = set()


def gain(st, ln, sp):
    """This line has just reached one claim on the span."""
    ln.ref += sp.wide
    ln.own.add(sp)
    if len(sp.by) == 1:
        ln.excl += sp.wide
    elif len(sp.by) == 2:
        for other in sp.by:
            if other is not ln:
                other.excl -= sp.wide
    z = ln
    while z is not None:
        k = sp.cover.get(z, 0) + 1
        sp.cover[z] = k
        if k == 1:
            z.reach += sp.wide
            z.covers.add(sp)
        z = z.up
    _settle(sp, ln)


def lose(st, ln, sp):
    """This line has just dropped to no claim on the span."""
    ln.ref -= sp.wide
    ln.own.discard(sp)
    if not sp.by:
        ln.excl -= sp.wide
    elif len(sp.by) == 1:
        for other in sp.by:
            other.excl += sp.wide
    z = ln
    while z is not None:
        k = sp.cover[z] - 1
        if k:
            sp.cover[z] = k
        else:
            del sp.cover[z]
            z.reach -= sp.wide
            z.covers.discard(sp)
        z = z.up
    _settle(sp, next(iter(sp.by)) if sp.by else None)


def _settle(sp, member):
    """Re-find the deepest line every standing line descends from, starting from one of them."""
    want = len(sp.by)
    new = None
    z = member
    while z is not None:
        if sp.cover.get(z, 0) == want:
            new = z
            break
        z = z.up
    old = sp.lca
    if new is old:
        return
    if old is not None:
        old.lcat -= sp.wide
        old.lcaof.discard(sp)
        _lift(old, -sp.wide)
    if new is not None:
        new.lcat += sp.wide
        new.lcaof.add(sp)
        _lift(new, sp.wide)
    sp.lca = new


def _lift(z, delta):
    while z is not None:
        z.deep += delta
        z = z.up


def retire(st, ln):
    """A dropped line's stamps go to its origin, and so does what it carried for them."""
    up = ln.up
    for sp in ln.lcaof:
        sp.lca = up
        if up is not None:
            up.lcat += sp.wide
            up.lcaof.add(sp)
    ln.lcaof = set()
    for sp in ln.covers:
        del sp.cover[ln]
    ln.covers = set()
    for kid in ln.kids:
        kid.up = up
        if up is not None:
            up.kids.add(kid)
    if up is not None:
        up.kids.discard(ln)
    ln.kids = set()


def charge(st, name):
    ln = st.lines.get(name)
    if ln is None:
        return "nosuch"
    return (ln.ref, ln.excl)


def gone(st, names):
    want = set()
    for name in names:
        ln = st.lines.get(name)
        if ln is None:
            return "nosuch"
        want.add(ln)
    rel = 0
    seen = set()
    for ln in want:
        for sp in ln.own:
            if sp in seen:
                continue
            seen.add(sp)
            if want.issuperset(sp.by):
                rel += sp.wide
    return (rel,)


def family(st, name):
    ln = st.lines.get(name)
    if ln is None:
        return "nosuch"
    members = []
    todo = [ln]
    while todo:
        z = todo.pop()
        members.append(z)
        todo.extend(z.kids)
    return (ln.reach, sum(z.excl for z in members))
PYEOF
