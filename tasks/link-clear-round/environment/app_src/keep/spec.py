class Bad(Exception):
    pass


GOES = ("drop", "clear", "bar", "wait")
MOVES = ("follow", "clear", "bar", "wait")


class Tab:
    __slots__ = ("name", "cols", "pos", "at")

    def __init__(self, name, cols, at):
        self.name = name
        self.cols = cols
        self.pos = {c: i for i, c in enumerate(cols)}
        self.at = at


class Link:
    __slots__ = ("name", "kid", "col", "ci", "par", "goes", "moves", "at")

    def __init__(self, name, kid, col, ci, par, goes, moves, at):
        self.name = name
        self.kid = kid
        self.col = col
        self.ci = ci
        self.par = par
        self.goes = goes
        self.moves = moves
        self.at = at


def _val(text):
    if text == "-":
        return None
    try:
        return int(text)
    except ValueError:
        raise Bad("%s is not a value" % text)


def _key(text):
    got = _val(text)
    if got is None:
        raise Bad("a key cannot be empty")
    return got


def _ring(tabs, links):
    edge = {name: set() for name in tabs}
    for ln in links:
        edge[ln.par].add(ln.kid)
    grey, black = set(), set()

    def down(name):
        grey.add(name)
        for nxt in edge[name]:
            if nxt in grey:
                raise Bad("%s is reachable from itself through the links" % nxt)
            if nxt not in black:
                down(nxt)
        grey.discard(name)
        black.add(name)

    for name in tabs:
        if name not in black:
            down(name)


def parse(text):
    tabs = {}
    links = []
    ops = []
    for raw in text.splitlines():
        part = raw.split()
        if not part:
            continue
        head = part[0]
        if head == "tab":
            if ops:
                raise Bad("tab after the first row op")
            if len(part) < 3:
                raise Bad("tab takes a name and at least one column")
            name = part[1]
            if name in tabs:
                raise Bad("table %s given twice" % name)
            cols = part[2:]
            if len(set(cols)) != len(cols):
                raise Bad("table %s repeats a column" % name)
            tabs[name] = Tab(name, cols, len(tabs))
        elif head == "link":
            if ops:
                raise Bad("link after the first row op")
            if len(part) != 7:
                raise Bad("link takes a name, a child, a column, a parent and two actions")
            name, kid, col, par, goes, moves = part[1:]
            if name in [ln.name for ln in links]:
                raise Bad("link %s given twice" % name)
            if kid not in tabs or par not in tabs:
                raise Bad("link %s names a table that is not there" % name)
            if kid == par:
                raise Bad("link %s joins a table to itself" % name)
            if col not in tabs[kid].pos:
                raise Bad("link %s names a column %s is without" % (name, kid))
            if goes not in GOES or moves not in MOVES:
                raise Bad("link %s carries an action that is not one" % name)
            ci = tabs[kid].pos[col]
            if ci == 0 and (goes == "clear" or moves == "clear"):
                raise Bad("link %s would empty a key" % name)
            links.append(Link(name, kid, col, ci, par, goes, moves, len(links)))
        elif head == "put":
            if len(part) < 3 or part[1] not in tabs:
                raise Bad("put takes a table and its values")
            tab = tabs[part[1]]
            vals = part[2:]
            if len(vals) != len(tab.cols):
                raise Bad("put on %s takes %d values" % (tab.name, len(tab.cols)))
            ops.append(("put", tab.name, [_key(vals[0])] + [_val(v) for v in vals[1:]]))
        elif head == "out":
            if len(part) != 3 or part[1] not in tabs:
                raise Bad("out takes a table and a key")
            ops.append(("out", part[1], _key(part[2])))
        elif head == "mov":
            if len(part) != 4 or part[1] not in tabs:
                raise Bad("mov takes a table, a key and a key")
            ops.append(("mov", part[1], _key(part[2]), _key(part[3])))
        else:
            raise Bad("unknown op %s" % head)
    if not tabs:
        raise Bad("no tab")
    _ring(tabs, links)
    return tabs, links, ops
