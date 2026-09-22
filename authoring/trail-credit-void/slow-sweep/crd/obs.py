class Watch:
    __slots__ = ("seen", "keys", "at_key")

    def __init__(self, bars):
        self.at_key = {}
        for one in bars:
            self.at_key.setdefault(one.key, []).append(one)
        self.keys = tuple(self.at_key)
        self.seen = {}

    def base(self, store):
        got = store.val.get
        self.seen = {key: got(key) for key in self.keys}

    def near(self, moved):
        out = []
        for group in self.at_key.values():
            out.extend(group)
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
        seen = self.seen
        got = store.val.get
        for key in moved:
            if key in seen:
                seen[key] = got(key)
