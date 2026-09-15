from mix import say


def add(h, name, n, w, cap):
    b = h.book
    b.names.append(name)
    b.size[name] = n
    b.weight[name] = w
    b.cap[name] = cap
    b.live.append(name)
    h.epoch[name] = 0
    h.cur[name] = 0
    h.cnt[name] = 0


def weigh(h, name, w):
    h.book.weight[name] = w


def drop(h, name):
    h.book.live.remove(name)


def at(h, name):
    if name in h.book.live:
        say.at(h, name, h.epoch[name], h.cur[name])
    else:
        say.at(h, name, None, None)
