class Req:
    __slots__ = ("txn", "tgt", "mode")

    def __init__(self, txn, tgt, mode):
        self.txn = txn
        self.tgt = tgt
        self.mode = mode


class Wait:
    __slots__ = ("q", "of")

    def __init__(self):
        self.q = {}
        self.of = {}

    def add(self, req):
        self.q.setdefault(req.tgt, []).append(req)
        self.of[req.txn] = req

    def remove(self, req):
        self.q[req.tgt].remove(req)
        if not self.q[req.tgt]:
            del self.q[req.tgt]
        del self.of[req.txn]

    def on(self, tgt):
        return list(self.q.get(tgt, ()))

    def targets(self):
        return list(self.q)
