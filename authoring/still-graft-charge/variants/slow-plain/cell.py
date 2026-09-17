from led import hold


class Cells:
    __slots__ = ("cap", "origin", "stills", "head")

    def __init__(self):
        self.cap = None
        self.origin = None
        self.stills = []
        self.head = {}


def mkline(st, name):
    st.lines[name] = Cells()


def line(st, name):
    return st.lines[name]


def spread(st, name, head, origin):
    one = Cells()
    one.origin = origin
    one.head = head
    st.lines[name] = one
    return one


def copy(st, name):
    return dict(st.lines[name].head)


def write(st, name, lo, hi, size):
    head = st.lines[name].head
    made = []
    for c in range(lo, hi + 1):
        old = head.get(c)
        if old is not None:
            hold.off(old, name)
        b = hold.Blk(0, size)
        hold.add(b, name)
        head[c] = b
        made.append((c, old, b))
    return made


def undo(st, name, made):
    head = st.lines[name].head
    for c, old, b in made:
        hold.off(b, name)
        if old is None:
            head.pop(c, None)
        else:
            head[c] = old
            hold.add(old, name)


def erase(st, name, lo, hi):
    head = st.lines[name].head
    for c in range(lo, hi + 1):
        old = head.pop(c, None)
        if old is not None:
            hold.off(old, name)


def at(st, name, c):
    b = st.lines[name].head.get(c)
    return None if b is None else b.num
