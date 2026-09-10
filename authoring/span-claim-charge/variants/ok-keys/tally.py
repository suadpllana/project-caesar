"""A correct variant: the same claims, with the family settled from a table keyed by standing set.

Every line gets one bit; every span carries the mask of the lines standing on it, and a table
keeps the total length of the spans per distinct mask. A family question walks the stamp tree
for the family's mask and sums the table: a span counts toward the family's referenced space
when its mask meets the family's, and toward its exclusive space when its mask lies inside it.
Nothing is transferred when a line is dropped, because the table is keyed by the standing set
and the family is read off the tree at the moment of the question.
"""


def setup(st):
    st.bits = {}
    st.table = {}


def start(st, ln):
    ln.ref = 0
    ln.excl = 0
    ln.own = set()
    st.bits[ln] = 1 << len(st.bits)


def _move(st, sp, before, after):
    if before:
        st.table[before] -= sp.wide
        if not st.table[before]:
            del st.table[before]
    if after:
        st.table[after] = st.table.get(after, 0) + sp.wide


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
    before = sp.mask or 0
    sp.mask = before | st.bits[ln]
    _move(st, sp, before, sp.mask)


def lose(st, ln, sp):
    """This line has just dropped to no claim on the span."""
    ln.ref -= sp.wide
    ln.own.discard(sp)
    if not sp.by:
        ln.excl -= sp.wide
    elif len(sp.by) == 1:
        for other in sp.by:
            other.excl += sp.wide
    before = sp.mask or 0
    sp.mask = before & ~st.bits[ln]
    _move(st, sp, before, sp.mask)


def retire(st, ln):
    up = ln.up
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
    """Correct, and a real derivation: sum the table over the standing masks inside the family."""
    ln = st.lines.get(name)
    if ln is None:
        return "nosuch"
    fam = 0
    todo = [ln]
    while todo:
        z = todo.pop()
        fam |= st.bits[z]
        todo.extend(z.kids)
    ref = 0
    excl = 0
    for mask, wide in st.table.items():
        if mask & fam:
            ref += wide
            if not (mask & ~fam):
                excl += wide
    return (ref, excl)
