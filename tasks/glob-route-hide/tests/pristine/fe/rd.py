import re

WORD = re.compile(r"[a-z][a-z0-9]*$")
PATH = re.compile(r"[a-z][a-z0-9]*(\.[a-z][a-z0-9]*)*$")


class Ln:
    __slots__ = ("k", "nm", "src", "bn", "pb", "cf", "cv", "ix")

    def __init__(self, k, nm, src=None, bn=None, pb=False, cf=None, cv=True, ix=-1):
        self.k = k
        self.nm = nm
        self.src = src
        self.bn = bn
        self.pb = pb
        self.cf = cf
        self.cv = cv
        self.ix = ix


class Md:
    __slots__ = ("path", "lns")

    def __init__(self, path):
        self.path = path
        self.lns = []


class Prog:
    __slots__ = ("on", "mods", "order", "items", "refs")

    def __init__(self):
        self.on = frozenset()
        self.mods = {}
        self.order = []
        self.items = []
        self.refs = []


def bad(at, why):
    raise ValueError("line %d: %s" % (at, why))


def word(tok, at):
    if not WORD.match(tok):
        bad(at, "bad name %r" % tok)
    return tok


def path(tok, at):
    if not PATH.match(tok):
        bad(at, "bad module path %r" % tok)
    return tok


def cond(toks, at):
    if len(toks) >= 2 and toks[-2] == "if":
        f = toks[-1]
        want = True
        if f.startswith("!"):
            want = False
            f = f[1:]
        return toks[:-2], word(f, at), want
    return toks, None, True


def load(text):
    prog = Prog()
    cur = None
    seen_flags = False
    for at, raw in enumerate(text.splitlines(), 1):
        toks = raw.split()
        if not toks:
            continue
        if not seen_flags:
            if toks[0] != "flags":
                bad(at, "the first line must be the flags line")
            prog.on = frozenset(word(t, at) for t in toks[1:])
            seen_flags = True
            continue
        head = toks[0]
        if head == "mod":
            if len(toks) != 2:
                bad(at, "mod takes one path")
            p = path(toks[1], at)
            if p in prog.mods:
                bad(at, "module %s declared twice" % p)
            cur = Md(p)
            prog.mods[p] = cur
            prog.order.append(p)
            continue
        if cur is None:
            bad(at, "line outside any module")
        if head == "ref":
            if len(toks) != 2:
                bad(at, "ref takes one name")
            ln = Ln("ref", word(toks[1], at))
            cur.lns.append(ln)
            prog.refs.append((cur.path, ln))
            continue
        pb = False
        if head == "pub":
            pb = True
            toks = toks[1:]
        toks, cf, cv = cond(toks, at)
        if not toks:
            bad(at, "empty line body")
        if toks[0] == "item" and len(toks) == 2:
            ln = Ln("item", word(toks[1], at), pb=pb, cf=cf, cv=cv, ix=len(prog.items))
            prog.items.append((cur.path, ln))
            cur.lns.append(ln)
        elif toks[0] == "use" and len(toks) in (2, 4):
            src, sep, nm = toks[1].rpartition("::")
            if not sep:
                bad(at, "use needs a path and a name")
            src = path(src, at)
            if nm == "*":
                if len(toks) != 2:
                    bad(at, "a glob takes no rename")
                cur.lns.append(Ln("glob", None, src=src, pb=pb, cf=cf, cv=cv))
            else:
                nm = word(nm, at)
                bn = nm
                if len(toks) == 4:
                    if toks[2] != "as":
                        bad(at, "expected as")
                    bn = word(toks[3], at)
                cur.lns.append(Ln("use", nm, src=src, bn=bn, pb=pb, cf=cf, cv=cv))
        else:
            bad(at, "unknown line %r" % raw.strip())
    if not seen_flags:
        bad(0, "no flags line")
    return prog
