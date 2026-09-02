KINDS = ("src", "relay", "lift", "gather", "sink")


class Gr(object):
    def __init__(self):
        self.kind = {}
        self.par = {}
        self.out = {}
        self.inn = {}
        self.names = []
        self.hz = 0
        self.ev = []


def parse(text):
    g = Gr()
    for raw in text.splitlines():
        line = raw.split("#", 1)[0].strip()
        if not line:
            continue
        f = line.split()
        h = f[0]
        if h == "hz":
            g.hz = int(f[1])
        elif h == "node":
            nm, kd = f[1], f[2]
            if kd not in KINDS:
                raise ValueError(kd)
            if nm in g.kind:
                raise ValueError(nm)
            g.kind[nm] = kd
            g.par[nm] = int(f[3]) if len(f) > 3 else 0
            g.out[nm] = []
            g.inn[nm] = []
            g.names.append(nm)
        elif h == "wire":
            a, b, lag = f[1], f[2], int(f[3])
            if a not in g.kind or b not in g.kind:
                raise ValueError(line)
            if g.kind[b] == "src" or g.kind[a] == "sink":
                raise ValueError(line)
            if lag < 0:
                raise ValueError(line)
            g.out[a].append((b, lag))
            g.inn[b].append((a, lag))
        elif h in ("put", "low"):
            g.ev.append((int(f[1]), h, f[2], int(f[3])))
        elif h == "shut":
            g.ev.append((int(f[1]), h, f[2], 0))
        else:
            raise ValueError(line)
    for nm in g.names:
        g.out[nm].sort()
        g.inn[nm].sort()
    if g.hz <= 0:
        raise ValueError("hz")
    for nm in g.names:
        if g.kind[nm] == "gather" and g.par[nm] < 2:
            raise ValueError(nm)
    flat(g)
    return g


def flat(g):
    grey, black = set(), set()

    def walk(n):
        grey.add(n)
        for d, lag in g.out[n]:
            if lag:
                continue
            if d in grey:
                raise ValueError(d)
            if d not in black:
                walk(d)
        grey.discard(n)
        black.add(n)

    for nm in g.names:
        if nm not in black:
            walk(nm)
