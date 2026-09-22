def form(ref, vals):
    """How a row's values stand against a reference: None when the reference is inert for
    them, False when it is broken (full, some columns null but not all), and otherwise the
    positions within the reference's columns that carry a value, which are the positions a
    matched key row has to agree on."""
    got = tuple(i for i, c in enumerate(ref.cols) if vals[c] is not None)
    if not got:
        return None
    if len(got) < len(ref.cols):
        if ref.mode == "simple":
            return None
        if ref.mode == "full":
            return False
    return got


class Book:
    """Value indexes over the store as it stands. A partial reference can leave any subset
    of its columns null, so rows are indexed once per pattern of non-null positions: key
    rows by the projection of their key onto the pattern, referencing rows by the projection
    of their own values. Built lazily and thrown away whenever the store changes."""

    def __init__(self, store):
        self.store = store
        self.up = {}
        self.down = {}

    def ups(self, ref, vals, pat=None):
        """Ids of the key rows that `vals` matches through `ref`."""
        if pat is None:
            pat = form(ref, vals)
            if not pat:
                return ()
        slot = (ref.key.name, pat)
        idx = self.up.get(slot)
        if idx is None:
            idx = {}
            kc = [ref.key.cols[i] for i in pat]
            data = self.store.data[ref.key.tab.name]
            for pid, pv in data.items():
                idx.setdefault(tuple(pv[c] for c in kc), []).append(pid)
            self.up[slot] = idx
        return idx.get(tuple(vals[ref.cols[i]] for i in pat), ())

    def downs(self, ref, pvals):
        """Ids of the rows that match, through `ref`, a key row holding `pvals`."""
        idx = self.down.get(ref.name)
        if idx is None:
            idx = {}
            data = self.store.data[ref.tab.name]
            for cid, cv in data.items():
                pat = form(ref, cv)
                if pat:
                    idx.setdefault(pat, {}).setdefault(
                        tuple(cv[ref.cols[i]] for i in pat), []).append(cid)
            self.down[ref.name] = idx
        out = []
        for pat, table in idx.items():
            hit = table.get(tuple(pvals[ref.key.cols[i]] for i in pat))
            if hit:
                out.extend(hit)
        return out


def book(store):
    got = getattr(store, "book", None)
    if got is None:
        got = store.book = Book(store)
    return got


def spoil(store):
    store.book = None
