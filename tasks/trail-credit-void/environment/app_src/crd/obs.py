class Watch:
    __slots__ = ("seen", "bars")

    def __init__(self, bars):
        self.bars = list(bars)
        self.seen = {}

    def base(self, store):
        self.seen = dict(store.val)

    def near(self, moved):
        return list(self.bars)

    def fires(self, bar, store):
        was = self.seen.get(bar.key)
        now = store.val.get(bar.key)
        kind = bar.kind
        if kind == "lost":
            return now is None
        if kind == "gain":
            return now is not None
        return was != now

    def refresh(self, store, moved):
        self.seen = dict(store.val)
