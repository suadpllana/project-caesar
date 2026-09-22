def key(row):
    return tuple((0, v, "") if type(v) is int else (1, 0, str(v)) for v in row)


def lines(st, got):
    out = []
    for q in st.asks:
        rows = sorted(set(got.get(q, ())), key=key)
        out.append("ans %s %d" % (q, len(rows)))
        for r in rows:
            out.append(" ".join([q] + [str(v) for v in r]))
    return out
