#!/bin/bash
# gives each fresh stretch one span
set -euo pipefail

cat > /app/store/dev.py <<'PYEOF'
"""Free space: the runs, and the two orders they have to be found in.

A run is a maximal stretch of free blocks. Allocation wants the smallest run that fits
(and the lowest of those, then the largest run when nothing fits), release wants the
neighbours of an address. Those are two different orders over the same runs, so both are
carried: `spot` maps a start to its length, `atlist` holds the starts in address order for
the backward neighbour, and `szlist` holds (length, start) so best fit is a bisection
rather than a scan. Runs only ever split at an allocation and merge at a release, so both
indexes are edited in place instead of rebuilt.
"""
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
"""Spans and the claims on them.

A span is a stretch of blocks handed out by one allocation; it never splits and never
grows. Every claim that points into one is registered here, twice over: once in `on`, so
the blocks under a range can be tested for a second claim, and once in `by`, a count per
line, so the charge side can be told which lines stand on the span without walking the
claims. Both are needed - `on` answers "may this block be rewritten in place", `by`
answers "is this span exclusive to one line", and neither answers the other's question.
"""
from store import dev, tally


class Span:
    __slots__ = ("at", "wide", "on", "by")

    def __init__(self, at, wide):
        self.at = at
        self.wide = wide
        self.on = {}
        self.by = {}


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
    seen = sp.by.get(cl.own.line, 0)
    sp.by[cl.own.line] = seen + 1
    if not seen:
        tally.gain(st, cl.own.line, sp)


def rip(st, cl):
    sp = cl.sp
    del sp.on[cl]
    left = sp.by[cl.own.line] - 1
    if left:
        sp.by[cl.own.line] = left
    else:
        del sp.by[cl.own.line]
        tally.lose(st, cl.own.line, sp)
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
"""Items, and the write path the rest of the rules force.

An item's claims are kept in item order and tile [0, size) exactly. A write is decided one
block at a time: where the block under it carries no second claim it stays where it is,
and everything else is fresh. That splits the written range into stretches, and the order
the rest of the rules impose is not the obvious one - the replaced claims go first, so the
spans they empty are back in the free map before the allocation runs and can be handed
straight back to the same write. The room check therefore has to be made against the free
total that release will produce, not the one standing when the command arrives, and the
allocated pieces are laid over the stretches in item order, so one stretch can straddle
two pieces and one piece can serve two stretches.
"""
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
    kit = st.lines.get(ln)
    if kit is None:
        return None
    return kit.get(nm)


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
    made = []
    for k, (lo, hi) in enumerate(gaps):
        sp = spans[k if k < len(spans) else len(spans) - 1]
        cl = hold.Claim(it, lo, sp, 0, hi - lo)
        made.append(cl)
        hold.add(st, cl)
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
    kit = st.lines.get(ln)
    if kit is None:
        return "nosuch"
    if n < 1:
        return "range"
    it = kit.get(nm)
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
        it = Item(ln)
        kit[nm] = it
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
    kit = st.lines.get(dl)
    if kit is None:
        return "nosuch"
    dst = kit.get(dn)
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
        dst = Item(dl)
        kit[dn] = dst
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
    kit = st.lines.get(ln)
    if kit is None:
        return "nosuch"
    it = kit.get(nm)
    if it is None:
        return "nosuch"
    touched = []
    _pull(st, it, 0, it.size, touched)
    del kit[nm]
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
"""Lines, and what a stamp and a drop do to the claims under them.

A line is a named set of items. Stamping one produces a second line standing on exactly
the same spans, which is why the origin has no exclusive space left the moment it is
stamped: every span it held alone is now held by two. The claims are copied rather than
shared, because the two lines diverge from the next write onward and each has to be
counted on its own.
"""
from store import hold, item, tally


def setup(st):
    st.lines = {}


def fresh(st, name):
    if name in st.lines:
        return "dup"
    st.lines[name] = {}
    tally.start(st, name)
    return None


def stamp(st, src, dst):
    if src not in st.lines:
        return "nosuch"
    if dst in st.lines:
        return "dup"
    st.lines[dst] = {}
    tally.start(st, dst)
    kit = st.lines[dst]
    for nm, it in st.lines[src].items():
        twin = item.Item(dst)
        twin.size = it.size
        for cl in it.cl:
            copy = hold.Claim(twin, cl.at, cl.sp, cl.off, cl.wide)
            twin.cl.append(copy)
            twin.ats.append(cl.at)
            hold.add(st, copy)
        kit[nm] = twin
    return (len(kit),)


def drop(st, name):
    if name not in st.lines:
        return "nosuch"
    touched = []
    for it in st.lines[name].values():
        for cl in it.cl:
            touched.append(hold.rip(st, cl))
        it.cl = []
        it.ats = []
    rel = hold.sweep(st, touched)
    del st.lines[name]
    tally.end(st, name)
    return (rel,)
PYEOF

cat > /app/store/tally.py <<'PYEOF'
"""What each line is charged, carried forward rather than recounted.

Referenced space is the whole length of every span a line stands on, counted once however
many claims it holds there. Exclusive space is the part of that no other line stands on.
Both change only when a line's claim count on one span leaves or reaches zero, so they are
running totals: `gain` and `lose` are called from the span table at exactly those moments
and move the two numbers by that span's length. `own` keeps the spans per line as well,
because the freed-by-dropping question is asked about a set of lines and no running total
can answer it.
"""


def setup(st):
    st.ref = {}
    st.excl = {}
    st.own = {}


def start(st, name):
    st.ref[name] = 0
    st.excl[name] = 0
    st.own[name] = set()


def end(st, name):
    del st.ref[name]
    del st.excl[name]
    del st.own[name]


def gain(st, name, sp):
    """This line has just reached one claim on the span."""
    st.ref[name] += sp.wide
    st.own[name].add(sp)
    if len(sp.by) == 1:
        st.excl[name] += sp.wide
    elif len(sp.by) == 2:
        for other in sp.by:
            if other != name:
                st.excl[other] -= sp.wide


def lose(st, name, sp):
    """This line has just dropped to no claim on the span."""
    st.ref[name] -= sp.wide
    st.own[name].discard(sp)
    if not sp.by:
        st.excl[name] -= sp.wide
    elif len(sp.by) == 1:
        for other in sp.by:
            st.excl[other] += sp.wide


def charge(st, name):
    if name not in st.ref:
        return "nosuch"
    return (st.ref[name], st.excl[name])


def gone(st, names):
    want = set()
    for name in names:
        if name not in st.own:
            return "nosuch"
        want.add(name)
    rel = 0
    seen = set()
    for name in want:
        for sp in st.own[name]:
            if sp in seen:
                continue
            seen.add(sp)
            if want.issuperset(sp.by):
                rel += sp.wide
    return (rel,)
PYEOF
