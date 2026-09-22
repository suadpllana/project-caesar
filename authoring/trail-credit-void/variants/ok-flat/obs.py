class Watch:
    __slots__ = ("keys", "was", "at_key")

    def __init__(self, bars):
        self.at_key = {}
        for one in bars:
            self.at_key.setdefault(one.key, []).append(one)
        self.keys = sorted(self.at_key)
        self.was = [None] * len(self.keys)

    def base(self, store):
        self.was = [store.val.get(key) for key in self.keys]

    def near(self, moved):
        out = []
        for key in moved:
            out.extend(self.at_key.get(key, ()))
        return sorted(out, key=lambda one: one.bid)

    def fires(self, bar, store):
        was = self.was[self.keys.index(bar.key)]
        now = store.val.get(bar.key)
        if bar.kind == "lost":
            return was is not None and now is None
        if bar.kind == "gain":
            return was is None and now is not None
        return not (was is None or now is None) and now < was

    def refresh(self, store, moved):
        spot = {key: i for i, key in enumerate(self.keys)}
        for key in moved:
            i = spot.get(key)
            if i is not None:
                self.was[i] = store.val.get(key)
