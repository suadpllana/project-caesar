class Watch:
    __slots__ = ("seen", "keys", "at_key")

    def __init__(self, bars):
        self.at_key = {}
        for one in bars:
            self.at_key.setdefault(one.key, []).append(one)
        self.keys = tuple(self.at_key)
        self.seen = {}

    def base(self, store):
        self.seen = dict(store.val)

    def near(self, moved):
        out = []
        for key in moved:
            out.extend(self.at_key.get(key, ()))
        out.sort(key=lambda one: one.bid)
        return out

    def fires(self, bar, store):
        was = self.seen.get(bar.key)
        now = store.val.get(bar.key)
        kind = bar.kind
        if kind == "lost":
            return was is not None and now is None
        if kind == "gain":
            return was is None and now is not None
        return was is not None and now is not None and now < was

    def refresh(self, store, moved):
        self.seen = dict(store.val)
