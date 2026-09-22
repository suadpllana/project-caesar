# Correct variant "topdown": the table as rows (fp.py needs them), requests answered by
# rebuilding one row in a list.


def start(locks):
    return tuple((None, 0, ()) for _ in range(locks))


def waiting(table, sess):
    return any(sess in row[2] for row in table)


def offer(table, kind, lock, sess):
    if any(sess in row[2] for row in table):
        return None
    if kind == "beat":
        return (None, table) if any(row[0] == sess for row in table) else None
    rows = list(table)
    h, d, q = rows[lock]
    if kind == "acq":
        if h is None:
            rows[lock], out = (sess, 1, q), "grant"
        elif h == sess:
            rows[lock], out = (h, d + 1, q), "again"
        else:
            rows[lock], out = (h, d, q + (sess,)), "wait"
    elif h != sess:
        return None
    elif d >= 2:
        rows[lock], out = (h, d - 1, q), "keep"
    elif len(q) == 0:
        rows[lock], out = (None, 0, ()), "free"
    else:
        rows[lock], out = (q[0], 1, tuple(q[1:])), "pass"
    return out, tuple(rows)
