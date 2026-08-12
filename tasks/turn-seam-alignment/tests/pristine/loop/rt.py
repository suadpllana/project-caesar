from loop import rec
from loop.ep import Ep


class RT:
    def __init__(self, cfg, tok, net, gen, store):
        self.cfg = cfg
        self.tok = tok
        self.net = net
        self.gen = gen
        self.store = store
        self.eps = {}
        self.trace = []
        self.ids = {}
        self.spans = {}

    def open(self, eid, salt):
        self.eps[eid] = Ep(self, eid, salt)
        self.note("open", eid)
        return self.eps[eid]

    def ep(self, eid):
        return self.eps[eid]

    def note(self, kind, eid):
        self.trace.append(kind + ":" + eid)

    def done(self, eid, seq, turns):
        self.ids[eid] = list(seq)
        self.spans[eid] = [list(p) for p in rec.spans(seq, turns)]
        self.store.drop(eid)

    def report(self):
        return {
            "enc_chars": self.tok.n_chars,
            "enc_calls": self.tok.n_calls,
            "fwd": self.net.n_fwd,
            "trace": list(self.trace),
            "ids": {k: list(v) for k, v in sorted(self.ids.items())},
            "spans": {k: [list(s) for s in v] for k, v in sorted(self.spans.items())},
        }
