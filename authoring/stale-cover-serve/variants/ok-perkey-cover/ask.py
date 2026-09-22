"""The read path, and what a commit leaves behind.

A commit ends the validity of every stretch it wrote inside at the version before it, which
is the last version those rows were still the store's, and then retention runs against the
new present version.

A read asks two different questions about two different versions, and keeping them apart is
the whole of it. The first is whether some version inside the allowance has the range wholly
covered; if one does, nothing is fetched and the answer is that version's. Only when no
allowed version has a whole cover does the read go to the store, and then it goes as of now:
the holes are the parts no current stretch covers, shaped into runs by mend and fetched in key
order, each installed from the version the store last wrote the keys of the run it was fetched
in - so a combined fetch, whose run is wider, is correct from later on than the holes inside it
would have been.
"""

from . import age, hole, knit, mend, out, pick


def settle(tb, touched, now, tune):
    if touched:
        tb.close(touched, now - 1)
    age.sweep(tb, now, tune.horizon)


def read(tb, st, lo, hi, s, tune):
    lines = []
    at = pick.at(tb, lo, hi, s, st.ver)
    if at is None:
        runs = hole.runs(tb.near(lo, hi), lo, hi)
        for a, b in mend.shape(runs, lo, hi, tune.slack, tune.cap):
            lines.append(out.fetch(a, b))
            rows, mark = st.at(a, b)
            tb.add(a, b, rows, mark)
        at = st.ver
    lines.append(out.ans(at, knit.rows(tb.near(lo, hi), lo, hi, at)))
    return lines
