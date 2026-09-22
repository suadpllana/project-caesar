"""The order the plan runs in.

Every rerun and every computed partition comes after the lines of what it read - including a
roll-up it read in place of a day of hours, which is not a declared read and may be declared
after its reader. Of the lines free to go next, the one whose partition ends first goes, then
the one whose dataset is declared first. The holds follow, by end hour and then declaration.
"""
import heapq

from plan.span import ends


def order(pp, book):
    def key(k):
        return ends(pp, *k), pp.pos[k[0]]

    waiting = {k: {d for d in book.rec[k].after if d in book.made} for k in book.made}
    users = {}
    for k, before in waiting.items():
        for d in before:
            users.setdefault(d, []).append(k)
    free = [(key(k), k) for k, before in waiting.items() if not before]
    heapq.heapify(free)
    rows = []
    while free:
        _, k = heapq.heappop(free)
        r = book.rec[k]
        rows.append(("run", k[0], k[1], r.word) if r.line == "run" else ("temp", k[0], k[1]))
        for u in users.get(k, ()):
            waiting[u].discard(k)
            if not waiting[u]:
                heapq.heappush(free, (key(u), u))
    for k in sorted(book.holds, key=key):
        rows.append(("hold", k[0], k[1], book.rec[k].word))
    return rows
