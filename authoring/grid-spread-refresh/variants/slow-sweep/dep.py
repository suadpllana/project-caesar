"""Reference dependency record.

Every evaluation goes through a Watch, so the record of a cell is the reads its last
evaluation actually performed, with the value each read observed at that moment. Both
kinds are recorded: `v` for the displayed value of a cell, `o` for whether a cell holds
its own content, which is what a block-valued formula probes for the cells it would
occupy. Recording the observed value is what makes the staleness test exact: a cell is
out of date only when one of those reads would now give something different, never
merely because a cell it read was recomputed.

The inverted index maps an address to the cells that read it, under either kind, and is
rebuilt for a cell whenever its record is replaced. It is the only thing that keeps the
cost of an edit proportional to what the edit can reach rather than to the size of the
sheet.
"""


class Watch:
    def __init__(self, st):
        self.st = st
        self.rd = []

    def val(self, ad):
        v = self.st.val(ad)
        self.rd.append(("v", ad, v))
        return v

    def own(self, ad):
        b = self.st.own(ad)
        self.rd.append(("o", ad, b))
        return b


class Dep:
    def __init__(self):
        self.rec = {}
        self.idx = {}

    def watch(self, st):
        return Watch(st)

    def note(self, ad, rd):
        self.drop(ad)
        self.rec[ad] = rd
        for _, t, _ in rd:
            s = self.idx.get(t)
            if s is None:
                s = self.idx[t] = set()
            s.add(ad)

    def drop(self, ad):
        for _, t, _ in self.rec.pop(ad, ()):
            s = self.idx.get(t)
            if s is not None:
                s.discard(ad)
                if not s:
                    del self.idx[t]

    def readers(self, ad):
        return self.idx.get(ad, ())

    def touched(self, ad):
        return [t for _, t, _ in self.rec.get(ad, ())]

    def stale(self, st, ad):
        rd = self.rec.get(ad)
        if rd is None:
            return True
        for k, t, was in rd:
            now = st.own(t) if k == "o" else st.val(t)
            if now != was:
                return True
        return False
