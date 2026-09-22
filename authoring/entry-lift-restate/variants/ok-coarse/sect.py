"""The board, and a climb that reports the names and the sections it touched.

This resolver does not remember which slot a lookup consulted, only which name and which
sections; that is coarser than it has to be, and reopens entries a finer index would leave
alone, but it can never leave one asleep.
"""
import bisect


class Store:
    __slots__ = ("at", "was", "jump", "goes")

    def __init__(self):
        self.at = {}
        self.was = {}
        self.jump = []
        self.goes = {}

    def before(self, key, pos):
        seq = self.at.get(key)
        if not seq:
            return None
        i = bisect.bisect_left(seq, pos)
        return None if i == 0 else self.was[(key, seq[i - 1])]

    def sec_before(self, pos):
        i = bisect.bisect_left(self.jump, pos)
        return 0 if i == 0 else self.goes[self.jump[i - 1]]

    def put(self, key, pos, con):
        seq = self.at.get(key)
        if seq is None:
            seq = self.at[key] = []
        bisect.insort(seq, pos)
        self.was[(key, pos)] = con

    def drop(self, key, pos):
        seq = self.at[key]
        seq.pop(bisect.bisect_left(seq, pos))
        del self.was[(key, pos)]

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
        for key, seq in self.at.items():
            if not seq:
                continue
            con = self.was[(key, seq[-1])]
            if key[0] == "l":
                links[key[1]] = con[1]
            elif con[0] == "v":
                held[(key[1], key[2])] = con[1]
            elif con[0] == "m":
                masked.append((key[1], key[2]))
        return held, sorted(masked), links


def read(st, sec, name, pos, saw):
    seen = set()
    at = sec
    while at not in seen:
        seen.add(at)
        if saw is not None:
            saw[0].add(name)
            saw[1].add(at)
        con = st.before(("s", at, name), pos)
        if con is not None:
            if con[0] == "v":
                return con[1]
            if con[0] == "m":
                return None
        nxt = st.before(("l", at), pos)
        if nxt is None:
            return None
        at = nxt[1]
    return None
