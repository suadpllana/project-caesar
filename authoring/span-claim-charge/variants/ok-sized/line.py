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
