from crd import pred


class Book:
    __slots__ = ("goals", "won", "dep")

    def __init__(self, goals):
        self.goals = goals
        self.won = set()
        self.dep = [[] for _ in goals]
        for one in goals:
            for up in one.pre:
                self.dep[up].append(one.gid)

    def credit(self, store, moved, delta):
        won = self.won
        fresh = []
        for one in self.goals:
            if one.gid in won and not pred.holds(one, store):
                won.discard(one.gid)
        again = True
        while again:
            again = False
            for one in self.goals:
                if one.gid in won:
                    continue
                if not all(up in won for up in one.pre):
                    continue
                if pred.holds(one, store):
                    won.add(one.gid)
                    fresh.append(one.gid)
                    again = True
        fresh.sort()
        return fresh

    def shut(self, gid):
        self.won.discard(gid)

    def settle(self, delta):
        return None

    def held(self, gid):
        return gid in self.won
