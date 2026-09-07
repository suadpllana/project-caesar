from . import grid, val

VAL = "v"
LAY = "r"


class State:
    def __init__(self, sheet):
        self.sheet = sheet
        self.book = {}
        self.busy = []
        self.mark = set()


def ask(st, tag, a, work):
    key = (tag, a)
    if key in st.book:
        return st.book[key]
    out = work()
    st.book.setdefault(key, out)
    return st.book[key]


def value(st, a):
    key = (VAL, a)
    if key in st.book:
        return st.book[key]
    if a in st.mark:
        for b in st.busy[st.busy.index(a):]:
            st.book[(VAL, b)] = grid.CYC
        return grid.CYC
    if not st.sheet.held(a):
        return grid.EMPTY
    st.busy.append(a)
    st.mark.add(a)
    try:
        out = val.run(st, st.sheet.node(a))
    finally:
        st.busy.pop()
        st.mark.discard(a)
    st.book.setdefault(key, out)
    return st.book[key]
