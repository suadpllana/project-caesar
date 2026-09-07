class Lay:
    def __init__(self):
        self.fp = {}

    def fit(self, st, ad, vals, w):
        r, c = ad
        want = [(r + i, c) for i in range(1, len(vals))]
        for t in want:
            if t[0] > st.nr or w.own(t):
                return None
        return want

    def put(self, st, ad, vals, tgt):
        for i, t in enumerate(tgt):
            st.show(t, vals[i + 1])
        self.fp[ad] = tgt

    def wipe(self, st, ad):
        for t in self.fp.pop(ad, ()):
            if not st.own(t):
                st.show(t, None)
