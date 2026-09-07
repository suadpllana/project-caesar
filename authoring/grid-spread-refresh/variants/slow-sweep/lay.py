"""Reference block layout.

A block-valued formula occupies the cells under it in its own column. Three things decide
whether it fits, and all three have to be settled before anything is written:

  * the last cell it would occupy has to be inside the sheet;
  * none of the cells it would occupy may hold its own content - and every one of those
    cells is probed through the Watch, including in the blocked case, so that clearing a
    blocker or planting a new one brings the formula back up to date;
  * none of the cells it would occupy may be a cell the formula itself read, which would
    make the block its own input.

Laying a block down writes the elements one cell at a time, so a reader of one occupied
cell is only affected when that cell's element moves. Giving a block up releases the cells
it no longer occupies, and leaves alone any cell that has since been given its own
content.
"""


class Lay:
    def __init__(self):
        self.fp = {}
        self.by = {}

    def block(self, st, ad):
        n = st.node(ad)
        return n is not None and n[0] == "c" and n[1] in ("RUN", "LIST", "TOP")

    def fit(self, st, ad, vals, w):
        r, c = ad
        want = [(r + i, c) for i in range(1, len(vals))]
        room = True
        taken = False
        for t in want:
            if t[0] > st.nr:
                room = False
                continue
            if w.own(t):
                taken = True
        if not room or taken:
            return None
        read = set(t for k, t, _ in w.rd if k == "v")
        for t in want:
            if t in read:
                return None
        return want

    def put(self, st, ad, vals, tgt):
        keep = set(tgt)
        for t in self.fp.get(ad, ()):
            if t not in keep and self.by.get(t) == ad:
                del self.by[t]
                if not st.own(t):
                    st.show(t, None)
        for i, t in enumerate(tgt):
            self.by[t] = ad
            st.show(t, vals[i + 1])
        if tgt:
            self.fp[ad] = tgt
        else:
            self.fp.pop(ad, None)

    def wipe(self, st, ad):
        for t in self.fp.pop(ad, ()):
            if self.by.get(t) == ad:
                del self.by[t]
                if not st.own(t):
                    st.show(t, None)

