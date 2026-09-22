from tx.cat import Cat, Check, Fk


class St:
    __slots__ = ("op", "table", "key", "vals", "sets", "name", "want")

    def __init__(self, op, **kw):
        self.op = op
        for f in self.__slots__[1:]:
            setattr(self, f, kw.get(f))


class Prog:
    def __init__(self, cat, rows, stmts):
        self.cat = cat
        self.rows = rows
        self.stmts = stmts


def val(word):
    return None if word == "-" else int(word)


def _tail(words):
    deferrable = bool(words) and words[0] == "deferrable"
    return deferrable, deferrable and len(words) > 1 and words[1] == "deferred"


def _stmt(w):
    op = w[0]
    if op in ("begin", "commit"):
        return St(op)
    if op == "rollback":
        if len(w) == 1:
            return St("rollback")
        return St("back", name=w[2])
    if op in ("savepoint", "release"):
        return St(op, name=w[1])
    if op == "set":
        return St("set", name=w[1], want=w[2])
    if op == "insert":
        return St("insert", table=w[1], key=int(w[2]), vals=tuple(val(x) for x in w[3:]))
    if op == "update":
        pairs = [(w[i], val(w[i + 1])) for i in range(3, len(w), 2)]
        return St("update", table=w[1], key=int(w[2]), sets=pairs)
    if op == "delete":
        return St("delete", table=w[1], key=int(w[2]))
    raise ValueError("unknown statement: %s" % " ".join(w))


def load(text):
    cat = Cat()
    rows, stmts = [], []
    for line in text.splitlines():
        w = line.split()
        if not w:
            continue
        head = w[0]
        if head == "table":
            cat.add_table(w[1], w[2:])
        elif head == "check":
            if w[4] == "min":
                test, floor, rest = "min", int(w[5]), w[6:]
            else:
                test, floor, rest = w[4], None, w[5:]
            cat.add(Check(len(cat.cons), w[1], w[2], w[3], test, floor, *_tail(rest)))
        elif head == "fk":
            cat.add(Fk(len(cat.cons), w[1], w[2], w[3], w[4], w[5], *_tail(w[6:])))
        elif head == "row":
            rows.append((w[1], int(w[2]), tuple(val(x) for x in w[3:])))
        else:
            stmts.append(_stmt(w))
    return Prog(cat, rows, stmts)
