import heapq

from lg import span


def run(store, pins, budget):
    gone = 0
    if store.count() <= budget:
        return gone
    heap = span.pairs(store, pins)
    heapq.heapify(heap)
    while heap and store.count() > budget:
        _won, edge, key, floor, last, lo, hi = heapq.heappop(heap)
        gone += span.collapse(store, key, floor, edge, last, lo, hi)
    return gone
