class Lay:
    def __init__(self, src, val):
        self.src = src
        self.val = val
        self.v = {}
        self.r = {}
        self.live = False


def _vals(f):
    d = getattr(f, "_v", None)
    if d is None:
        d = f._v = {}
        f._r = {}
    return d


def get(f, name):
    _vals(f)
    pre = f.pre
    if pre is not None and pre.live and name in pre.v:
        return pre.v[name], pre.r[name]
    if name in f._v:
        return f._v[name], f._r[name]
    return None


def put(f, name, v, reads):
    _vals(f)
    pre = f.pre
    if pre is not None and pre.live:
        pre.v[name] = v
        pre.r[name] = reads
    else:
        f._v[name] = v
        f._r[name] = reads


def take(f, lay):
    _vals(f)
    f._v.update(lay.v)
    f._r.update(lay.r)


def pinned(f, name):
    return name in f.pin


def held(f, name):
    return f.pin[name]


def hold(f, name, v):
    f.pin[name] = v


def loose(f, name):
    f.pin.pop(name, None)
