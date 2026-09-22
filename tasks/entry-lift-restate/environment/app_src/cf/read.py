ENTRY_ARGS = {"sec": 1, "set": 2, "clr": 1, "cut": 1, "add": 2, "lnk": 1}


class Bad(Exception):
    pass


class Ent:
    __slots__ = ("kind", "a", "b", "guard", "g", "w", "chg")

    def __init__(self, kind, a, b, guard, g, w, chg):
        self.kind = kind
        self.a = a
        self.b = b
        self.guard = guard
        self.g = g
        self.w = w
        self.chg = chg


class Prog:
    __slots__ = ("ents", "steps", "nchg")

    def __init__(self, ents, steps, nchg):
        self.ents = ents
        self.steps = steps
        self.nchg = nchg


def _ints(part, want, head):
    if len(part) != want:
        raise Bad("%s takes %d numbers, got %d" % (head, want, len(part)))
    try:
        return [int(x) for x in part]
    except ValueError:
        raise Bad("%s takes numbers" % head)


def parse(text):
    ents = []
    steps = []
    nchg = 0
    held = None
    for raw in text.splitlines():
        part = raw.split()
        if not part:
            continue
        head = part[0]
        if head == "open":
            if part[1:]:
                raise Bad("open takes nothing")
            if held is not None:
                raise Bad("open inside a change")
            held = nchg
            nchg += 1
            continue
        if head == "shut":
            if part[1:]:
                raise Bad("shut takes nothing")
            if held is None:
                raise Bad("shut without open")
            held = None
            continue
        if head in ("off", "back"):
            (c,) = _ints(part[1:], 1, head)
            if c < 0 or c >= nchg:
                raise Bad("%s names no change" % head)
            steps.append((head, c))
            continue
        if head == "get":
            s, n = _ints(part[1:], 2, "get")
            if s < 0 or n < 0:
                raise Bad("get takes a section and a name")
            steps.append(("get", s, n))
            continue
        if head == "all":
            if part[1:]:
                raise Bad("all takes nothing")
            steps.append(("all",))
            continue
        guard, g, w = None, 0, 0
        if head in ("if", "once"):
            if len(part) < 4:
                raise Bad("%s takes a name, a number and an entry" % head)
            guard = head
            g, w = _ints(part[1:3], 2, head)
            if g < 0:
                raise Bad("%s takes a name" % head)
            part = part[3:]
            head = part[0]
        if head not in ENTRY_ARGS:
            raise Bad("unknown op %s" % head)
        args = _ints(part[1:], ENTRY_ARGS[head], head)
        if args[0] < 0:
            raise Bad("%s takes a section or a name" % head)
        if held is None:
            chg = nchg
            nchg += 1
        else:
            chg = held
        ents.append(Ent(head, args[0], args[1] if len(args) > 1 else 0, guard, g, w, chg))
        steps.append(("ent", len(ents) - 1))
    if held is not None:
        raise Bad("open without shut")
    return Prog(ents, steps, nchg)
