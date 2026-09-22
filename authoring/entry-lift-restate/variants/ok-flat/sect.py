"""The board, held as a history per key with its position index rebuilt only when asked for.

Writes go into a dictionary from position to content and the sorted position list beside it
is marked stale; the list is rebuilt the next time somebody looks a position up. Withdrawing
a change usually touches several writes to the same key at once, so rebuilding once beats
keeping the list in order on every single write.
"""
import bisect


class Store:
    __slots__ = ("hist", "seq", "stale", "jump", "goes")

    def __init__(self):
        self.hist = {}
        self.seq = {}
        self.stale = set()
        self.jump = []
        self.goes = {}

    def _order(self, key):
        if key in self.stale:
            self.seq[key] = sorted(self.hist[key])
            self.stale.discard(key)
        return self.seq.get(key, ())

    def before(self, key, pos):
        book = self.hist.get(key)
        if not book:
            return None
        order = self._order(key)
        i = bisect.bisect_left(order, pos)
        return None if i == 0 else book[order[i - 1]]

    def sec_before(self, pos):
        i = bisect.bisect_left(self.jump, pos)
        return 0 if i == 0 else self.goes[self.jump[i - 1]]

    def put(self, key, pos, con):
        book = self.hist.get(key)
        if book is None:
            book = self.hist[key] = {}
        book[pos] = con
        self.stale.add(key)

    def drop(self, key, pos):
        del self.hist[key][pos]
        self.stale.add(key)

    def sec_put(self, pos, target):
        if pos not in self.goes:
            bisect.insort(self.jump, pos)
        self.goes[pos] = target

    def sec_drop(self, pos):
        if pos in self.goes:
            self.jump.pop(bisect.bisect_left(self.jump, pos))
            del self.goes[pos]

    def next_sec(self, pos):
        i = bisect.bisect_right(self.jump, pos)
        return self.jump[i] if i < len(self.jump) else None

    def board(self):
        held, masked, links = {}, [], {}
        for key, book in self.hist.items():
            if not book:
                continue
            con = book[max(book)]
            if key[0] == "l":
                links[key[1]] = con[1]
            elif con[0] == "v":
                held[(key[1], key[2])] = con[1]
            elif con[0] == "m":
                masked.append((key[1], key[2]))
        return held, sorted(masked), links


def read(st, sec, name, pos, trail):
    been = []
    at = sec
    while at not in been:
        been.append(at)
        key = ("s", at, name)
        if trail is not None:
            trail.add(key)
        con = st.before(key, pos)
        if con is not None:
            if con[0] == "v":
                return con[1]
            if con[0] == "m":
                return None
        lkey = ("l", at)
        if trail is not None:
            trail.add(lkey)
        nxt = st.before(lkey, pos)
        if nxt is None:
            return None
        at = nxt[1]
    return None
