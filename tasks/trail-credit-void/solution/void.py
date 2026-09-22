from crd import book as bk


def cone(book, gid):
    seen = {gid}
    stack = [gid]
    while stack:
        here = stack.pop()
        for down in book.dep[here]:
            if down not in seen:
                seen.add(down)
                stack.append(down)
    return sorted(seen)


def fire(book, bar, delta):
    state = book.state
    lost = []
    for gid in cone(book, bar.goal):
        if state[gid] == bk.HELD:
            state[gid] = bk.OPEN
            delta[gid] = delta.get(gid, 0) - 1
            lost.append(gid)
    book.shut(bar.goal)
    return lost
