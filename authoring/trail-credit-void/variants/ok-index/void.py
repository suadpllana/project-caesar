from collections import deque


def fire(book, bar, delta):
    reach = {bar.goal}
    line = deque([bar.goal])
    while line:
        here = line.popleft()
        for down in book.under(here):
            if down not in reach:
                reach.add(down)
                line.append(down)
    lost = []
    for gid in sorted(reach):
        if book.held(gid):
            book.drop(gid)
            delta[gid] = delta.get(gid, 0) - 1
            lost.append(gid)
    book.shut(bar.goal)
    return lost
