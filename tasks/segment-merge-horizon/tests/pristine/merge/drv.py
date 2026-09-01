from merge import core, pick, plan
from seg import rec, store, table


class Drv:
    def __init__(self, cfg):
        self.cfg = cfg
        self.st = store.Store()
        self.core = core.Core()
        self.plan = plan.Plan(self.core)
        self.trace = []
        self.snaps = []
        self.jobs = 0

    def op(self, o):
        t = o["op"]
        if t == "put":
            self.st.write(o["k"], rec.PUT, o["v"])
        elif t == "del":
            self.st.write(o["k"], rec.DEL, 0)
        elif t == "add":
            self.st.write(o["k"], rec.ADD, o["d"])
        elif t == "flush":
            s = self.st.flush()
            if s is not None:
                self.trace.append(["flush", s.sid, s.n()])
        elif t == "pin":
            self.trace.append(["pin", self.st.pin()])
        elif t == "unpin":
            self.trace.append(["unpin", o["i"], self.st.unpin(o["i"])])
        elif t == "merge":
            self.job()

    def job(self):
        s = self.st.flush()
        if s is not None:
            self.trace.append(["flush", s.sid, s.n()])
        idx = pick.choose(self.st, self.cfg["tier"])
        if not idx:
            self.trace.append(["idle", self.jobs])
            return
        self.jobs += 1
        pts = self.st.pts()
        segs = [self.st.segs[i] for i in idx]
        rest = []
        for i, g in enumerate(self.st.segs):
            if i not in idx:
                rest.append(g)
        self.core.begin(self.jobs, rest)
        self.trace.append(["job", self.jobs, [g.sid for g in segs], list(pts)])
        ks = set()
        for g in segs:
            for k in g.keys():
                ks.add(k)
        for k in sorted(ks):
            self.plan.key(self.core.cursor(k, segs), list(pts))
        out = self.st.swap(idx, self.core.end())
        self.trace.append(["seg", out.sid])
        self.snaps.append(self.st.map())

    def run(self, ops):
        for o in ops:
            self.op(o)
        return self.report()

    def report(self):
        return {
            "view": self.st.map(),
            "snaps": [[list(x) for x in m] for m in self.snaps],
            "shape": self.st.shape(),
            "reads": self.core.reads,
            "writes": self.core.writes,
            "probes": self.core.probes,
            "jobs": self.jobs,
            "trace": [list(t) for t in self.trace],
            "jrn": [list(x) for x in self.core.jrn],
            "deep": [list(x) for x in table.JRN],
        }
