"""Lines, the stamp tree, and what a stamp and a drop do to the claims under them.

A line is a named set of items and a place in the stamp tree: the line it was stamped from,
and the lines stamped from it. Stamping copies the claims rather than sharing them, because
the two lines diverge from the next write onward and each has to be counted on its own, and
it is why the origin has no exclusive space left the moment it is stamped. The tree is kept
on the line records themselves, never by name: a dropped name can be made again, and the new
line stands alone while the old one's stamps went to the old one's origin.
"""
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
