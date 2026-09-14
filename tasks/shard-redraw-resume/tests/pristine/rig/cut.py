def width(run, st):
    return st.rank * run.micro * run.accum


def span(run, st):
    wide = width(run, st)
    left = run.rows - st.seen
    if left >= wide:
        return st.seen, wide
    unit = st.rank * run.micro
    short = (left // unit) * unit if unit else 0
    if short <= 0:
        return None
    return st.seen, short


def roll(st):
    st.epoch += 1
    st.seen = 0
