"""Items as one entry per block, and the write path over them."""
from store import dev, hold


def setup(st):
    return None


def _spots(runs):
    out = []
    for lo, hi in runs:
        out.extend(range(lo, hi))
    return out


def _runs(lo, hi, flags):
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


def _item(st, ln, nm):
    line = st.lines.get(ln)
    if line is None:
        return None
    return line.kit.get(nm)


def write(st, ln, nm, at, n):
    line = st.lines.get(ln)
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
        if st.spare + hold.doomed(it, spots) < need:
            return "noroom"
    elif st.spare < need:
        return "noroom"
    if it is None:
        it = hold.Item(line, nm)
        line.kit[nm] = it
    seen = set()
    for lo, hi in gaps:
        if lo < size:
            hold.strip(st, it, lo, hi if hi < size else size, seen)
    rel = hold.bury(st, seen)
    if end > size:
        it.cell.extend([None] * (end - size))
    hold.fill(st, it, _spots(gaps), dev.take(st, need))
    return (need, kept, rel)


def share(st, sl, sn, at, n, dl, dn, to):
    src = _item(st, sl, sn)
    if src is None:
        return "nosuch"
    if n < 1 or at + n > len(src.cell):
        return "range"
    line = st.lines.get(dl)
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
        dst = hold.Item(line, dn)
        line.kit[dn] = dst
    size = len(dst.cell)
    end = to + n
    seen = set()
    if to < size:
        hold.strip(st, dst, to, end if end < size else size, seen)
    if end > size:
        dst.cell.extend([None] * (end - size))
    for k, cell in enumerate(grab):
        dst.cell[to + k] = cell
        hold.hook(st, dst.line, cell[0], cell[1])
    return (hold.bury(st, seen),)


def trim(st, ln, nm, n):
    it = _item(st, ln, nm)
    if it is None:
        return "nosuch"
    size = len(it.cell)
    if n > size:
        return "range"
    seen = set()
    hold.strip(st, it, n, size, seen)
    del it.cell[n:]
    return (hold.bury(st, seen),)


def erase(st, ln, nm):
    line = st.lines.get(ln)
    if line is None:
        return "nosuch"
    it = line.kit.get(nm)
    if it is None:
        return "nosuch"
    seen = set()
    hold.strip(st, it, 0, len(it.cell), seen)
    del line.kit[nm]
    return (hold.bury(st, seen),)


def vac(st, ln, nm):
    it = _item(st, ln, nm)
    if it is None:
        return "nosuch"
    size = len(it.cell)
    if not size:
        return (0, 0)
    if st.spare + hold.doomed(it, range(size)) < size:
        return "noroom"
    seen = set()
    hold.strip(st, it, 0, size, seen)
    rel = hold.bury(st, seen)
    hold.fill(st, it, list(range(size)), dev.take(st, size))
    return (size, rel)


def chart(st, ln, nm):
    it = _item(st, ln, nm)
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
