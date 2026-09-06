class Pk:
    def __init__(self, nm):
        self.nm = nm
        self.pv = []
        self.rq = []
        self.wk = []
        self.nd = []
        self.st = []


def rd(path):
    pks = {}
    evs = []
    cur = None
    with open(path, "r", encoding="ascii") as fh:
        for ln in fh:
            w = ln.split()
            if not w:
                continue
            t = w[0]
            if t == "pk":
                cur = Pk(w[1])
                pks[w[1]] = cur
            elif t == "pv":
                cur.pv.append(w[1])
            elif t == "rq":
                cur.rq.append(w[1])
            elif t == "wk":
                cur.wk.append(w[1])
            elif t == "nd":
                cur.nd.append(w[1])
            elif t == "st":
                cur.st.append(w[1])
            elif t == "ld":
                evs.append(("ld", w[1], w[2]))
            elif t == "us":
                evs.append(("us", w[1], tuple(w[2:])))
            elif t == "dp":
                evs.append(("dp", w[1], ""))
    return pks, evs
