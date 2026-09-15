def who(h):
    b = h.book
    best = None
    for name in b.live:
        if best is None:
            best = name
            continue
        mine = h.cnt[name] * b.weight[best]
        held = h.cnt[best] * b.weight[name]
        if mine < held or (mine == held and b.weight[name] > b.weight[best]):
            best = name
    return best
