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
