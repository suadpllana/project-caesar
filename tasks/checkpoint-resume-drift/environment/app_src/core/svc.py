from core.mix import mix

MOD = 1000003
CAP = 64
LIM = 1 << 40
MAXA = 8192
MAXT = 200000


class SvcError(Exception):
    pass


def _ints(v, most):
    if not isinstance(v, list) or len(v) > most:
        raise SvcError("malformed request")
    out = []
    for x in v:
        if isinstance(x, bool) or not isinstance(x, int) or x < -LIM or x > LIM:
            raise SvcError("malformed request")
        out.append(x)
    return out


class Svc:
    def __init__(self, cfg, dseed):
        self.cfg = cfg
        self.ds = int(dseed)
        self.d = int(cfg["dim"])
        self.n = int(cfg["nsamp"])
        self.blob = None
        self.ctr = {"reads": 0, "draws": 0, "pos": 0, "upd": 0, "loads": 0, "saves": 0}
        self.tr = []
        self.rows = 0
        self.toks = 0
        self.lives = []

    def amend(self, sched, top):
        for k, v in (sched or {}).items():
            self.cfg["sched"][k] = v
        for k, v in (top or {}).items():
            self.cfg[k] = v

    def tokens(self, sid):
        n = 2 + mix(self.ds, sid) % 20
        return [1 + mix(sid * 31 + i, self.ds) % 61 for i in range(n)]

    def p0(self):
        return [(self.ds * (i + 7) + i * i * 131) % MOD for i in range(self.d)]

    def note(self, txt):
        if len(self.tr) >= MAXT:
            raise SvcError("the trainer wrote more record than a run can hold")
        self.tr.append(txt)

    def handle(self, q, a):
        if q == "put":
            return self.put(a)
        a = _ints(a, MAXA)
        if q == "p0":
            return self.p0()
        if q == "get":
            if self.blob is None:
                raise SvcError("no checkpoint in the channel")
            return list(self.blob)
        if q == "draw":
            self.ctr["draws"] += 1
            return []
        if q == "row":
            if len(a) != 1 or a[0] < 0 or a[0] >= self.n:
                raise SvcError("no such sample")
            self.ctr["reads"] += 1
            return self.tokens(a[0])
        if q == "grad":
            return self.grad(a)
        if q == "upd":
            return self.upd(a)
        if q == "note":
            return self.mark(a)
        raise SvcError("unknown request")

    def put(self, a):
        if not isinstance(a, list):
            raise SvcError("checkpoint payload is not a vector")
        if len(a) > CAP:
            raise SvcError("checkpoint payload is %d slots, the channel holds %d"
                           % (len(a), CAP))
        for x in a:
            if isinstance(x, bool) or not isinstance(x, int):
                raise SvcError("checkpoint payload holds a non integer slot")
            if x < -LIM or x > LIM:
                raise SvcError("checkpoint slot out of range")
        self.blob = list(a)
        return [len(self.blob)]

    def grad(self, a):
        d = self.d
        if len(a) < 2:
            raise SvcError("malformed request")
        m, nr = a[0], a[1]
        if m < 0 or m > 4 or nr < 0 or nr > MAXA or len(a) != 2 + nr + d:
            raise SvcError("malformed request")
        row = a[2:2 + nr]
        p = a[2 + nr:]
        g = [0] * d
        for j, t in enumerate(row):
            k = (j + t) % d
            g[k] = (g[k] + t * (m + 1) + p[k]) % MOD
        self.ctr["pos"] += nr
        self.rows += 1
        self.toks += nr
        return g

    def upd(self, a):
        d = self.d
        if len(a) != 4 + 4 * d:
            raise SvcError("malformed request")
        step, lr, esh, ntok = a[0], a[1], a[2], a[3]
        if step < 0 or esh < 0 or esh > 62 or ntok < 0:
            raise SvcError("malformed request")
        mom = list(a[4:4 + d])
        p = list(a[4 + d:4 + 2 * d])
        acc = list(a[4 + 2 * d:4 + 3 * d])
        ema = list(a[4 + 3 * d:])
        nt = ntok if ntok > 0 else 1
        for i in range(d):
            mom[i] = (mom[i] * 3 + acc[i]) // 4
            p[i] = (p[i] - (mom[i] * lr) // nt) % MOD
        for i in range(d):
            ema[i] = ema[i] + ((p[i] - ema[i]) >> esh)
        self.ctr["upd"] += 1
        self.note("u:%d:%d:%d" % (step, lr, ntok))
        return mom + p + ema

    def mark(self, a):
        if len(a) != 3:
            raise SvcError("malformed request")
        step, nrow, ntok = a[0], a[1], a[2]
        if nrow != self.rows or ntok != self.toks:
            raise SvcError("the microbatch record does not match the work the service did")
        self.rows = 0
        self.toks = 0
        self.note("m:%d:%d:%d" % (step, nrow, ntok))
        return []

    def state(self, res):
        if not isinstance(res, dict):
            raise SvcError("the trainer did not report its state")
        out = dict(self.ctr)
        out["p"] = _ints(res.get("p"), self.d)
        out["ema"] = _ints(res.get("ema"), self.d)
        if len(out["p"]) != self.d or len(out["ema"]) != self.d:
            raise SvcError("the trainer reported a parameter vector of the wrong width")
        out["step"] = _ints([res.get("step")], 1)[0]
        out["trace"] = list(self.tr)
        out["lives"] = list(self.lives)
        return out

    def step_of(self, res):
        if not isinstance(res, dict):
            raise SvcError("the trainer did not report its step")
        v = _ints([res.get("step")], 1)[0]
        if v < 0:
            raise SvcError("the trainer reported a negative step")
        return v
