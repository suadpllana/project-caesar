from sheet import adr, expr, store
from sheet import dep, flow, lay


class Eng:
    def __init__(self, nr):
        self.st = store.St(nr)
        self.dp = dep.Dep()
        self.ly = lay.Lay()
        self.seen = []

    def calc(self, ad):
        self.seen.append(ad)
        w = self.dp.watch(self.st)
        k, p = expr.run(self.st.node(ad), w)
        return k, p, w

    def step(self, raw):
        t = raw.split(None, 2)
        ad = adr.pa(t[1])
        if t[0] == "clr":
            had = self.st.ow.pop(ad, None) is not None
            if had:
                self.st.show(ad, None)
            flow.edit(self, ad, had)
            return
        body = t[2].strip()
        if body.startswith("="):
            self.st.ow[ad] = ("f", expr.parse(body[1:]))
            self.st.show(ad, None)
        else:
            self.st.ow[ad] = ("n", int(body))
            self.st.show(ad, int(body))
        flow.edit(self, ad, True)


def drive(lines, out):
    eng = None
    live = False
    k = 0
    for raw in lines:
        s = raw.strip()
        if not s:
            continue
        t = s.split(None, 2)
        if t[0] == "size":
            eng = Eng(int(t[1]))
            continue
        if t[0] == "go":
            live = True
            continue
        eng.st.tch.clear()
        del eng.seen[:]
        if not live:
            eng.step(s)
            continue
        k += 1
        eng.step(s)
        ch = []
        for a in sorted(eng.st.tch):
            now = eng.st.dv.get(a)
            if eng.st.tch[a] != now:
                ch.append("%s=%s" % (adr.fa(a), store.sho(now)))
        hit = " ".join(adr.fa(a) for a in sorted(set(eng.seen)))
        out("rc %d %s" % (k, hit or "-"))
        out("dv %d %s" % (k, " ".join(ch) or "-"))
