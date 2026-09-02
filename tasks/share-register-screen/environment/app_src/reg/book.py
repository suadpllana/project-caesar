from . import lex


class Book:
    __slots__ = ("cos", "seat", "vps", "held", "nom", "pg", "seen")

    def __init__(self):
        self.cos = []
        self.seat = {}
        self.vps = {}
        self.held = {}
        self.nom = {}
        self.pg = []
        self.seen = []


def _touch(bk, who):
    if who not in bk.seen:
        bk.seen.append(who)


def load(text):
    bk = Book()
    for op, arg in lex.scan(text):
        if op == "co":
            cid, n = arg
            if cid in bk.seat:
                raise lex.Bad("twice: %s" % cid)
            bk.cos.append(cid)
            bk.seat[cid] = int(n)
            _touch(bk, cid)
        elif op == "cl":
            cid, kind, w = arg
            if cid not in bk.seat:
                raise lex.Bad("no co: %s" % cid)
            bk.vps[(cid, kind)] = int(w)
        elif op == "is":
            cid, kind, n, who = arg
            if (cid, kind) not in bk.vps:
                raise lex.Bad("no cl: %s %s" % (cid, kind))
            key = (cid, kind, who)
            bk.held[key] = bk.held.get(key, 0) + int(n)
            _touch(bk, who)
        elif op == "mv":
            cid, kind, n, src, dst = arg
            key = (cid, kind, src)
            have = bk.held.get(key, 0)
            take = int(n)
            if take > have:
                raise lex.Bad("short: %s %s %s" % (cid, kind, src))
            bk.held[key] = have - take
            to = (cid, kind, dst)
            bk.held[to] = bk.held.get(to, 0) + take
            _touch(bk, dst)
        elif op == "nm":
            who, principal = arg
            bk.nom[who] = principal
            _touch(bk, who)
            _touch(bk, principal)
        elif op == "nx":
            who = arg[0]
            bk.nom.pop(who, None)
        else:
            who = arg[0]
            if who not in bk.pg:
                bk.pg.append(who)
            _touch(bk, who)
    return bk
