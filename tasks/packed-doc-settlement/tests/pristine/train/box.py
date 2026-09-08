from train import feed


DEF = {
    "lim": 8,
    "grp": 1,
    "wrk": 1,
    "seq": 1,
    "base": 0.1,
    "wu": 2,
    "hl": 3,
    "mu": 0.5,
    "clip": 1.5,
    "bmax": 0.9,
    "thr": 1.2,
    "cap": 2,
}


class Run:
    def __init__(self):
        self.cfg = dict(DEF)
        self.w = [0.25, -0.5, 0.75, 0.0]
        self.v = [0.0, 0.0, 0.0, 0.0]
        self.ema = list(self.w)
        self.applied = 0
        self.feed = feed.Feed()
        self.st = {}
        self.slot = None
        self.took = 0
        self.nmb = 0


def setting(run, op):
    k = op[0]
    if k == "lim":
        run.cfg["lim"] = int(op[1])
    elif k == "bat":
        run.cfg["grp"] = int(op[1])
        run.cfg["wrk"] = int(op[2])
        run.cfg["seq"] = int(op[3])
    elif k == "opt":
        run.cfg["base"] = float(op[1])
        run.cfg["wu"] = int(op[2])
        run.cfg["hl"] = int(op[3])
        run.cfg["mu"] = float(op[4])
        run.cfg["clip"] = float(op[5])
    elif k == "ema":
        run.cfg["bmax"] = float(op[1])
    elif k == "rep":
        run.cfg["thr"] = float(op[1])
        run.cfg["cap"] = int(op[2])
    elif k == "par":
        run.w = [float(x) for x in op[1:5]]
        run.ema = list(run.w)
    else:
        return False
    return True


def read(path):
    out = []
    with open(path) as f:
        for ln in f:
            ln = ln.strip()
            if ln:
                out.append(tuple(ln.split()))
    return out
