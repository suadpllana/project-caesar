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
    """Correct, and the way it reads: walk the family and look at every span it stands on."""
    ln = st.lines.get(name)
    if ln is None:
        return "nosuch"
    members = set()
    todo = [ln]
    while todo:
        z = todo.pop()
        members.add(z)
        todo.extend(z.kids)
    ref = 0
    excl = 0
    seen = set()
    for z in members:
        for sp in z.own:
            if sp in seen:
                continue
            seen.add(sp)
            ref += sp.wide
            if members.issuperset(sp.by):
                excl += sp.wide
    return (ref, excl)
