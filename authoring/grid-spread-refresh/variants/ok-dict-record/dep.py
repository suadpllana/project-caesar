"""Correct variant: the read record as two dictionaries instead of one list.

The reference keeps a cell's reads as the list the Watch produced, in order, and tests it
by walking that list. Here a cell keeps a dict of address to observed value for the values
it read and a second dict for the cells it probed, and the inverted index is built from
their keys. The reads a range performs collapse to one entry per address, so the record is
smaller and the staleness test walks a set rather than a sequence - the same rule, a
different representation.
"""


class Watch:
    def __init__(self, st):
        self.st = st
        self.saw = {}
        self.was = {}
        self.rd = []

    def val(self, ad):
        v = self.st.val(ad)
        self.saw[ad] = v
        self.rd.append(("v", ad, v))
        return v

    def own(self, ad):
        b = self.st.own(ad)
        self.was[ad] = b
        self.rd.append(("o", ad, b))
        return b


class Dep:
    def __init__(self):
        self.rec = {}
        self.idx = {}

    def watch(self, st):
        return Watch(st)

    def note(self, ad, rd):
        saw, was = {}, {}
        for kind, t, seen in rd:
            (saw if kind == "v" else was)[t] = seen
        self.drop(ad)
        self.rec[ad] = (saw, was)
        for t in list(saw) + list(was):
            self.idx.setdefault(t, set()).add(ad)

    def drop(self, ad):
        pair = self.rec.pop(ad, None)
        if pair is None:
            return
        for t in list(pair[0]) + list(pair[1]):
            s = self.idx.get(t)
            if s is not None:
                s.discard(ad)
                if not s:
                    del self.idx[t]

    def readers(self, ad):
        return self.idx.get(ad, ())

    def touched(self, ad):
        pair = self.rec.get(ad)
        return [] if pair is None else list(pair[0]) + list(pair[1])

    def stale(self, st, ad):
        pair = self.rec.get(ad)
        if pair is None:
            return True
        for t, seen in pair[0].items():
            if st.val(t) != seen:
                return True
        for t, seen in pair[1].items():
            if st.own(t) != seen:
                return True
        return False
