class Watch:
    def __init__(self, st):
        self.st = st
        self.rd = []

    def val(self, ad):
        v = self.st.val(ad)
        self.rd.append(ad)
        return v

    def own(self, ad):
        return self.st.own(ad)


class Dep:
    def __init__(self):
        self.rec = {}
        self.idx = {}

    def watch(self, st):
        return Watch(st)

    def note(self, ad, rd):
        self.drop(ad)
        self.rec[ad] = rd
        for t in rd:
            s = self.idx.get(t)
            if s is None:
                s = self.idx[t] = set()
            s.add(ad)

    def drop(self, ad):
        for t in self.rec.pop(ad, ()):
            s = self.idx.get(t)
            if s is not None:
                s.discard(ad)
                if not s:
                    del self.idx[t]

    def readers(self, ad):
        return self.idx.get(ad, ())
