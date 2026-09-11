def init(r):
    r.ck = {}


def save(r, tag):
    rows = []
    for name in r.map:
        rows.extend(r.par[name].keep())
    r.ck[tag] = rows


def load(r, tag):
    rows = [list(x) for x in r.ck[tag]]
    i = 0
    for name in r.map:
        c = r.par[name]
        left = c.n
        v = m = 0
        while left and i < len(rows):
            v, m = rows[i][1], rows[i][2]
            k = min(left, rows[i][0])
            left -= k
            rows[i][0] -= k
            if rows[i][0] == 0:
                i += 1
        c.put(v, m)
