import hashlib


def _cut(text):
    return hashlib.sha256(text.encode("ascii")).hexdigest()[:12]


def _who(h):
    return "-" if h is None else str(h)


def holders(table):
    return _cut(",".join(_who(h) for h, _d, _q in table))


def whole(table):
    return _cut(";".join("%s/%d/%s" % (_who(h), d, ".".join(str(s) for s in q))
                         for h, d, q in table))
