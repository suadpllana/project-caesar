class Frame:
    def __init__(self):
        self.rows = []

    def begin(self, ui):
        pool = list(ui.nd.values()) + [s.root for s in ui.scr.values()]
        state = {n: (n.par, tuple(n.kids), frozenset(n.fl), n.grp) for n in pool}
        self.rows.append((dict(ui.nd), state))

    def commit(self, ui):
        self.rows.pop()

    def abort(self, ui):
        nodes, state = self.rows.pop()
        ui.nd = nodes
        for n, (par, kids, flags, group) in state.items():
            n.par = par
            n.kids = list(kids)
            n.fl = set(flags)
            n.grp = group
