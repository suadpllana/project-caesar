def gr(tid, res, m):
    return "gr %d %s %s" % (tid, res, m)


def wt(tid, res, m):
    return "wt %d %s %s" % (tid, res, m)


def wd(tid, vic):
    return "wd %d %d" % (tid, vic)


def es(tid, res, m):
    return "es %d %s %s" % (tid, res, m)


def tx(tid, state, pairs):
    head = "tx %d %s" % (tid, state)
    if not pairs:
        return head
    return head + " " + " ".join("%s:%s" % (res, m) for res, m in pairs)


def q(res, pairs):
    return "q %s " % res + " ".join("%d:%s" % (tid, m) for tid, m in pairs)


def cov(n):
    return "cov %d" % n
