"""What each line, and each family of lines, is charged - carried forward, never recounted.

Referenced space is the whole length of every span a line stands on, counted once however
many claims it holds there. Exclusive space is the part of that no other line stands on. Both
change only when a line's claim count on one span leaves or reaches zero, so they are running
totals: `gain` and `lose` are called from the span table at exactly those moments and move the
two numbers by that span's length. `own` keeps the spans per line as well, because the
freed-by-dropping question is asked about a set of lines and no running total can answer it.

The family questions are asked about a line and everything stamped from it, and at the stated
scale they cannot be answered by walking either. What each span carries instead is its standing
set read against the stamp tree: `cover` counts, for every line above a standing line, how many
standing lines descend from it, and `lca` is the deepest line all of them descend from - the
first line on any standing line's way to the root whose count is the whole set. A span lies in
a family's exclusive space exactly when its `lca` is inside the family, and in its referenced
space exactly when its `cover` names the family's line, so every line keeps `lcat` (the spans
whose `lca` it is), `deep` (the same summed over everything stamped from it) and `reach` (the
spans whose `cover` names it), and a query reads two numbers. A drop hands the dropped line's
`lcat` to its origin, which is where the deepest common line of those spans now sits.
"""


def setup(st):
    return None


BITS = {}
TABLE = {}


def start(st, ln):
    ln.ref = 0
    ln.excl = 0
    ln.own = set()
    ln.kids = set() if not hasattr(ln, "kids") else ln.kids
    if not BITS:
        TABLE.clear()
    BITS[ln] = 1 << len(BITS)


def _move(sp, before, after):
    if before:
        TABLE[before] -= sp.wide
        if not TABLE[before]:
            del TABLE[before]
    if after:
        TABLE[after] = TABLE.get(after, 0) + sp.wide


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
    before = sp.lca or 0
    sp.lca = before | BITS[ln]
    _move(sp, before, sp.lca)


def lose(st, ln, sp):
    """This line has just dropped to no claim on the span."""
    ln.ref -= sp.wide
    ln.own.discard(sp)
    if not sp.by:
        ln.excl -= sp.wide
    elif len(sp.by) == 1:
        for other in sp.by:
            other.excl += sp.wide
    before = sp.lca or 0
    sp.lca = before & ~BITS[ln]
    _move(sp, before, sp.lca)


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
        fam |= BITS[z]
        todo.extend(z.kids)
    ref = 0
    excl = 0
    for mask, wide in TABLE.items():
        if mask & fam:
            ref += wide
            if not (mask & ~fam):
                excl += wide
    return (ref, excl)
