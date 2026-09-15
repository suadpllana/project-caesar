from mix import say


def add(h, name, n, w, cap):
    b = h.book
    b.names.append(name)
    b.size[name] = n
    b.wt[name] = w
    b.cap[name] = cap
    b.live.append(name)
    h.ep[name] = 0
    h.cur[name] = 0
    h.cnt[name] = 0


def weigh(h, name, w):
    h.book.wt[name] = w


def drop(h, name):
    h.book.live.remove(name)


def at(h, name):
    say.at(h, name, 0, 0)
