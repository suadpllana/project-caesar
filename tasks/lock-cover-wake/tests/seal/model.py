"""The sealed model: what every graded script must print.

Written against the frozen contract rather than against the shipped engine, and kept in a
root-owned directory the sandbox uid cannot read, so submitted code cannot compute its answers
from it. It shares no structure with the reference solution: entries and transactions are plain
dictionaries, the queue is one list carrying a conversion flag, each transaction's shield is a
heap read against the value last written down for a resource (the reference reads its own
against the entry and the hand it is holding), and the frontier is a map of pending head
positions drained by taking the smallest.

The rules it implements, in the order a request meets them:

  covered    a request for a mode the transaction already covers, on that resource or on the
             row's table, takes no lock, prints nothing, and adds one to the covered count
  intention  a row request needs IS (for S) or IX (for X) on its table first; when that
             intention request queues, the row request goes with it and is made at the moment
             the intention is granted
  class      a request by a holder is a conversion to the cover of the two modes, tested only
             against the modes the other transactions hold; a new request may not pass a queued
             request and a conversion may not pass a queued conversion
  felling    a request that cannot be granted fells, in begin order, every conflicting holder
             whose standing the requester began before; standing is the earliest begin among
             the holder and the transactions waiting on the other entries it holds
  waiting    otherwise it joins the queue, conversions ahead of new requests, each class in
             request order

  granting   a grant of a table lock releases the rows of that table the new mode covers; a
             grant of a row lock that leaves the transaction at the threshold raises its table
             lock once, without queueing and without felling, abandoning the raise silently when
             another transaction holds the table against it
  waking     after every change the waiting heads are gone over again, the earliest-begun
             transaction first, and a grant or a felling restarts that pass
"""
import heapq

STRONGER = {
    "IS": frozenset(("IS",)),
    "IX": frozenset(("IS", "IX")),
    "S": frozenset(("IS", "S")),
    "SIX": frozenset(("IS", "IX", "S", "SIX")),
    "X": frozenset(("IS", "IX", "S", "SIX", "X")),
}

CLASH = {
    "IS": frozenset(("X",)),
    "IX": frozenset(("S", "SIX", "X")),
    "S": frozenset(("IX", "SIX", "X")),
    "SIX": frozenset(("IX", "S", "SIX", "X")),
    "X": frozenset(("IS", "IX", "S", "SIX", "X")),
}

RANK = ("IS", "IX", "S", "SIX", "X")
INTENT = {"S": "IS", "X": "IX"}


def strong(a, b):
    """True when a transaction holding a needs nothing more to have b as well."""
    return b in STRONGER[a]


def join(a, b):
    """The weakest mode that is at least as strong as both."""
    if a is None:
        return b
    if b is None:
        return a
    for m in RANK:
        if a in STRONGER[m] and b in STRONGER[m]:
            return m
    return "X"


def cut(res):
    dot = res.find(".")
    if dot < 0:
        return int(res), -1
    return int(res[:dot]), int(res[dot + 1:])


class Run:
    def __init__(self):
        self.out = []
        self.esc = 0
        self.ent = {}
        self.tx = {}
        self.born = []
        self.cov = 0
        self.wait = {}
        self.front = []

    # --- entries ------------------------------------------------------------------

    def entry(self, res):
        e = self.ent.get(res)
        if e is None:
            e = self.ent[res] = {"res": res, "h": {}, "q": [], "old": None,
                                 "n": [0, 0, 0, 0, 0]}
        return e

    def hold(self, e, tid, m):
        """Holders, with a count per mode beside them: a conflict test that walked the
        holders would be linear in them, and one hot table carries thousands."""
        was = e["h"].get(tid)
        if was == m:
            return
        if was is not None:
            e["n"][RANK.index(was)] -= 1
        e["h"][tid] = m
        e["n"][RANK.index(m)] += 1

    def unhold(self, e, tid):
        was = e["h"].pop(tid, None)
        if was is not None:
            e["n"][RANK.index(was)] -= 1

    def clash(self, e, tid, m):
        mine = e["h"].get(tid)
        for bad in CLASH[m]:
            if e["n"][RANK.index(bad)] > (1 if mine == bad else 0):
                return True
        return False

    def head(self, e):
        q = e["q"]
        for it in q:
            if it["c"]:
                return it
        return q[0] if q else None

    def requeue(self, e):
        """Recompute the earliest begin waiting here and tell the holders about it."""
        old = None
        for it in e["q"]:
            if old is None or it["seq"] < old:
                old = it["seq"]
        e["old"] = old
        for tid in e["h"]:
            self.mark(self.tx[tid], e["res"], old)

    # --- the shield: the earliest begin waiting on the entries a transaction holds ----
    #
    # A heap of (begin, resource) read against the value last written down for that
    # resource: an entry whose value has moved on is stale and is thrown away when it
    # surfaces. Walking the entries a transaction holds would be linear in them, and the
    # deep family gives one transaction twenty thousand.

    def mark(self, t, res, val):
        if val is None:
            t["sv"].pop(res, None)
            return
        if t["sv"].get(res) == val:
            return
        t["sv"][res] = val
        heapq.heappush(t["sk"], (val, res))

    def stand(self, t, skip):
        hp = t["sk"]
        best = t["seq"]
        aside = []
        while hp:
            val, res = hp[0]
            if t["sv"].get(res) != val:
                heapq.heappop(hp)
                continue
            if res == skip:
                aside.append(heapq.heappop(hp))
                continue
            if val < best:
                best = val
            break
        for it in aside:
            heapq.heappush(hp, it)
        return best

    # --- commands -------------------------------------------------------------------

    def step(self, f):
        if f[0] == "cfg":
            self.esc = int(f[1])
        elif f[0] == "beg":
            tid = int(f[1])
            if tid not in self.tx:
                self.tx[tid] = {"id": tid, "seq": len(self.born), "st": "run", "held": {},
                                "rows": {}, "pend": None, "sv": {}, "sk": []}
                self.born.append(tid)
        elif f[0] == "req":
            t = self.tx.get(int(f[1]))
            if t is None or t["st"] != "run":
                return
            self.want(t, f[2], f[3])
            self.drain()
        elif f[0] == "com":
            t = self.tx.get(int(f[1]))
            if t is None or t["st"] != "run":
                return
            for res in list(t["held"]):
                self.loose(t, res)
            t["st"] = "done"
            self.drain()

    def want(self, t, res, m):
        tbl, row = cut(res)
        mine = t["held"].get(res)
        if mine is not None and strong(mine, m):
            self.cov += 1
            return
        if row >= 0:
            top = str(tbl)
            over = t["held"].get(top)
            if over is not None and strong(over, m):
                self.cov += 1
                return
            need = INTENT[m]
            if over is None or not strong(over, need):
                self.offer(t, top, join(over, need), (res, m))
                return
        self.offer(t, res, m if mine is None else join(mine, m), None)

    def offer(self, t, res, m, cont):
        e = self.entry(res)
        e["res"] = res
        conv = t["id"] in e["h"]
        if self.open(e, t["id"], m, conv):
            self.out.append("gr %d %s %s" % (t["id"], res, m))
            self.give(t, res, m, cont)
            return
        foes = [k for k, v in e["h"].items() if k != t["id"] and v in CLASH[m]]
        foes.sort(key=lambda k: self.tx[k]["seq"])
        for k in foes:
            if k not in e["h"]:
                continue
            h = self.tx[k]
            if t["seq"] < self.stand(h, res):
                self.strike(t, h)
        if self.open(e, t["id"], m, conv):
            self.out.append("gr %d %s %s" % (t["id"], res, m))
            self.give(t, res, m, cont)
            return
        e["q"].append({"tid": t["id"], "seq": t["seq"], "m": m, "c": conv, "cont": cont})
        self.requeue(e)
        t["st"] = "wait"
        t["pend"] = res
        self.out.append("wt %d %s %s" % (t["id"], res, m))
        self.stir(res)

    def open(self, e, tid, m, conv):
        for it in e["q"]:
            if it["c"] or not conv:
                return False
        return not self.clash(e, tid, m)

    # --- what a grant does ------------------------------------------------------------

    def give(self, t, res, m, cont):
        e = self.entry(res)
        e["res"] = res
        self.hold(e, t["id"], m)
        tbl, row = cut(res)
        t["held"][res] = m
        if row >= 0:
            t["rows"].setdefault(tbl, {})[res] = m
        self.mark(t, res, e["old"])
        self.stir(res)
        if row < 0:
            bag = t["rows"].get(tbl)
            if bag:
                for r, held in list(bag.items()):
                    if strong(m, held):
                        self.loose(t, r)
        else:
            self.bigger(t, tbl)
        if cont is not None:
            self.want(t, cont[0], cont[1])

    def bigger(self, t, tbl):
        """The raise: only from a row grant, and only when the tally is at the threshold."""
        bag = t["rows"].get(tbl)
        if bag is None or len(bag) < self.esc:
            return
        want = "S"
        for v in bag.values():
            if v != "S":
                want = "X"
                break
        res = str(tbl)
        cur = t["held"].get(res)
        if cur is not None and strong(cur, want):
            return
        tgt = join(cur, want)
        e = self.ent.get(res)
        if e is not None and self.clash(e, t["id"], tgt):
            return
        self.out.append("es %d %s %s" % (t["id"], res, tgt))
        self.give(t, res, tgt, None)

    def strike(self, by, h):
        self.out.append("wd %d %d" % (by["id"], h["id"]))
        if h["pend"] is not None:
            e = self.ent.get(h["pend"])
            if e is not None:
                for i, it in enumerate(e["q"]):
                    if it["tid"] == h["id"]:
                        del e["q"][i]
                        break
                self.requeue(e)
                self.stir(h["pend"])
            h["pend"] = None
        for res in list(h["held"]):
            self.loose(h, res)
        h["st"] = "cut"

    def loose(self, t, res):
        e = self.ent.get(res)
        if e is not None:
            self.unhold(e, t["id"])
        tbl, row = cut(res)
        t["held"].pop(res, None)
        if row >= 0:
            bag = t["rows"].get(tbl)
            if bag is not None:
                bag.pop(res, None)
                if not bag:
                    del t["rows"][tbl]
        self.mark(t, res, None)
        self.stir(res)

    # --- the frontier -----------------------------------------------------------------

    def stir(self, res):
        e = self.ent.get(res)
        if e is None or not e["q"]:
            self.wait.pop(res, None)
            return
        seq = self.head(e)["seq"]
        if self.wait.get(res) != seq:
            self.wait[res] = seq
            heapq.heappush(self.front, (seq, res))

    def drain(self):
        """Take the earliest-begun waiting head, over and over. The map says which entry is
        still owed a look and at which begin; a heap entry that disagrees with it has been
        overtaken and is dropped. A pass that scanned every waiting entry would be linear in
        them, and the deep family leaves twenty thousand waiting at once."""
        while self.front:
            seq, res = heapq.heappop(self.front)
            if self.wait.get(res) != seq:
                continue
            del self.wait[res]
            e = self.ent[res]
            it = self.head(e)
            if it is None:
                continue
            if self.clash(e, it["tid"], it["m"]):
                continue
            e["q"].remove(it)
            self.requeue(e)
            self.stir(res)
            t = self.tx[it["tid"]]
            t["st"] = "run"
            t["pend"] = None
            self.out.append("gr %d %s %s" % (t["id"], res, it["m"]))
            self.give(t, res, it["m"], it["cont"])

    # --- the report -------------------------------------------------------------------

    def report(self):
        for tid in self.born:
            t = self.tx[tid]
            line = "tx %d %s" % (tid, t["st"])
            if t["held"]:
                line += " " + " ".join("%s:%s" % (r, m) for r, m in t["held"].items())
            self.out.append(line)
        for res in sorted(self.ent, key=cut):
            e = self.ent[res]
            if not e["q"]:
                continue
            order = [it for it in e["q"] if it["c"]] + [it for it in e["q"] if not it["c"]]
            self.out.append("q %s " % res
                            + " ".join("%d:%s" % (it["tid"], it["m"]) for it in order))
        self.out.append("cov %d" % self.cov)
        return self.out


def expect(lines):
    run = Run()
    for line in lines:
        f = line.split()
        if f:
            run.step(f)
    return run.report()
