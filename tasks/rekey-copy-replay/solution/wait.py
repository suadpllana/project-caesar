import heapq


class Wait:
    def __init__(self):
        self.pile = {}
        self.gone = {}
        self.n = 0

    def add(self, key, k):
        heapq.heappush(self.pile.setdefault(key, []), k)
        self.n += 1

    def drop(self, key, k):
        tags = self.gone.setdefault(key, {})
        tags[k] = tags.get(k, 0) + 1
        self.n -= 1

    def take(self, key):
        pile = self.pile.get(key)
        if not pile:
            return None
        tags = self.gone.get(key)
        while pile:
            k = heapq.heappop(pile)
            if tags and tags.get(k):
                tags[k] -= 1
                continue
            self.n -= 1
            return k
        return None

    def count(self):
        return self.n
