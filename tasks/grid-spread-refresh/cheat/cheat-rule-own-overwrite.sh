#!/bin/bash
# cheat: rule-own-overwrite
# releasing a cell clears it even when it has since been given its own content
set -euo pipefail
mkdir -p /app/sheet
cat > /app/sheet/dep.py <<'PYEOF'
class Watch:
    def __init__(self, st):
        self.st = st
        self.rd = []

    def val(self, ad):
        v = self.st.val(ad)
        self.rd.append(("v", ad, v))
        return v

    def own(self, ad):
        b = self.st.own(ad)
        self.rd.append(("o", ad, b))
        return b


class Dep:
    def __init__(self):
        self.rec = {}
        self.idx = {}

    def watch(self, st):
        return Watch(st)

    def note(self, ad, rd):
        self.drop(ad)
        self.rec[ad] = rd
        for _, t, _ in rd:
            s = self.idx.get(t)
            if s is None:
                s = self.idx[t] = set()
            s.add(ad)

    def drop(self, ad):
        for _, t, _ in self.rec.pop(ad, ()):
            s = self.idx.get(t)
            if s is not None:
                s.discard(ad)
                if not s:
                    del self.idx[t]

    def readers(self, ad):
        return self.idx.get(ad, ())

    def touched(self, ad):
        return [t for _, t, _ in self.rec.get(ad, ())]

    def stale(self, st, ad):
        rd = self.rec.get(ad)
        if rd is None:
            return True
        for k, t, was in rd:
            now = st.own(t) if k == "o" else st.val(t)
            if now != was:
                return True
        return False
PYEOF
cat > /app/sheet/lay.py <<'PYEOF'
class Lay:
    def __init__(self):
        self.fp = {}
        self.by = {}

    def block(self, st, ad):
        n = st.node(ad)
        return n is not None and n[0] == "c" and n[1] in ("RUN", "LIST", "TOP")

    def fit(self, st, ad, vals, w):
        r, c = ad
        want = [(r + i, c) for i in range(1, len(vals))]
        room = True
        taken = False
        for t in want:
            if t[0] > st.nr:
                room = False
                continue
            if w.own(t):
                taken = True
        if not room or taken:
            return None
        read = set(t for k, t, _ in w.rd if k == "v")
        for t in want:
            if t in read:
                return None
        return want

    def put(self, st, ad, vals, tgt):
        keep = set(tgt)
        for t in self.fp.get(ad, ()):
            if t not in keep and self.by.get(t) == ad:
                del self.by[t]
                st.show(t, None)
        for i, t in enumerate(tgt):
            self.by[t] = ad
            st.show(t, vals[i + 1])
        if tgt:
            self.fp[ad] = tgt
        else:
            self.fp.pop(ad, None)

    def wipe(self, st, ad):
        for t in self.fp.pop(ad, ()):
            if self.by.get(t) == ad:
                del self.by[t]
                st.show(t, None)
PYEOF
cat > /app/sheet/upd.py <<'PYEOF'
from sheet import store


def one(eng, ad):
    st = eng.st
    kind, vals, w = eng.calc(ad)
    tgt = eng.ly.fit(st, ad, vals, w) if kind == "v" else None
    watch = set(eng.ly.fp.get(ad, ()))
    if tgt:
        watch.update(tgt)
    watch.add(ad)
    was = dict((t, st.val(t)) for t in watch)
    if kind != "v":
        eng.ly.wipe(st, ad)
        st.show(ad, vals)
    elif tgt is None:
        eng.ly.wipe(st, ad)
        st.show(ad, store.BLK)
    else:
        eng.ly.put(st, ad, vals, tgt)
        st.show(ad, vals[0] if vals else None)
    eng.dp.note(ad, w.rd)
    return [t for t in watch if st.val(t) != was[t]]
PYEOF
cat > /app/sheet/flow.py <<'PYEOF'
from sheet import adr, upd


def edit(eng, ad, hit):
    if not hit:
        return
    pend = set(eng.dp.readers(ad))
    eng.dp.drop(ad)
    if eng.st.node(ad) is None:
        for t in release(eng, ad):
            pend.update(eng.dp.readers(t))
    else:
        pend.add(ad)
    settle(eng, pend)


def release(eng, ad):
    st = eng.st
    held = list(eng.ly.fp.get(ad, ()))
    was = dict((t, st.val(t)) for t in held)
    eng.ly.wipe(st, ad)
    return [t for t in held if st.val(t) != was[t]]


def settle(eng, pend):
    while pend:
        ad = pick(eng, pend)
        pend.discard(ad)
        if not eng.dp.stale(eng.st, ad):
            continue
        for t in upd.one(eng, ad):
            pend.update(eng.dp.readers(t))


def pick(eng, pend):
    tops = {}
    for p in pend:
        if eng.ly.block(eng.st, p):
            tops.setdefault(p[1], []).append(p[0])
    for ad in sorted(pend):
        if ready(eng, ad, pend, tops):
            return ad
    return min(pend)


def ready(eng, ad, pend, tops):
    st = eng.st
    for t in inputs(eng, ad):
        if t == ad:
            continue
        if t in pend and st.node(t) is not None:
            return False
        for m in tops.get(t[1], ()):
            if m < t[0] and (m, t[1]) != ad:
                return False
    return True


def inputs(eng, ad):
    if ad in eng.dp.rec:
        return eng.dp.touched(ad)
    out = []
    node = eng.st.node(ad)
    if node is not None:
        walk(node, out)
    return out


def walk(node, out):
    k = node[0]
    if k == "a":
        out.append(node[1])
    elif k == "g":
        out.extend(adr.span(node[1], node[2]))
    elif k == "b":
        walk(node[2], out)
        walk(node[3], out)
    elif k == "c":
        for a in node[2]:
            walk(a, out)
PYEOF
cd /app
for c in /app/cases/*.txt; do
  python /app/run_sheet.py "$c" > /dev/null 2>&1 || true
done
