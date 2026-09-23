from bisect import bisect_left

from scn import dct, rd


def ensure_read(ch, pg, mem, out):
    """The page's raw (as-written, no update overrides applied) values,
    reading and caching them -- printing dc -- only the first time ever."""
    key = (pg.c, pg.j, pg.p)
    vals = mem.read_vals.get(key)
    if vals is None:
        out.dc(pg.c, pg.j, pg.p)
        vals = rd.values(ch, pg)
        mem.read_vals[key] = vals
    return vals


def eligible(pg, upd_sorted):
    """Row ids in this page's range that take their value from the page
    itself, i.e. carry no update override for its column."""
    lo = pg.start
    hi = lo + pg.n
    if not upd_sorted:
        return list(range(lo, hi))
    i = bisect_left(upd_sorted, lo)
    j = bisect_left(upd_sorted, hi)
    if i == j:
        return list(range(lo, hi))
    skip = set(upd_sorted[i:j])
    return [r for r in range(lo, hi) if r not in skip]


def resolve_page(mem, cond, ch, pg, alive, upd_sorted, out):
    """Settle cond for every alive, eligible row this (header-ambiguous) page
    still holds, consulting the dictionary and/or reading the page only when
    that cannot be avoided. Returns the rows that fail cond (and so die);
    an empty list means every such row already passes."""
    elig = [r for r in eligible(pg, upd_sorted) if r in alive]
    if not elig:
        return elig
    key = (pg.c, pg.j, pg.p)
    vals = mem.read_vals.get(key)
    if vals is None and pg.form == "i" and cond.kind not in ("nn", "nu"):
        dct.consult(mem, ch, out)
        v = dct.verdict(ch, pg, cond)
        if v == "miss":
            return elig
        if v == "allsat":
            return []
    if vals is None:
        vals = ensure_read(ch, pg, mem, out)
    start = pg.start
    return [r for r in elig if not rd.sat(cond, vals[r - start])]
