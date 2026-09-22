HEAD = 8
ENT = 2
KID = 2


def span(ents, kids):
    n = HEAD + kids * KID
    for e in ents:
        n += ENT + len(e)
    return n


def bulk(tr, pid):
    page = tr.at(pid)
    if page.leaf:
        return span(page.keys, 0)
    return span(page.seps, len(page.kids))


def over(tr, pid):
    return bulk(tr, pid) > tr.cap


def under(tr, pid):
    return bulk(tr, pid) < tr.floor
