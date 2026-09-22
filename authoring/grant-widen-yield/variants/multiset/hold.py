"""Second correct implementation of the hold table, written to the same contract.

Where the reference keeps two integers per transaction and node, this keeps the children
themselves in two sets - the ones that need a shared intention above them and the ones that
need an exclusive one - so the cover is read off whether the exclusive set is empty. Holders
are grouped by mode rather than counted by mode, and the subtree walk is breadth first.

None of that is graded. It is here to show that the verifier is checking the contract and not
one arrangement of it.
"""
from lk import mode, name, say


class Book:
    __slots__ = ("ask", "bump", "hot", "isk", "ixk", "kat", "now", "stir", "seat", "who")

    def __init__(self):
        self.ask = {}
        self.isk = {}
        self.ixk = {}
        self.kat = {}
        self.now = {}
        self.who = {}
        self.seat = {}
        self.hot = set()
        self.stir = set()
        self.bump = set()

    # --- reading ------------------------------------------------------------------

    def eff(self, t, res):
        return self.now.get((t, res))

    def held(self, t):
        return [res for (u, res) in self.now if u == t]

    def at(self, res):
        return dict((u, self.now[(u, res)]) for u in self.who.get(res, ()))

    def clash(self, t, res, goal):
        book = self.seat.get(res)
        if not book:
            return False
        for bad in mode.FOE[goal]:
            crowd = book.get(bad)
            if crowd and (len(crowd) > 1 or t not in crowd):
                return True
        return False

    def foes(self, t, res, goal):
        book = self.seat.get(res, {})
        out = []
        for bad in mode.FOE[goal]:
            for u in book.get(bad, ()):
                if u != t:
                    out.append(u)
        return out

    def asked(self, t, res):
        return self.ask.get((t, res))

    def kids(self, t, res):
        return list(self.isk.get((t, res), ())) + list(self.ixk.get((t, res), ()))

    def carriers(self, res):
        return self.kat.get(res, ())

    def need(self, t, res):
        if self.ixk.get((t, res)):
            return "IX"
        return "IS" if self.isk.get((t, res)) else None

    def want(self, t, res):
        return mode.sup(self.asked(t, res), self.need(t, res))

    # --- writing ------------------------------------------------------------------

    def raise_ask(self, t, res, m, out):
        key = (t, res)
        self.ask[key] = mode.sup(self.ask.get(key), m)
        self.retune(t, res, out)

    def set_ask(self, t, res, m, out):
        self.ask[(t, res)] = m
        self.retune(t, res, out)

    def retune(self, t, res, out):
        self.mark(t, res, self.want(t, res), out)

    def mark(self, t, res, val, out, tag="free"):
        key = (t, res)
        old = self.now.get(key)
        if old == val:
            return
        self.touch(res)
        self.chair(res, t, old, val)
        if val is None:
            del self.now[key]
            self.who.get(res, set()).discard(t)
            out.append(say.give(t, res, old) if tag == "give" else say.free(t, res))
        else:
            self.now[key] = val
            self.who.setdefault(res, set()).add(t)
            rising = old is None or mode.sup(old, val) == val
            out.append((say.hold if rising else say.thin)(t, res, val))
        self.shift(t, res, old, val, out)

    def chair(self, res, t, old, new):
        book = self.seat.setdefault(res, {})
        if old is not None:
            book[old].discard(t)
            if not book[old]:
                del book[old]
        if new is not None:
            book.setdefault(new, set()).add(t)
        if not book:
            del self.seat[res]

    def touch(self, res):
        self.hot.add(res)
        self.stir.add(res)

    def shift(self, t, child, old, new, out):
        par = name.up(child)
        if par is None:
            return
        self.count(t, par, child, old, new)
        self.retune(t, par, out)

    def count(self, t, par, child, old, new):
        key = (t, par)
        low = self.isk.setdefault(key, set())
        high = self.ixk.setdefault(key, set())
        low.discard(child)
        high.discard(child)
        if new is not None:
            (high if mode.cov(new) == "IX" else low).add(child)
        if low or high:
            self.kat.setdefault(par, set()).add(t)
        else:
            self.kat.get(par, set()).discard(t)
        self.bump.add((t, par))

    def erase(self, t, res):
        key = (t, res)
        was = self.now.pop(key, None)
        if was is not None:
            self.touch(res)
            self.who.get(res, set()).discard(t)
            self.chair(res, t, was, None)
        self.ask.pop(key, None)
        self.isk.pop(key, None)
        self.ixk.pop(key, None)
        self.kat.get(res, set()).discard(t)
        par = name.up(res)
        if par is not None:
            self.count(t, par, res, was, None)
        return was

    def sub(self, t, top):
        found = []
        queue = [top]
        while queue:
            here = queue.pop(0)
            if (t, here) in self.now:
                found.append(here)
            queue.extend(self.kids(t, here))
        found.sort(key=name.deep)
        return found

    def strip(self, t, top, out, tag):
        gone = []
        nodes = self.sub(t, top)
        if not nodes:
            return gone
        for res in nodes:
            gone.append((res, self.asked(t, res)))
            was = self.erase(t, res)
            out.append(say.give(t, res, was) if tag == "give" else say.free(t, res))
        par = name.up(top)
        if par is not None:
            self.retune(t, par, out)
        return gone

    def forget(self, t):
        for res in self.held(t):
            self.touch(res)
            was = self.now.pop((t, res), None)
            self.who.get(res, set()).discard(t)
            self.chair(res, t, was, None)
            self.kat.get(res, set()).discard(t)
        for key in [k for k in self.ask if k[0] == t]:
            del self.ask[key]
        for key in [k for k in self.isk if k[0] == t]:
            del self.isk[key]
        for key in [k for k in self.ixk if k[0] == t]:
            del self.ixk[key]
