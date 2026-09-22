def values(ch):
    if ch.enc == "p":
        return ch.plain
    dic = ch.dic
    lit = ch.lit
    out = []
    for i, code in enumerate(ch.code):
        if code >= 0:
            out.append(dic[code])
        elif code == -1:
            out.append(None)
        else:
            out.append(lit[i])
    return out


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
