from lg import span


def run(store, pins, budget):
    gone = 0
    if store.count() <= budget:
        return gone
    bins = span.board(store, pins)
    for won in sorted(bins, reverse=True):
        for _edge, key, row in bins[won]:
            if store.count() <= budget:
                return gone
            gone += span.collapse(store, key, row)
    return gone
