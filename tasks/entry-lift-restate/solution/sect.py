import bisect


class Store:
    __slots__ = ("wpos", "wcon", "secpos", "secto")

    def __init__(self):
        self.wpos = {}
        self.wcon = {}
        self.secpos = []
        self.secto = {}

    def before(self, key, pos):
        seq = self.wpos.get(key)
        if not seq:
            return None
        idx = bisect.bisect_left(seq, pos)
        if idx == 0:
            return None
        return self.wcon[(key, seq[idx - 1])]

    def sec_before(self, pos):
        idx = bisect.bisect_left(self.secpos, pos)
        return 0 if idx == 0 else self.secto[self.secpos[idx - 1]]

    def put(self, key, pos, con):
        seq = self.wpos.get(key)
        if seq is None:
            seq = self.wpos[key] = []
        bisect.insort(seq, pos)
        self.wcon[(key, pos)] = con

    def drop(self, key, pos):
        seq = self.wpos[key]
        seq.pop(bisect.bisect_left(seq, pos))
        del self.wcon[(key, pos)]

    def sec_put(self, pos, target):
        idx = bisect.bisect_left(self.secpos, pos)
        if idx == len(self.secpos) or self.secpos[idx] != pos:
            self.secpos.insert(idx, pos)
        self.secto[pos] = target

    def sec_drop(self, pos):
        idx = bisect.bisect_left(self.secpos, pos)
        if idx < len(self.secpos) and self.secpos[idx] == pos:
            self.secpos.pop(idx)
            del self.secto[pos]

    def next_sec(self, pos):
        idx = bisect.bisect_right(self.secpos, pos)
        return self.secpos[idx] if idx < len(self.secpos) else None

    def board(self):
        held, masked, links = {}, [], {}
        for key, seq in self.wpos.items():
            if not seq:
                continue
            con = self.wcon[(key, seq[-1])]
            if key[0] == "l":
                links[key[1]] = con[1]
            elif con[0] == "v":
                held[(key[1], key[2])] = con[1]
            elif con[0] == "m":
                masked.append((key[1], key[2]))
        return held, sorted(masked), links


def read(st, sec, name, pos, trail):
    seen = set()
    at = sec
    while True:
        if at in seen:
            return None
        seen.add(at)
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
        lcon = st.before(lkey, pos)
        if lcon is None:
            return None
        at = lcon[1]
