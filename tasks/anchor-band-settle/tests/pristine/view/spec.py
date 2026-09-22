import re


class Bad(Exception):
    pass


IDENT = re.compile(r"[a-z]+[0-9]+\Z")
EDITS = ("size", "add", "drop", "shut", "open", "pin", "unpin", "lift", "sink", "to")


class Prog:
    __slots__ = ("vh", "decl", "at", "frames")

    def __init__(self, vh, decl, at, frames):
        self.vh = vh
        self.decl = decl
        self.at = at
        self.frames = frames


def num(tok, head):
    if not tok.isdigit():
        raise Bad("%s takes a non-negative integer, got %r" % (head, tok))
    return int(tok)


def ident(tok, head):
    if not IDENT.match(tok):
        raise Bad("%s: bad id %r" % (head, tok))
    return tok


def flags(toks, head):
    got = {"pin": None, "shut": False, "lift": False, "live": False}
    for tok in toks:
        if tok.startswith("pin="):
            got["pin"] = num(tok[4:], head)
        elif tok in ("shut", "lift", "live"):
            got[tok] = True
        else:
            raise Bad("%s: unknown flag %r" % (head, tok))
    return got


def arity(part, lo, hi=None):
    n = len(part) - 1
    if n < lo or (hi is not None and n > hi):
        raise Bad("%s: wrong number of fields" % part[0])


def parse(text):
    vh = None
    decl = []
    at = None
    frames = []
    seen = set()
    for raw in text.splitlines():
        part = raw.split()
        if not part:
            continue
        head = part[0]
        if head == "view":
            if vh is not None or decl:
                raise Bad("view must come first, once")
            arity(part, 1, 1)
            vh = num(part[1], head)
            if vh < 1:
                raise Bad("view needs a height")
        elif head == "box":
            if vh is None or at is not None:
                raise Bad("box outside the declarations")
            arity(part, 3)
            bid = ident(part[1], head)
            par = part[2]
            if par != "-" and par not in seen:
                raise Bad("box %s: parent %s not declared" % (bid, par))
            if bid in seen:
                raise Bad("id %s used twice" % bid)
            seen.add(bid)
            decl.append((bid, par, num(part[3], head), flags(part[4:], head)))
        elif head == "at":
            if vh is None or at is not None:
                raise Bad("at must follow the declarations, once")
            arity(part, 1, 1)
            at = num(part[1], head)
        elif head == "frame":
            if at is None:
                raise Bad("frame before at")
            arity(part, 0, 0)
            frames.append([])
        elif head in EDITS:
            if not frames:
                raise Bad("%s outside a frame" % head)
            frames[-1].append(edit(part, seen))
        else:
            raise Bad("unknown statement %r" % head)
    if vh is None or at is None:
        raise Bad("a program needs view and at")
    return Prog(vh, decl, at, frames)


def edit(part, seen):
    head = part[0]
    if head == "to":
        arity(part, 1, 1)
        return ("to", None, num(part[1], head))
    if head == "add":
        arity(part, 4)
        bid = ident(part[1], head)
        if bid in seen:
            raise Bad("id %s used twice" % bid)
        seen.add(bid)
        par = part[2]
        if par != "-":
            ident(par, head)
        return ("add", bid, (par, num(part[3], head), num(part[4], head), flags(part[5:], head)))
    if head == "size":
        arity(part, 2, 2)
        return ("size", ident(part[1], head), num(part[2], head))
    if head == "pin":
        arity(part, 2, 2)
        return ("pin", ident(part[1], head), num(part[2], head))
    arity(part, 1, 1)
    return (head, ident(part[1], head), None)
