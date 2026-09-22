from crd import pred


class Book:
    __slots__ = ("goals", "win", "bad", "at_obs", "now", "at_key", "dep", "wake")

    def __init__(self, goals):
        self.goals = goals
        self.win = set()
        self.bad = set()
        self.at_obs = {}
        self.now = 0
        self.at_key = {}
        self.dep = {}
        for one in goals:
            self.at_key.setdefault(one.key, []).append(one.gid)
            for up in one.pre:
                self.dep.setdefault(up, []).append(one.gid)
        self.wake = set(one.gid for one in goals if not one.pre)

    def under(self, gid):
        return self.dep.get(gid, ())

    def credit(self, store, moved, delta):
        self.now += 1
        now = self.now
        look = set(self.wake)
        self.wake = set()
        for key in moved:
            look.update(self.at_key.get(key, ()))
        win, bad, at_obs = self.win, self.bad, self.at_obs
        won = []
        for gid in sorted(look):
            one = self.goals[gid]
            if gid in bad:
                if not pred.holds(one, store):
                    bad.discard(gid)
                continue
            if gid in win:
                continue
            ready = True
            for up in one.pre:
                if up not in win or at_obs[up] >= now:
                    ready = False
                    break
            if ready and pred.holds(one, store):
                win.add(gid)
                at_obs[gid] = now
                delta[gid] = delta.get(gid, 0) + 1
                won.append(gid)
        return won

    def drop(self, gid):
        self.win.discard(gid)
        self.at_obs.pop(gid, None)

    def shut(self, gid):
        self.bad.add(gid)
        self.wake.add(gid)

    def settle(self, delta):
        for gid in delta:
            for down in self.under(gid):
                self.wake.add(down)

    def held(self, gid):
        return gid in self.win
