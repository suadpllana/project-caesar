"""Variant B: a heap over the answered outstanding commands, with lazy deletion."""
import heapq


class Pend(object):
    def __init__(self):
        self.order = []
        self.heap = []
        self.dead = set()
        self.tick = 0

    def add(self, rec):
        self.tick += 1
        rec_id = self.tick
        self.order.append((rec_id, rec))
        if rec.pos is not None:
            heapq.heappush(self.heap, (rec.pos, rec_id, rec))

    def empty(self):
        return not self.order

    def first(self):
        return self.order[0][1]

    def fastest(self):
        while self.heap and self.heap[0][1] in self.dead:
            heapq.heappop(self.heap)
        if not self.heap:
            return self.order[0][1]
        return self.heap[0][2]

    def drop(self, rec):
        for at in range(len(self.order)):
            if self.order[at][1] is rec:
                self.dead.add(self.order[at][0])
                self.order.pop(at)
                return
