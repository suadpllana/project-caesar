"""The budgeted collapse loop.

The heap is settled once, at the start of the command, and then drained. A key's version
moves only when its table is rebuilt, so a pair that has stopped being valid is discarded
when it surfaces rather than searched for.
"""

import heapq

from lg import span


def run(store, pins, budget):
    gone = 0
    if store.count() <= budget:
        return gone
    span.settle(store, pins)
    heap = store.heap
    while heap and store.count() > budget:
        won, edge, key, floor, last, lo, hi, mark = heap[0]
        heapq.heappop(heap)
        if store.ver.get(key) != mark:
            continue
        gone += span.collapse(store, key, floor, edge, last, lo, hi)
    return gone
