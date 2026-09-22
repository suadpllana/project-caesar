HEAD = 8
ENT = 2
KID = 2


def common(ents):
    if not ents:
        return ""
    out = ents[0]
    for e in ents[1:]:
        k = 0
        top = len(out) if len(out) < len(e) else len(e)
        while k < top and out[k] == e[k]:
            k += 1
        out = out[:k]
        if not out:
            break
    return out


def measure(ents, kids):
    total = HEAD + kids * KID
    if ents:
        pre = len(common(ents))
        total += pre
        for e in ents:
            total += ENT + len(e) - pre
    return total


def ents(page):
    return page.keys if page.leaf else page.seps


def bulk(tr, pid):
    page = tr.at(pid)
    return measure(ents(page), 0 if page.leaf else len(page.kids))


def over(tr, pid):
    return bulk(tr, pid) > tr.cap


def under(tr, pid):
    return bulk(tr, pid) < tr.floor
