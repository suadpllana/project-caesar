from cf import step


class Book:
    __slots__ = ("ents", "nchg", "upto", "dead", "awake", "rows", "own")

    def __init__(self, prog):
        self.ents = prog.ents
        self.nchg = prog.nchg
        self.upto = 0
        self.dead = set()
        self.awake = set()
        self.rows = [None] * len(prog.ents)
        self.own = [[] for _ in range(prog.nchg)]
        for i, ent in enumerate(prog.ents):
            self.own[ent.chg].append(i)

    def stands(self, i):
        return self.ents[i].chg not in self.dead


def note(bk, bd, i):
    ent = bk.ents[i]
    if ent.kind == "sec":
        bk.rows[i] = ("sec", bd.cur, 0, False)
    elif ent.kind == "lnk":
        bk.rows[i] = ("lnk", bd.cur, bd.link.get(bd.cur), False)
    else:
        key = step.target(bd, ent)
        bk.rows[i] = ("val", key, bd.val.get(key), key in bd.gone)


def undo(bk, bd, i):
    row = bk.rows[i]
    if row is None:
        return
    bk.rows[i] = None
    if row[0] == "sec":
        bd.cur = row[1]
    elif row[0] == "lnk":
        if row[2] is None:
            bd.link.pop(row[1], None)
        else:
            bd.link[row[1]] = row[2]
    else:
        key = row[1]
        if row[2] is None:
            bd.val.pop(key, None)
        else:
            bd.val[key] = row[2]
        if row[3]:
            bd.gone.add(key)
        else:
            bd.gone.discard(key)
