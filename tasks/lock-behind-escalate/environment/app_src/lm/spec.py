class Bad(Exception):
    pass


class Cfg:
    __slots__ = ("k",)

    def __init__(self, k):
        self.k = k


class Op:
    __slots__ = ("kind", "tgt", "mode")

    def __init__(self, kind, tgt=None, mode=None):
        self.kind = kind
        self.tgt = tgt
        self.mode = mode


def table_of(tgt):
    return tgt.split(".", 1)[0]


def is_row(tgt):
    return "." in tgt


def _target(word):
    head, dot, tail = word.partition(".")
    if not head or not head.replace("_", "a").isalnum() or head[0].isdigit():
        raise Bad("bad target %r" % word)
    if dot and not tail.isdigit():
        raise Bad("bad row %r" % word)
    return word


def parse(text):
    cfg = None
    order = []
    ops = {}
    for n, raw in enumerate(text.splitlines(), 1):
        part = raw.split()
        if not part:
            continue
        if part[0] == "cfg":
            if cfg is not None or len(part) != 2 or not part[1].isdigit() or int(part[1]) < 1:
                raise Bad("line %d: bad cfg" % n)
            cfg = Cfg(int(part[1]))
            continue
        if cfg is None:
            raise Bad("line %d: cfg must come first" % n)
        name = part[0]
        if not (name[:1] == "T" and name[1:].isdigit()):
            raise Bad("line %d: bad transaction %r" % (n, name))
        if name not in ops:
            ops[name] = []
            order.append(name)
        if ops[name] and ops[name][-1].kind == "commit":
            raise Bad("line %d: %s already committed" % (n, name))
        if len(part) == 4 and part[1] == "lock" and part[3] in ("s", "x"):
            ops[name].append(Op("lock", _target(part[2]), part[3]))
        elif len(part) == 3 and part[1] == "drop":
            ops[name].append(Op("drop", _target(part[2])))
        elif len(part) == 2 and part[1] == "commit":
            ops[name].append(Op("commit"))
        else:
            raise Bad("line %d: bad op" % n)
    if cfg is None:
        raise Bad("no cfg line")
    for name in order:
        if ops[name][-1].kind != "commit":
            raise Bad("%s never commits" % name)
    return cfg, [(name, ops[name]) for name in order]
