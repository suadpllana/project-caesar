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
