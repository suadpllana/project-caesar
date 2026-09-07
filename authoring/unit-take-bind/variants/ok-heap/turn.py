import heapq

from prog.deck import OWN, UNIT, at, blank, put
from prog.unit import find

from .pick import settle
from .show import out_all, out_one
from .step import cost, srcs


def run(prog):
    deck = blank(prog.units)
    heap = []
    for u in prog.units.values():
        for x in u.owns:
            heapq.heappush(heap, (0, u.nm, x, OWN, u.nm))
        for x, vn in u.als:
            if find(prog, vn) is not None:
                heapq.heappush(heap, (0, u.nm, x, UNIT, vn))

    def offer(u, rank):
        for s, what in u.pulls:
            for vn, rs in srcs(deck, prog, u, s):
                if what == "*":
                    for x, b in out_all(deck, prog, vn):
                        if cost(rs, b[2]) == rank and at(deck, u.nm, x) is None:
                            heapq.heappush(heap, (rank, u.nm, x, b[0], b[1]))
                else:
                    b = out_one(deck, prog, vn, what)
                    if b is None or at(deck, u.nm, what) is not None:
                        continue
                    if cost(rs, b[2]) == rank:
                        heapq.heappush(heap, (rank, u.nm, what, b[0], b[1]))

    rank = 0
    while True:
        seen = {}
        while heap and heap[0][0] == rank:
            _, un, x, kind, tgt = heapq.heappop(heap)
            if at(deck, un, x) is None:
                seen.setdefault((un, x), []).append((kind, tgt))
        for (un, x), cands in seen.items():
            kind, tgt = settle(cands)
            put(deck, un, x, kind, tgt, rank)
        rank += 1
        for u in prog.units.values():
            offer(u, rank)
        if not heap:
            return deck
