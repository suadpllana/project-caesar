def values(ch, pg):
    if pg.form == "v":
        return pg.toks
    dic = ch.dic
    return [None if t is None else dic[t] for t in pg.toks]


def sat(cond, v):
    k = cond.kind
    if v is None:
        return k == "nu"
    if k == "nu":
        return False
    if k == "nn":
        return True
    if k == "ge":
        return v >= cond.v
    if k == "le":
        return v <= cond.v
    if k == "eq":
        return v == cond.v
    return v != cond.v
