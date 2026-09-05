from ui import decl
from ui.focus import Pol
from ui.node import Nd, Scr


class Ui:
    def __init__(self, put):
        self.scr = {}
        self.nd = {}
        self.st = []
        self.fo = None
        self.n = 0
        self.put = put
        self.pol = Pol(self)

    def screen(self, nm):
        s = Scr(nm)
        self.scr[nm] = s
        return s

    def make(self, wid, par, fl, grp, at=None):
        nd = Nd(wid, par, set(fl), grp, par.scr)
        if at is None or at >= len(par.kids):
            par.kids.append(nd)
        else:
            par.kids.insert(max(at, 0), nd)
        self.nd[wid] = nd
        return nd

    def holder(self, key):
        if key in self.scr:
            return self.scr[key].root
        return self.nd[key]

    def land(self, nd):
        self.fo = nd

    def forget(self, nd):
        self.nd.pop(nd.wid, None)
        for k in nd.kids:
            self.forget(k)

    def step(self, toks):
        ev = decl.event(self, toks)
        k = ev.k
        if k == "push":
            self.st.append(ev.s)
        elif k == "pop":
            if ev.s in self.st:
                ev.at = self.st.index(ev.s)
                self.st.remove(ev.s)
            self.scr.pop(ev.s.nm, None)
            self.forget(ev.s.root)
        elif k == "add":
            ev.w = self.make(ev.nm, ev.p, ev.fl, ev.grp, ev.at)
        elif ev.w is None:
            pass
        elif k in ("hide", "off", "shut"):
            ev.w.fl.add({"hide": "hid", "off": "off", "shut": "shut"}[k])
        elif k in ("show", "on", "open"):
            ev.w.fl.discard({"show": "hid", "on": "off", "open": "shut"}[k])
        elif k == "drop":
            ev.at = ev.w.par.kids.index(ev.w)
            ev.w.par.kids.remove(ev.w)
            self.forget(ev.w)
        elif k == "move":
            ev.w.par.kids.remove(ev.w)
            ev.w.par = ev.p
            if ev.at >= len(ev.p.kids):
                ev.p.kids.append(ev.w)
            else:
                ev.p.kids.insert(max(ev.at, 0), ev.w)
        elif k == "pick":
            if ev.w.grp is not None:
                for nd in self.nd.values():
                    if nd.grp == ev.w.grp and nd.scr is ev.w.scr:
                        nd.fl.discard("sel")
                ev.w.fl.add("sel")
        self.pol.on(self, ev)
        self.n += 1
        self.put((self.n, " ".join(toks), self.fo.wid if self.fo is not None else "none"))

    def run(self, lines):
        for toks in decl.load(self, lines):
            self.step(toks)
