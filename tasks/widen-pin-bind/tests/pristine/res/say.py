def lines(k, res):
    out = []
    if res.how == "bind":
        for site, ent in res.binds:
            out.append("bind %d %d %d" % (k, site, ent))
        for ent, kind in res.pins:
            out.append("pin %d %s" % (ent, kind))
        out.append("res %d %s" % (k, res.kind))
    else:
        out.append("res %d %s" % (k, res.how))
    return out


def tally(n):
    return "tally %d" % n
