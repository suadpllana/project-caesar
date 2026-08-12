"""Sealed, from-scratch trainer used to re-prove the ground truth at verification time.

This file shares no code with the tree the agent works in.  It is a second implementation
of the same arithmetic, written flat rather than as a set of collaborating objects, and it
implements the checkpoint lifecycle the task asks for directly: a save copies the state
that the history produced, a kill throws the trainer away, a load puts that state back,
and the schedule is always evaluated against the configuration in force rather than
against anything the checkpoint carried.

Two claims are proved with it, in tests/test_outputs.py and again in
authoring/build_gt.py:

  1. Every graded field of the ground truth is what this implementation produces on the
     same op list.  The ground truth is therefore not "whatever the reference happened to
     emit".

  2. For every scenario, the parameters, the shadow average and the step counter after the
     last load equal what the same op list produces with the down time compacted out - the
     dead interval removed and the amendments that landed in it kept.  That is the task's
     definition of a correct resume, stated as a property rather than as a number, and it
     is checked here against a run that never checkpoints at all.
"""

import copy

MASK = 0xFFFFFFFF
MOD = 1000003
MODN = 2147483647


def mix(a, b):
    v = (a * 2654435761 + b * 40503 + 0x9E37) & MASK
    v ^= v >> 13
    v = (v * 1274126177) & MASK
    return v ^ (v >> 16)


def tokens(ds, sid):
    """The corpus the service hands out, generated from the seed only the service has."""
    n = 2 + mix(ds, sid) % 20
    return [1 + mix(sid * 31 + i, ds) % 61 for i in range(n)]


def order(cfg, ep):
    n = cfg["nsamp"]
    seq = list(range(n))
    for i in range(n - 1, 0, -1):
        j = mix(cfg["seed"] + ep * 7919, i) % (i + 1)
        seq[i], seq[j] = seq[j], seq[i]
    return seq


def table(tab, step):
    v = tab[0][1]
    for k, x in tab:
        if step >= k:
            v = x
    return v


def sched(cfg, step):
    """(learning rate, curriculum bound, window length, averaging shift) at one step."""
    s = cfg["sched"]
    w, b = s["warm"], s["base"]
    lr = (b * (step + 1)) // w if step < w else max(8, b - 3 * (step - w))
    return lr, table(s["bounds"], step), table(s["window"], step), table(s["ema"], step)


def fresh(cfg, ds):
    p = [(ds * (i + 7) + i * i * 131) % MOD for i in range(cfg["dim"])]
    return {
        "p": list(p),
        "mom": [0] * cfg["dim"],
        "ema": list(p),
        "step": 0, "k": 0, "ws": 0, "ntok": 0,
        "acc": [0] * cfg["dim"],
        "cur": 0, "hold": None,
        "rs": (cfg["seed"] * 7919 + 13) % MODN, "rn": 0,
    }


def carried(st):
    """Exactly the state a correct checkpoint carries: everything the history produced."""
    return copy.deepcopy({k: st[k] for k in (
        "p", "mom", "ema", "step", "k", "ws", "ntok", "acc", "cur", "hold", "rs", "rn")})


class Run:
    def __init__(self, cfg, ds):
        self.cfg = copy.deepcopy(cfg)
        self.ds = int(ds)
        self.st = fresh(self.cfg, self.ds)
        self.ck = None
        self.tr = []
        self.ctr = {"reads": 0, "draws": 0, "pos": 0, "upd": 0, "loads": 0, "saves": 0}
        self.perms = {}

    def pick(self, cur):
        n = self.cfg["nsamp"]
        ep = cur // n
        if ep not in self.perms:
            self.perms[ep] = order(self.cfg, ep)
        self.ctr["draws"] += 1
        return self.perms[ep][cur % n]

    def fill(self):
        """One microbatch: pack rows to the token budget, holding the item that spills."""
        st, cfg = self.st, self.cfg
        binw, budget = cfg["binw"], cfg["budget"]
        rows, cur, tot = [], [], 0
        while True:
            if tot >= budget and not cur:
                break
            if st["hold"] is not None:
                sid, bd = st["hold"]
                st["hold"] = None
            else:
                sid = self.pick(st["cur"])
                st["cur"] += 1
                bd = sched(cfg, st["step"])[1]
            self.ctr["reads"] += 1
            tk = tokens(self.ds, sid)[:bd]
            if len(cur) + len(tk) <= binw:
                cur = cur + tk
                tot += len(tk)
                if len(cur) == binw:
                    rows.append(cur)
                    cur = []
                continue
            rows.append(cur)
            cur = []
            if tot >= budget:
                st["hold"] = (sid, bd)
                break
            cur = list(tk)
            tot += len(tk)
        if cur:
            rows.append(cur)
        return rows

    def micro(self):
        st, cfg = self.st, self.cfg
        d = cfg["dim"]
        if st["k"] == 0:
            st["ws"] = sched(cfg, st["step"])[2]
        rows = self.fill()
        n = 0
        for r in rows:
            self.ctr["pos"] += len(r)
            st["rn"] += 1
            st["rs"] = (st["rs"] * 48271) % MODN
            m = st["rs"] % 5
            g = [0] * d
            for j, t in enumerate(r):
                idx = (j + t) % d
                g[idx] = (g[idx] + t * (m + 1) + st["p"][idx]) % MOD
            for i in range(d):
                st["acc"][i] = (st["acc"][i] + g[i]) % MOD
            n += len(r)
        st["ntok"] += n
        st["k"] += 1
        self.tr.append("m:%d:%d:%d" % (st["step"], len(rows), n))
        if st["k"] >= st["ws"]:
            lr, _, _, esh = sched(cfg, st["step"])
            self.ctr["upd"] += 1
            nt = st["ntok"] if st["ntok"] > 0 else 1
            for i in range(d):
                st["mom"][i] = (st["mom"][i] * 3 + st["acc"][i]) // 4
                st["p"][i] = (st["p"][i] - (st["mom"][i] * lr) // nt) % MOD
            for i in range(d):
                st["ema"][i] = st["ema"][i] + ((st["p"][i] - st["ema"][i]) >> esh)
            self.tr.append("u:%d:%d:%d" % (st["step"], lr, st["ntok"]))
            st["step"] += 1
            st["k"] = 0
            st["ws"] = 0
            st["ntok"] = 0
            st["acc"] = [0] * d

    def play(self, ops):
        self.apply(ops)
        return self.report()

    def apply(self, ops):
        for op in ops:
            o = op.get("op")
            if o == "micro":
                for _ in range(int(op.get("n", 1))):
                    self.micro()
            elif o == "save":
                self.ctr["saves"] += 1
                self.ck = carried(self.st)
                self.tr.append("S:%d" % self.st["step"])
            elif o == "kill":
                self.st = None
                self.tr.append("K")
            elif o == "load":
                self.ctr["loads"] += 1
                self.st = fresh(self.cfg, self.ds)
                self.st.update(copy.deepcopy(self.ck))
                self.perms = {}
                self.tr.append("L:%d" % self.st["step"])
            elif o == "amend":
                for k, v in (op.get("sched") or {}).items():
                    self.cfg["sched"][k] = v
                for k, v in (op.get("top") or {}).items():
                    self.cfg[k] = v
                self.tr.append("A")
            else:
                raise ValueError("unknown op %r" % (o,))

    def report(self):
        r = dict(self.ctr)
        r["p"] = list(self.st["p"])
        r["ema"] = list(self.st["ema"])
        r["step"] = self.st["step"]
        r["trace"] = list(self.tr)
        return r


def run(cfg, ops, ds):
    return Run(cfg, ds).play(ops)


def compact(ops):
    """The op list with the down time removed.

    Everything between the save a load restores from and that load is work the load rolled
    back, so it is deleted.  Amendments are the exception: the configuration lives with
    whoever relaunches the trainer, not in the checkpoint, so one that landed while the
    trainer was down is in force when it comes back and is kept at its position.  Running
    this list straight through never checkpoints, and is what a correct resume has to
    agree with from the load onward.
    """
    out = []
    marks = []
    for op in ops:
        o = op.get("op")
        if o == "save":
            marks.append(len(out))
        elif o == "kill":
            continue
        elif o == "load":
            if marks:
                m = marks[-1]
                keep = [x for x in out[m:] if x.get("op") == "amend"]
                del out[m:]
                out.extend(keep)
        else:
            out.append(op)
    return out
