# Correct variant "packed": same service, holders read off a precomputed map per table.


def start(locks):
    return tuple((None, 0, ()) for _ in range(locks))


def waiting(table, sess):
    for row in table:
        if sess in row[2]:
            return True
    return False


def offer(table, kind, lock, sess):
    if waiting(table, sess):
        return None
    if kind == "beat":
        held = {row[0] for row in table}
        return (None, table) if sess in held else None
    h, d, q = table[lock]
    if kind == "rel":
        if h != sess:
            return None
        if d == 1 and not q:
            new, out = (None, 0, ()), "free"
        elif d == 1:
            new, out = (q[0], 1, q[1:]), "pass"
        else:
            new, out = (h, d - 1, q), "keep"
    elif h is None:
        new, out = (sess, 1, ()), "grant"
    elif h == sess:
        new, out = (h, d + 1, q), "again"
    else:
        new, out = (h, d, q + (sess,)), "wait"
    return out, tuple(new if k == lock else row for k, row in enumerate(table))
