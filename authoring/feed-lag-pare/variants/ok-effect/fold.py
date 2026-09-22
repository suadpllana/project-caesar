class Gone:
    __slots__ = ()


ABSENT = Gone()

NOP = ("nop", 0)


def make(kind, arg):
    if kind == "set":
        return ("set", arg)
    if kind == "add":
        return ("add", arg)
    return ("del", 0)


def join(first, second):
    tag = second[0]
    if tag == "nop":
        return first
    if tag in ("set", "del"):
        return second
    head = first[0]
    if head == "nop":
        return ("add", second[1])
    if head == "add":
        return ("add", first[1] + second[1])
    if head == "set":
        return ("set", first[1] + second[1])
    return ("set", second[1])


def land(eff, before):
    tag = eff[0]
    if tag == "nop":
        return before
    if tag == "set":
        return eff[1]
    if tag == "del":
        return ABSENT
    return eff[1] if before is ABSENT else before + eff[1]


def step(cur, kind, arg):
    return land(make(kind, arg), cur)


def same(one, two):
    if isinstance(one, Gone) or isinstance(two, Gone):
        return isinstance(one, Gone) and isinstance(two, Gone)
    return one == two


def value(store, key, point):
    eff = NOP
    for seq in store.at(key, 0, point):
        kind, _key, arg = store.entry(seq)
        eff = join(eff, make(kind, arg))
    return land(eff, ABSENT)
