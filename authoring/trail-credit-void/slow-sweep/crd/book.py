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

    def credit(self, store, moved, delta):
        state = self.state
        goals = self.goals
        was = list(state)
        won = []
        for gid in range(len(goals)):
            here = state[gid]
            one = goals[gid]
            if here == SHUT:
                if not pred.holds(one, store):
                    state[gid] = OPEN
            elif here == OPEN:
                ok = True
                for up in one.pre:
                    if was[up] != HELD:
                        ok = False
                        break
                if ok and pred.holds(one, store):
                    state[gid] = HELD
                    delta[gid] = delta.get(gid, 0) + 1
                    won.append(gid)
        return won

    def shut(self, gid):
        self.state[gid] = SHUT

    def settle(self, delta):
        return None

    def held(self, gid):
        return self.state[gid] == HELD
