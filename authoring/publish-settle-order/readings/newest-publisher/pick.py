"""Which live unit answers a name.

The rule is the first publisher in publication order, fallback or not. Read literally that is a
scan of the order per resolution, which is exactly correct and far too slow: a run that settles
a hundred thousand uses against twenty thousand units pays the length of the order every time.

The invariant that makes it cheap is that the order only ever grows at the end. A unit joining
the back can never displace an answer that is already there, so its publications can be appended
to the per-name lists without looking at what is in front of them, and the head of a name's list
is that name's answer. Leaving is the direction that needs care - the unit behind the one that
left becomes the answer - and keeping the lists in publication order gives that for nothing.
"""


def _idx(h):
    i = getattr(h, "idx", None)
    if i is None:
        i = {}
        h.idx = i
    return i


def joined(h, r):
    i = _idx(h)
    for sym in dict.fromkeys(p[0] for p in r.pubs):
        i.setdefault(sym, []).append(r)


def parted(h, r):
    i = _idx(h)
    for sym in dict.fromkeys(p[0] for p in r.pubs):
        lst = i.get(sym)
        if not lst:
            continue
        for n, x in enumerate(lst):
            if x is r:
                del lst[n]
                break


def find(h, sym):
    lst = _idx(h).get(sym)
    return lst[-1] if lst else None
