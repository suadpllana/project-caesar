"""One entry applied to a standing value, and a run of them folded from absent.

An `add` onto an absent key makes it present at that amount rather than doing nothing, which
is the difference between a key that comes back and one that stays gone. `same` is the only
place absent is compared: it is equal to absent and to nothing else, including zero.
"""

class Gone:
    __slots__ = ()

    def __repr__(self):
        return "-"


ABSENT = Gone()


def step(cur, kind, arg):
    if kind == "set":
        return arg
    if kind == "add":
        return arg if cur is ABSENT else cur + arg
    return ABSENT


def same(one, two):
    if one is ABSENT or two is ABSENT:
        return one is two
    return one == two


def value(store, key, point):
    cur = ABSENT
    for seq in store.at(key, 0, point):
        kind, _key, arg = store.entry(seq)
        cur = step(cur, kind, arg)
    return cur
