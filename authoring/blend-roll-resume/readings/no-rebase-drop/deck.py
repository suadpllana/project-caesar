"""The manifest side: who is in the blend, what they weigh, and who has left.

Every change here is a blend change, and a blend change is what returns the draw counters to
zero. Declaring a source mid-run is one, reweighing is one whatever weight it names, and a
departure is one.
"""
from mix import say


def add(h, name, n, w, cap):
    b = h.book
    b.names.append(name)
    b.size[name] = n
    b.weight[name] = w
    b.cap[name] = cap
    b.live.append(name)
    h.epoch[name] = 0
    h.cur[name] = 0
    h.cnt[name] = 0
    rebase(h)


def weigh(h, name, w):
    h.book.weight[name] = w
    rebase(h)


def drop(h, name):
    h.book.live.remove(name)


def rebase(h):
    for name in h.book.live:
        h.cnt[name] = 0


def sig(h):
    """The blend as the draw rule sees it: who is live, in order, and what each weighs."""
    b = h.book
    return tuple(b.live), tuple(b.weight[name] for name in b.live)


def at(h, name):
    if name in h.book.live:
        say.at(h, name, h.epoch[name], h.cur[name])
    else:
        say.at(h, name, None, None)
