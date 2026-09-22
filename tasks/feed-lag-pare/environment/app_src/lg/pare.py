from lg import span


def run(store, pins, budget):
    gone = 0
    while store.count() >= budget:
        rows = span.pairs(store, pins)
        if not rows:
            break
        key, floor, edge, _count, first = rows[0]
        gone += span.collapse(store, pins, key, floor, edge, first)
    return gone
