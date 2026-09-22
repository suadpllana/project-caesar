def start(locks):
    return tuple((None, 0, ()) for _ in range(locks))


def waiting(table, sess):
    return any(sess in q for _h, _d, q in table)


def offer(table, kind, lock, sess):
    if waiting(table, sess):
        return None
    if kind == "beat":
        return None, table
    h, d, q = table[lock]
    if kind == "acq":
        if h is None:
            row, out = (sess, 1, q), "grant"
        elif h == sess:
            row, out = (h, d, q), "again"
        else:
            row, out = (h, d, q + (sess,)), "wait"
    else:
        if h != sess:
            return None
        if q:
            row, out = (q[0], 1, q[1:]), "pass"
        else:
            row, out = (None, 0, ()), "free"
    return out, table[:lock] + (row,) + table[lock + 1:]


def asks(table, locks, sessions):
    for lock in range(locks):
        for sess in range(sessions):
            yield "acq", lock, sess
    for lock, (h, _d, _q) in enumerate(table):
        if h is not None:
            yield "rel", lock, h
    for sess in range(sessions):
        yield "beat", None, sess
