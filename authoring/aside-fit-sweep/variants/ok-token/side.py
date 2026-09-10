"""The aside list as one stack per size and one queue of tokens with tombstones."""
from pool import find
from reg import geom


def _bag(h):
    b = getattr(h, "sb", None)
    if b is None:
        b = h.sb = {"at": {}, "by": {}, "q": [], "head": 0, "n": 0, "tick": 0}
    return b


def park(h, a, n):
    b = _bag(h)
    b["tick"] += 1
    tag = b["tick"]
    b["at"][tag] = (a, n)
    b["by"].setdefault(n, []).append(tag)
    b["q"].append(tag)
    b["n"] += 1
    while b["n"] > geom.ROOM:
        tag = b["q"][b["head"]]
        b["head"] += 1
        got = b["at"].pop(tag, None)
        if got is None:
            continue
        b["n"] -= 1
        find.add(h, got[0], got[1])


def match(h, n):
    b = _bag(h)
    stack = b["by"].get(n)
    while stack:
        got = b["at"].pop(stack.pop(), None)
        if got is not None:
            b["n"] -= 1
            return got
    return None


def all_back(h):
    b = _bag(h)
    for a, n in b["at"].values():
        find.add(h, a, n)
    b["at"].clear()
    b["by"].clear()
    del b["q"][:]
    b["head"] = 0
    b["n"] = 0
