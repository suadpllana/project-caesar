from mix import perm


def take(h, name):
    b = h.book
    row = perm.order(h.seed, b.names.index(name), h.epoch[name], b.size[name])
    sample = row[h.cur[name]]
    h.cnt[name] += 1
    h.cur[name] += 1
    if h.cur[name] == b.size[name]:
        h.cur[name] = 0
        h.epoch[name] += 1
    return sample


def spent(h, name):
    cap = h.book.cap[name]
    return cap and h.epoch[name] > cap
