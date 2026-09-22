LATEST = 1 << 60


def waits_on(held, wait, req):
    seen = set()
    for u in held.clashers(req.txn, req.tgt, req.mode):
        if u not in seen:
            seen.add(u)
            yield u
    for w in wait.clashing(req.tgt, req.mode):
        if w.txn != req.txn and w.seq < req.seq and w.txn not in seen:
            seen.add(w.txn)
            yield w.txn


class View:
    __slots__ = ("held", "wait", "bit", "reach")

    def __init__(self, held, wait):
        self.held = held
        self.wait = wait
        self.bit = {}
        self.reach = None

    def _bit(self, txn):
        b = self.bit.get(txn)
        if b is None:
            b = self.bit[txn] = 1 << len(self.bit)
        return b

    def _close(self):
        outs = {req.txn: list(waits_on(self.held, self.wait, req)) for req in self.wait.queue}
        for txn in outs:
            self._bit(txn)
        reach = {}
        index = {}
        low = {}
        stack = []
        onstack = set()
        count = [0]

        def strong(v):
            index[v] = low[v] = count[0]
            count[0] += 1
            stack.append(v)
            onstack.add(v)
            for u in outs.get(v, ()):
                if u not in outs:
                    continue
                if u not in index:
                    strong(u)
                    low[v] = min(low[v], low[u])
                elif u in onstack:
                    low[v] = min(low[v], index[u])
            if low[v] == index[v]:
                comp = []
                while True:
                    u = stack.pop()
                    onstack.discard(u)
                    comp.append(u)
                    if u == v:
                        break
                mask = 0
                for u in comp:
                    if len(comp) > 1:
                        mask |= self._bit(u)
                    for w in outs[u]:
                        mask |= self._bit(w) | reach.get(w, 0)
                for u in comp:
                    reach[u] = mask

        for v in outs:
            if v not in index:
                strong(v)
        self.reach = reach

    def depends(self, v, txn):
        if self.reach is None:
            self._close()
        return bool(self.reach.get(v, 0) & self._bit(txn))


def grantable(held, wait, txn, tgt, mode, seq, view=None):
    for _u in held.clashers(txn, tgt, mode):
        return False
    for w in wait.clashing(tgt, mode):
        if w.txn == txn or w.seq >= seq:
            continue
        if view is None:
            view = View(held, wait)
        if not view.depends(w.txn, txn):
            return False
    return True
