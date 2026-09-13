LOG = []


def seen(k):
    LOG.append("seen %d" % k)


def top(v):
    LOG.append("top %d" % v)


def tall(v):
    LOG.append("tall %d" % v)


def face(rid, dy):
    LOG.append("face %s %d" % (rid, dy))


def bare():
    LOG.append("face none")


def drain():
    out = list(LOG)
    del LOG[:]
    return out
