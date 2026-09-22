from . import age, hole, knit, mend, out, pick


def settle(tb, touched, now, tune):
    if touched:
        tb.kill(touched)
    age.sweep(tb, now, tune.horizon)


def read(tb, st, lo, hi, s, tune):
    lines = []
    at = pick.at(tb, lo, hi, s, st.ver)
    if at is None:
        runs = mend.shape(hole.runs(tb.items, lo, hi), lo, hi, tune.slack, tune.cap)
        for a, b in runs:
            lines.append(out.fetch(a, b))
            rows, mark = st.at(a, b)
            tb.add(a, b, rows, mark)
        at = st.ver
    lines.append(out.ans(at, knit.rows(tb.items, lo, hi, at)))
    return lines
