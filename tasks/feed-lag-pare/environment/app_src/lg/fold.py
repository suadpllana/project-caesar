class Gone:
    __slots__ = ()

    def __repr__(self):
        return "-"


ABSENT = Gone()


def step(cur, kind, arg):
    if kind == "set":
        return arg
    if kind == "add":
        return cur if cur is ABSENT else cur + arg
    return ABSENT


def value(store, key, point):
    cur = ABSENT
    for seq in store.at(key, 0, point):
        kind, _key, arg = store.entry(seq)
        cur = step(cur, kind, arg)
    return cur
