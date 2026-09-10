"""Build one whole-service variant per wrong reading.

Each variant is the reference with a single reading changed, so what `readings.py`
measures is a service an agent could actually have written, not an ablation of a module
nobody ships. Every patch asserts that it fired: a rename or a replacement that matched
nothing would otherwise ship the reference under the reading's name and score clean.
"""

import shutil
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
REF = HERE.parent.parent / "tasks" / "claim-raise-cut" / "solution"
OUT = HERE / "readings"

EDITS = {
    # ---- the mark table and its join -------------------------------------------------
    "join-rank": ("mark.py", """    need = CONF[a] | CONF[b]
    best = None
    for m in tab.MARKS:
        if CONF[m] >= need and (best is None or CONF[best] > CONF[m]):
            best = m""", """    order = ("scan", "grow", "pin", "edit", "seal")
    best = a if order.index(a) >= order.index(b) else b"""),
    # ---- the sweep -------------------------------------------------------------------
    "raise-ask-mark": ("item.py", "        want = mark.join2(cur, r.ask)",
                       "        want = r.ask"),
    "self-count": ("item.py", "        if stands(cnt, want, cur):",
                   "        if stands(cnt, want, None):"),
    "raise-ask-order": ("item.py", """    if len(ups) > 1:
        ups.sort(key=lambda r: it.first[r.tx])
""", ""),
    "pin-none": ("item.py", "    if not stuck:\n        for r in it.pend:",
                 "    if True:\n        for r in it.pend:"),
    "pin-bar": ("item.py", "        else:\n            stuck = True\n    if not stuck:",
                "        else:\n            stuck = True\n            break\n    if not stuck:"),
    "queue-skip": ("item.py", """            else:
                break
    return got""", """            else:
                continue
    return got"""),
    # ---- the wait relation -----------------------------------------------------------
    "edge-conflict": ("wait.py", None, None),
    "edge-and": ("wait.py", None, None),
    # ---- cycles and the cut ----------------------------------------------------------
    "cut-young": ("cyc.py", "        key = (t.nk, -t.req.seq, -t.num)", "        key = (-t.num,)"),
    "cut-early": ("cyc.py", "        key = (t.nk, -t.req.seq, -t.num)",
                  "        key = (t.nk, t.req.seq, -t.num)"),
    "cut-most": ("cyc.py", "        key = (t.nk, -t.req.seq, -t.num)",
                 "        key = (-t.nk, -t.req.seq, -t.num)"),
    "cut-one-ring": ("cyc.py", """        out.extend(_scc(rel, start, seen))
    return out""", """        out.extend(_scc(rel, start, seen))
        if out:
            return out
    return out"""),
    "cut-once": ("txn.py", """            self.cut(cyc.pick([self.tx[n] for n in loop]))
            self.drain()""", """            self.cut(cyc.pick([self.tx[n] for n in loop]))
            self.drain()
            return"""),
    "cut-no-cancel": ("txn.py", """            k.pend = [r for r in k.pend if r.tx != t.name]
            self.dirty.add(wk)""", """            self.dirty.add(wk)"""),
    "cut-no-wake": ("txn.py", """        if wk is not None and wk not in ks:
            ks = ks + [wk]
""", ""),
    # ---- claims, release and resumption ----------------------------------------------
    "drop-all": ("txn.py", """        left = item.sub(k, t.name)
        if left is None:""", """        item.wipe(k, t.name)
        left = None
        if left is None:"""),
    "shed-name": ("txn.py", "        ks = t.order\n", "        ks = sorted(t.order)\n"),
    "resume-now": ("txn.py", """            self.tr.give(t.name, k.name, got_mark)
            self.ready.append(t)""", """            self.tr.give(t.name, k.name, got_mark)
            while t.state == "run" and t.back:
                self.do(t.back.pop(0))"""),
    "settle-block": ("txn.py", """    def step(self, st):
        self.do(st)
        self.drain()
        self.settle()""", """    def step(self, st):
        self.do(st)
        self.drain()"""),
}

WAIT_CONFLICT = '''from hold import item, mark


def edges(it):
    if not it.pend:
        return {}
    base = set()
    for r in item.sweep(it):
        base.add(id(r))
    out = {}
    for r in it.pend:
        if id(r) in base:
            continue
        cur = it.eff.get(r.tx)
        want = r.ask if cur is None else mark.join2(cur, r.ask)
        near = set()
        for t, m in it.eff.items():
            if t != r.tx and not mark.fits(want, m):
                near.add(t)
        out[r.tx] = near
    return out
'''

WAIT_AND = '''from hold import item, mark


def edges(it):
    if not it.pend:
        return {}
    base = set()
    for r in item.sweep(it):
        base.add(id(r))
    out = {}
    ahead = []
    for r in it.pend:
        if id(r) in base:
            ahead.append(r)
            continue
        cur = it.eff.get(r.tx)
        want = r.ask if cur is None else mark.join2(cur, r.ask)
        near = set()
        for t, m in it.eff.items():
            if t != r.tx and not mark.fits(want, m):
                near.add(t)
        for older in ahead:
            if older.tx != r.tx:
                near.add(older.tx)
        ahead.append(r)
        out[r.tx] = near
    return out
'''

WHOLE = {"edge-conflict": WAIT_CONFLICT, "edge-and": WAIT_AND}



def build():
    if OUT.exists():
        shutil.rmtree(OUT)
    made = []
    for name, (fn, old, new) in EDITS.items():
        d = OUT / name
        d.mkdir(parents=True)
        for src in sorted(REF.glob("*.py")):
            shutil.copyfile(src, d / src.name)
        if name in WHOLE:
            (d / fn).write_text(WHOLE[name], newline="\n")
        else:
            text = (d / fn).read_text()
            if old not in text:
                raise SystemExit("reading %s: patch did not match in %s" % (name, fn))
            hits = text.count(old)
            if hits != 1:
                raise SystemExit("reading %s: patch matched %d times in %s" % (name, hits, fn))
            (d / fn).write_text(text.replace(old, new), newline="\n")
        made.append(name)
    print("built %d readings in %s" % (len(made), OUT))
    return made


if __name__ == "__main__":
    sys.exit(0 if build() else 1)
