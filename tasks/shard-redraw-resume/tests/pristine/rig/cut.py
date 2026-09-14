def width(run, st):
    return st.rank * run.micro * run.accum


def room(run, st):
    left = run.rows - st.seen
    if left >= width(run, st):
        return True
    unit = st.rank * run.micro
    return unit > 0 and left >= unit


def roll(st):
    st.epoch += 1
    st.seen = 0
