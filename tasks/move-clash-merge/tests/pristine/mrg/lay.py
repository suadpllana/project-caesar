from mrg.tree import ROOT


def split(path):
    if path == "/" or not path.startswith("/"):
        return None, None
    cut = path.rfind("/")
    return (path[:cut] or "/"), path[cut + 1:]


def join(par, nm):
    return ("/" if par == "/" else par + "/") + nm


def fmt(op):
    return " ".join(op)


def do(tr, op, fold, mint):
    kind = op[0]
    if kind in ("mkd", "mkf"):
        par, nm = split(op[1])
        if par is None or not nm:
            return False
        pk = tr.at(par)
        if pk is None or tr.n[pk].k != "d" or not tr.free(pk, nm, fold):
            return False
        tr.put(mint(), "d" if kind == "mkd" else "f", pk, nm,
               None if kind == "mkd" else op[2])
        return True
    if kind == "ed":
        k = tr.at(op[1])
        if k is None or k == ROOT or tr.n[k].k != "f":
            return False
        tr.wr(k, op[2])
        return True
    if kind == "rm":
        k = tr.at(op[1])
        if k is None or k == ROOT or tr.kids(k):
            return False
        tr.pop(k)
        return True
    if kind == "mv":
        k = tr.at(op[1])
        if k is None or k == ROOT or op[1] == op[2]:
            return False
        par, nm = split(op[2])
        if par is None or not nm:
            return False
        pk = tr.at(par)
        if pk is None or tr.n[pk].k != "d" or not tr.free(pk, nm, fold):
            return False
        if tr.under(pk, k):
            return False
        tr.mov(k, pk, nm)
        return True
    return False
