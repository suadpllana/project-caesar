class Find:
    __slots__ = ("st", "links")

    def __init__(self, st, links):
        self.st = st
        self.links = links

    def kids(self, link, keys):
        held = self.st.held(link.kid)
        got = []
        for key in sorted(held):
            val = held[key][link.ci]
            if val is not None and val in keys:
                got.append(key)
        return got
