class Route:
    def __init__(self, core, ms, spec, wm):
        self.core = core
        self.ms = ms
        self.spec = spec
        self.wm = wm

    def kinds_for(self, src):
        out = []
        for kind, srcs in self.spec.items():
            if src in srcs:
                out.append(kind)
        return sorted(out)

    def push(self, d, edits):
        gs = set()
        for e in edits:
            gs.add(e.g)
        for g in sorted(gs):
            for kind in self.kinds_for(d.src):
                self.core.rebuild(g, kind, self.ms.group(d.src, g))
        return sorted(gs)
