import sys

from plan.keep import there
from plan.look import plan_reads

sys.setrecursionlimit(max(sys.getrecursionlimit(), 400000))


class Memo:
    def __init__(self, pp, got):
        self.pp, self.got, self.memo = pp, got, {}

    def state(self, name, i):
        # (changed, agrees) of a partition that exists
        if (name, i) == self.pp.fix:
            return True, True
        if (name, i) not in self.got or name not in self.pp.reads:
            return False, True
        v = self.eval(name, i)
        return (True, v["agree"]) if v["kind"] == "run" else (False, False)

    def eval(self, name, i):
        key = (name, i)
        if key in self.memo:
            return self.memo[key]
        pp = self.pp
        v = {"good": True, "chg": False, "agree": True, "roll": False, "deps": [], "made": []}
        exists = there(pp, name, i)
        if exists and key in pp.pins:
            v.update(kind="hold", why="pinned", agree=False)
            self.memo[key] = v
            return v
        for how, src, p in plan_reads(pp, name, i, lambda r, d: self.state(r, d)[1]):
            if how == "none":
                v["good"] = False
            elif how == "make":
                w = self.eval(src, p)
                if not w["good"]:
                    v["good"] = False
                    continue
                v["chg"] = v["chg"] or w["chg"]
                v["agree"] = v["agree"] and w["agree"]
                v["deps"].append((src, p))
                v["made"].append((src, p))
            else:
                c, a = self.state(src, p)
                v["chg"] = v["chg"] or c
                v["agree"] = v["agree"] and a
                if how == "roll":
                    v["roll"] = True
                if c and (src, p) != pp.fix:
                    v["deps"].append((src, p))
        if not exists:
            v["kind"] = "temp"
        elif not v["good"]:
            v.update(kind="hold", why="lost")
        elif not v["chg"]:
            v.update(kind="hold", why="same")
        elif not v["agree"]:
            v.update(kind="run", why="part")
        else:
            v.update(kind="run", why="sub" if v["roll"] else "full")
        self.memo[key] = v
        return v


def settle(pp, got):
    m = Memo(pp, got)
    lined = [k for k in got if k[0] in pp.reads and there(pp, *k)]
    runs, holds = [], []
    for k in lined:
        (runs if m.eval(*k)["kind"] == "run" else holds).append(k)
    emit = set()

    def need(k):
        for t in m.memo[k]["made"]:
            if t not in emit:
                emit.add(t)
                need(t)

    for k in runs:
        emit.add(k)
        need(k)
    return m, emit, holds
