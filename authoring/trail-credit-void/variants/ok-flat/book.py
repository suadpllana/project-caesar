from crd import pred

OPEN = 0
HELD = 1
SHUT = 2


class Book:
    __slots__ = ("goals", "state", "ready", "at_key", "dep", "queue")

    def __init__(self, goals):
        self.goals = goals
        self.state = [OPEN] * len(goals)
        self.ready = [len(one.pre) for one in goals]
        self.at_key = {}
        self.dep = [[] for _ in goals]
        for one in goals:
            self.at_key.setdefault(one.key, []).append(one.gid)
            for up in one.pre:
                self.dep[up].append(one.gid)
        self.queue = set(one.gid for one in goals if not one.pre)

    def near(self, moved):
        cand = self.queue
        self.queue = set()
        for key in moved:
            cand.update(self.at_key.get(key, ()))
        return sorted(cand)

    def credit(self, store, moved, delta):
        state = self.state
        ready = self.ready
        goals = self.goals
        won = []
        for gid in self.near(moved):
            here = state[gid]
            if here == SHUT:
                if not pred.holds(goals[gid], store):
                    state[gid] = OPEN
            elif here == OPEN and ready[gid] == 0 and pred.holds(goals[gid], store):
                state[gid] = HELD
                delta[gid] = delta.get(gid, 0) + 1
                won.append(gid)
        return won

    def shut(self, gid):
        self.state[gid] = SHUT
        self.queue.add(gid)

    def settle(self, delta):
        ready = self.ready
        for gid, moved in delta.items():
            if moved > 0:
                for down in self.dep[gid]:
                    ready[down] -= 1
                    if ready[down] == 0:
                        self.queue.add(down)
            elif moved < 0:
                for down in self.dep[gid]:
                    ready[down] += 1

    def held(self, gid):
        return self.state[gid] == HELD
