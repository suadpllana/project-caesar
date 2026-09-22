from lk import mode, name, say


class Book:
    __slots__ = ("now", "who")

    def __init__(self):
        self.now = {}
        self.who = {}

    def eff(self, t, res):
        row = self.now.get(t)
        return row.get(res) if row else None

    def held(self, t):
        return list(self.now.get(t, ()))

    def at(self, res):
        return self.who.get(res, {})

    def put(self, t, res, m, out):
        old = self.now.get(t, {}).get(res)
        val = mode.sup(old, m)
        if old == val:
            return
        self.now.setdefault(t, {})[res] = val
        self.who.setdefault(res, {})[t] = val
        out.append(say.hold(t, res, val))

    def cut(self, t, res, out, tag):
        old = self.now.get(t, {}).pop(res, None)
        if old is None:
            return None
        row = self.who.get(res)
        row.pop(t, None)
        if not row:
            self.who.pop(res, None)
        out.append(say.give(t, res, old) if tag == "give" else say.free(t, res))
        return old

    def sub(self, t, top):
        stem = top + "."
        found = [r for r in self.now.get(t, ()) if r == top or r.startswith(stem)]
        found.sort(key=name.deep)
        return found

    def forget(self, t):
        for res in self.now.pop(t, {}):
            row = self.who.get(res)
            if row is not None:
                row.pop(t, None)
                if not row:
                    self.who.pop(res, None)
