"""Lines and the stamp tree, kept as stamp paths so the standing lines of a span sort in tree order."""
from store import hold, tally


class Line:
    __slots__ = ("name", "path", "kit", "alive", "ref", "excl", "own", "lcat", "pair")

    def __init__(self, name, path):
        self.name = name
        self.path = path
        self.kit = {}
        self.alive = True
        self.ref = 0
        self.excl = 0
        self.own = set()
        self.lcat = 0
        self.pair = 0


def setup(st):
    st.lines = {}
    st.bypath = {}
    st.serial = 0


def mint(st, name, up):
    st.serial += 1
    path = (st.serial,) if up is None else up.path + (st.serial,)
    line = Line(name, path)
    st.lines[name] = line
    st.bypath[path] = line
    return line


def deepest(st, path):
    for k in range(len(path), 0, -1):
        line = st.bypath.get(path[:k])
        if line is not None and line.alive:
            return line
    return None


def meet(st, pa, pb):
    k = 0
    n = min(len(pa), len(pb))
    while k < n and pa[k] == pb[k]:
        k += 1
    return deepest(st, pa[:k]) if k else None


def kin(st, line):
    n = len(line.path)
    return [z for z in st.lines.values() if z.path[:n] == line.path]


def fresh(st, name):
    if name in st.lines:
        return "dup"
    mint(st, name, None)
    return None


def stamp(st, src, dst):
    origin = st.lines.get(src)
    if origin is None:
        return "nosuch"
    if dst in st.lines:
        return "dup"
    line = mint(st, dst, origin)
    for nm, it in origin.kit.items():
        twin = hold.Item(line, nm)
        twin.cell = list(it.cell)
        line.kit[nm] = twin
        for cell in twin.cell:
            if cell is not None:
                hold.hook(st, line, cell[0], cell[1])
    return (len(line.kit),)


def drop(st, name):
    line = st.lines.get(name)
    if line is None:
        return "nosuch"
    seen = set()
    for it in line.kit.values():
        hold.strip(st, it, 0, len(it.cell), seen)
    rel = hold.bury(st, seen)
    up = deepest(st, line.path[:-1]) if len(line.path) > 1 else None
    if up is not None:
        up.lcat += line.lcat
        up.pair += line.pair
    line.lcat = 0
    line.pair = 0
    line.alive = False
    del st.lines[name]
    return (rel,)
