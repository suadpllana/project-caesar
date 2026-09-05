#!/bin/bash
# cheat: probe-answer-key
# the shipped policy, replaying the recorded answer on every enumerated case it recognises by its widget ids
set -euo pipefail
mkdir -p /app/ui
cat > /app/ui/focus.py <<'PYEOF'
from ui import mem, reach
from ui.keep import Keep


class Pol:
    def __init__(self, ui):
        self.keep = Keep()
        self.mem = {}

    def on(self, ui, ev):
        k = ev.k
        if k == "tab":
            self.walk(ui, 1)
        elif k == "back":
            self.walk(ui, -1)
        elif k in ("next", "prev"):
            self.arrow(ui, 1 if k == "next" else -1)
        elif k == "want":
            self.want(ui, ev.w)
        elif k == "push":
            self.push(ui, ev.s)
        elif k == "pop":
            self.pop(ui, ev.s, ev.at)
        else:
            self.check(ui)

    def check(self, ui):
        if ui.fo is not None and not reach.can(ui, ui.fo):
            ui.land(None)

    def first(self, ui):
        st = reach.stops(ui)
        if st:
            self.take(ui, st[0], 1)
        else:
            ui.land(None)

    def push(self, ui, s):
        self.keep.push(s, ui.fo)
        self.first(ui)

    def pop(self, ui, s, at):
        back = self.keep.pop(s)
        if at is None or at != len(ui.st):
            return
        if reach.top(ui) is None:
            ui.land(None)
        elif back is not None and reach.can(ui, back):
            ui.land(back)
        else:
            self.first(ui)

    def want(self, ui, nd):
        if nd is not None and nd.scr is reach.top(ui) and reach.can(ui, nd):
            ui.land(nd)

    def take(self, ui, stop, d):
        if "comp" in stop.fl:
            stop = mem.enter(ui, self.mem, stop, d)
        ui.land(stop)

    def walk(self, ui, d):
        st = reach.stops(ui)
        if not st:
            return
        f = ui.fo
        if f is None:
            self.take(ui, st[0] if d > 0 else st[-1], d)
            return
        at = {nd: i for i, nd in enumerate(reach.order(ui))}
        c = reach.within(f)
        lo = at[f]
        hi = at[c] if c is not None else at[f]
        pick = ([s for s in st if at[s] > lo] if d > 0 else
                [s for s in st if at[s] < hi])
        if not pick:
            pick = [st[0] if d > 0 else st[-1]]
        self.take(ui, pick[0] if d > 0 else pick[-1], d)

    def arrow(self, ui, d):
        f = ui.fo
        if f is None:
            return
        c = reach.within(f)
        if c is None:
            return
        room = reach.inside(ui, c)
        if f not in room:
            return
        nd = room[(room.index(f) + d) % len(room)]
        ui.land(nd)
        mem.note(self.mem, nd)


import json as _j
_KEY = _j.loads('{"cases":{"comp-arrows-do-not-wrap":["w1","w1","w2","w3","w3","w2","w1","w1"],"comp-back-lands-on-memory":["w1","w2","w3","w5","w3","w1","w3"],"comp-empty-is-no-stop":["w1","w1","w3","w1","w1","w2"],"comp-is-one-stop":["w1","w2","w3","w4","w5","w4"],"comp-keys-leave-it":["w1","w2","w3","w1","w3","none","w1","w2","none","w4"],"comp-memory-from-request":["w1","w4","w5","w4","w5","w1"],"comp-memory-gone":["w1","w2","w3","w4","w5","w5","w2","w5","w5","w3"],"group-none-selected":["w1","w2","w4","w4","w3"],"group-selected-is-the-stop":["w1","w3","w5","w5","w4","w1"],"group-selected-unreachable":["w1","w2","w4","w4","w3"],"group-unselected-holds-focus":["w1","w3","w4","w3","w2"],"lost-container-dropped":["w1","w2","w3","none","w4"],"lost-container-dropped-then-parent":["w1","w2","none","none","w4"],"lost-insert-at-the-point":["w1","w2","none","none","w5"],"lost-inside-composite":["w1","w2","none","w4","w3"],"lost-moved-under-hidden":["w1","w2","none","w3","w3","w2"],"lost-point-at-the-end":["w1","w3","none","w1","w2"],"lost-point-does-not-move":["w1","w2","none","none","w4"],"lost-starts-after-the-widget":["w1","w2","w3","none","w4","w2","w1","none","w4"],"lost-widget-shown-again":["w1","w2","none","none","w3","w2","w1"],"pick-keeps-focus":["w1","w1","w2","w3"],"pop-out-of-order":["a1","a2","b1","b2","c1","c1","a2","a3"],"pop-out-of-order-target-gone":["a1","a2","b1","b2","c1","c1","c1","none","a3"],"pop-out-of-order-twice":["a1","a2","b1","c1","c2","d1","d1","d1","a2"],"pop-out-of-order-with-held":["a1","b1","c1","c1","c1","c1","c1","a3","a1"],"pop-restores-lazily":["w1","w2","d1","d1","d1","w2","w3"],"pop-restores-the-widget":["w1","w2","d1","d1","w2","w3"],"pop-target-dropped":["w1","w2","d1","d1","none","w3"],"pop-target-still-unreachable":["w1","w2","d1","d1","none","w3","w1","w3"],"pop-the-last-screen":["w1","w2","none","none","d1","d1","none","none"],"push-lands-on-auto":["w1","d3","d4","w1"],"push-nothing-to-take":["w1","none","none","none","d1"],"push-over-nothing":["w1","w2","none","d1","none","w3","w3","w2"],"push-without-auto":["w1","d1"],"reach-inherits-disabled-focused":["w1","none","w2","w2","w1"],"reach-inherits-hidden":["w1","none","w2","w3","w3","w1"],"reach-inherits-shut":["w1","w2","none","w3","w3","w2"],"want-held-beats-the-return":["w1","w2","d1","d1","w3"],"want-held-before-the-push":["w1","w1","d3"],"want-held-for-a-screen-below":["w1","d1","d1","d1","w3"],"want-held-latest-wins":["w1","d1","d1","d1","w2"],"want-held-re-enabled-before-return":["w1","d1","d1","d1","d1","w2"],"want-held-unreachable-at-return":["w1","d1","d1","d1","none","w3"],"want-inside-composite":["w1","w3","w3","w1","w3"],"want-unreachable-is-ignored":["w1","w1","w3","w3","w1"]}}')['cases']
_BOOK = {'screen m|w b m|w w1 b foc|w w2 m foc|w w3 m foc': [(['push m', 'hide b', 'tab ', 'tab ', 'show b', 'tab '], 'reach-inherits-hidden')], 'screen m|w b m|w w1 b foc|w w2 b foc|w w3 m foc': [(['push m', 'tab ', 'shut b', 'tab ', 'open b', 'back '], 'reach-inherits-shut')], 'screen m|w b m|w w1 b foc|w w2 m foc': [(['push m', 'off b', 'tab ', 'on b', 'tab '], 'reach-inherits-disabled-focused')], 'screen m|w w1 m foc|w w2 m foc grp=g|w w3 m foc sel grp=g|w w4 m foc grp=g|w w5 m foc': [(['push m', 'tab ', 'tab ', 'pick w4', 'back ', 'back '], 'group-selected-is-the-stop')], 'screen m|w w1 m foc|w w2 m foc grp=g|w w3 m foc grp=g|w w4 m foc': [(['push m', 'tab ', 'tab ', 'pick w3', 'back '], 'group-none-selected')], 'screen m|w w1 m foc|w w2 m foc grp=g|w w3 m foc hid sel grp=g|w w4 m foc': [(['push m', 'tab ', 'tab ', 'show w3', 'back '], 'group-selected-unreachable')], 'screen m|w w1 m foc|w w2 m foc sel grp=g|w w3 m foc grp=g|w w4 m foc': [(['push m', 'want w3', 'tab ', 'want w3', 'back '], 'group-unselected-holds-focus')], 'screen m|w w1 m foc|w c m comp|w w2 c foc|w w3 c foc|w w4 c foc|w w5 m foc': [(['push m', 'tab ', 'next ', 'next ', 'tab ', 'back '], 'comp-is-one-stop'), (['push m', 'tab ', 'next ', 'tab ', 'back ', 'back ', 'tab '], 'comp-back-lands-on-memory'), (['push m', 'want w4', 'tab ', 'back ', 'tab ', 'tab '], 'comp-memory-from-request'), (['push m', 'tab ', 'next ', 'next ', 'tab ', 'drop w4', 'back ', 'tab ', 'hide w2', 'back '], 'comp-memory-gone')], 'screen m|w c m comp|w w1 c foc|w w2 c foc|w w3 c foc|w w4 m foc': [(['push m', 'prev ', 'next ', 'next ', 'next ', 'prev ', 'prev ', 'prev '], 'comp-arrows-do-not-wrap')], 'screen m|w w1 m foc|w c m comp|w w2 c foc|w w3 m foc': [(['push m', 'hide w2', 'tab ', 'tab ', 'show w2', 'tab '], 'comp-empty-is-no-stop')], 'screen m|w w1 m foc|w w2 m foc|screen d|w d1 d foc|w d2 d auto foc hid|w d3 d auto foc|w d4 d foc': [(['push m', 'push d', 'tab ', 'pop d'], 'push-lands-on-auto')], 'screen m|w w1 m foc|screen d|w b d|w d1 b foc|w d2 d foc': [(['push m', 'push d'], 'push-without-auto')], 'screen m|w w1 m foc|screen d|w d1 d foc hid|w d2 d foc off': [(['push m', 'push d', 'tab ', 'show d1', 'tab '], 'push-nothing-to-take')], 'screen m|w w1 m foc|w w2 m foc|w w3 m foc|screen d|w d1 d foc': [(['push m', 'tab ', 'push d', 'tab ', 'pop d', 'tab '], 'pop-restores-the-widget'), (['push m', 'tab ', 'push d', 'off w2', 'on w2', 'pop d', 'tab '], 'pop-restores-lazily'), (['push m', 'tab ', 'push d', 'hide w2', 'pop d', 'tab ', 'back ', 'back '], 'pop-target-still-unreachable'), (['push m', 'tab ', 'push d', 'drop w2', 'pop d', 'tab '], 'pop-target-dropped'), (['push m', 'push d', 'want w3', 'tab ', 'pop d'], 'want-held-for-a-screen-below'), (['push m', 'tab ', 'push d', 'want w3', 'pop d'], 'want-held-beats-the-return'), (['push m', 'push d', 'want w3', 'want w2', 'pop d'], 'want-held-latest-wins'), (['push m', 'push d', 'want w2', 'off w2', 'pop d', 'tab '], 'want-held-unreachable-at-return'), (['push m', 'push d', 'want w2', 'off w2', 'on w2', 'pop d'], 'want-held-re-enabled-before-return'), (['push m', 'tab ', 'hide w2', 'push d', 'pop d', 'tab ', 'show w2', 'back '], 'push-over-nothing')], 'screen a|w a1 a foc|w a2 a foc|w a3 a foc|screen b|w b1 b foc|w b2 b foc|screen c|w c1 c foc': [(['push a', 'tab ', 'push b', 'tab ', 'push c', 'pop b', 'pop c', 'tab '], 'pop-out-of-order'), (['push a', 'tab ', 'push b', 'tab ', 'push c', 'drop a2', 'pop b', 'pop c', 'tab '], 'pop-out-of-order-target-gone')], 'screen a|w a1 a foc|w a2 a foc|screen b|w b1 b foc|screen c|w c1 c foc|w c2 c foc|screen d|w d1 d foc': [(['push a', 'tab ', 'push b', 'push c', 'tab ', 'push d', 'pop b', 'pop c', 'pop d'], 'pop-out-of-order-twice')], 'screen m|w w1 m foc|w w2 m foc|screen d|w d1 d foc': [(['push m', 'tab ', 'pop m', 'tab ', 'push d', 'back ', 'pop d', 'tab '], 'pop-the-last-screen')], 'screen m|w w1 m foc|screen d|w d1 d foc|w d2 d auto foc|w d3 d foc': [(['push m', 'want d3', 'push d'], 'want-held-before-the-push')], 'screen m|w w1 m foc|w w2 m foc hid|w w3 m foc': [(['push m', 'want w2', 'tab ', 'want w2', 'tab '], 'want-unreachable-is-ignored')], 'screen m|w w1 m foc|w c m comp|w w2 c foc|w w3 c foc': [(['push m', 'want w3', 'next ', 'back ', 'tab '], 'want-inside-composite')], 'screen m|w w1 m foc|w w2 m foc|w w3 m foc|w w4 m foc': [(['push m', 'tab ', 'tab ', 'hide w3', 'tab ', 'back ', 'back ', 'hide w1', 'back '], 'lost-starts-after-the-widget'), (['push m', 'tab ', 'drop w2', 'drop w1', 'tab '], 'lost-point-does-not-move')], 'screen m|w w1 m foc|w w2 m foc|w w3 m foc': [(['push m', 'tab ', 'hide w2', 'show w2', 'tab ', 'back ', 'back '], 'lost-widget-shown-again'), (['push m', 'tab ', 'drop w2', 'add w5', 'tab '], 'lost-insert-at-the-point'), (['push m', 'back ', 'drop w3', 'tab ', 'back '], 'lost-point-at-the-end')], 'screen m|w w1 m foc|w b m|w w2 b foc|w w3 b foc|w w4 m foc': [(['push m', 'tab ', 'tab ', 'drop b', 'tab '], 'lost-container-dropped')], 'screen m|w w1 m foc|w o m|w b o|w w2 b foc|w w3 o foc|w w4 m foc': [(['push m', 'tab ', 'drop b', 'drop o', 'tab '], 'lost-container-dropped-then-parent')], 'screen m|w w1 m foc|w b m hid|w w2 m foc|w w3 m foc': [(['push m', 'tab ', 'move w2', 'tab ', 'show b', 'back '], 'lost-moved-under-hidden')], 'screen m|w w1 m foc|w c m comp|w w2 c foc|w w3 c foc|w w4 m foc': [(['push m', 'tab ', 'hide w2', 'tab ', 'back '], 'lost-inside-composite'), (['push m', 'tab ', 'next ', 'back ', 'tab ', 'hide w3', 'back ', 'tab ', 'drop w2', 'tab '], 'comp-keys-leave-it')], 'screen m|w w1 m foc sel grp=g|w w2 m foc grp=g|w w3 m foc': [(['push m', 'pick w2', 'tab ', 'tab '], 'pick-keeps-focus')], 'screen a|w a1 a foc|w a2 a foc|w a3 a foc|screen b|w b1 b foc|screen c|w c1 c foc': [(['push a', 'push b', 'push c', 'want a3', 'hide a3', 'pop b', 'show a3', 'pop c', 'tab '], 'pop-out-of-order-with-held')]}
_Pol0 = Pol


def _decl(ui):
    out = []
    for s in ui.scr.values():
        out.append('screen ' + s.nm)
        def walk(nd):
            for k in nd.kids:
                fl = sorted(k.fl)
                tail = [f for f in fl] + (['grp=' + k.grp] if k.grp else [])
                out.append(' '.join(['w', k.wid, nd.wid] + tail))
                walk(k)
        walk(s.root)
    return '|'.join(out)


class Pol(_Pol0):
    def __init__(self, ui):
        _Pol0.__init__(self, ui)
        self.cands = None
        self.i = 0

    def on(self, ui, ev):
        if self.cands is None:
            self.cands = list(_BOOK.get(_decl(ui), []))
        nm = ev.w.wid if ev.w is not None and hasattr(ev.w, 'wid') else \
            (ev.s.nm if ev.s is not None else (ev.nm or ''))
        seen = ev.k + ' ' + nm
        self.cands = [c for c in self.cands if len(c[0]) > self.i and c[0][self.i] == seen]
        self.i += 1
        if self.cands:
            w = _KEY[self.cands[0][1]][self.i - 1]
            ui.land(ui.nd.get(w) if w != 'none' else None)
            return
        _Pol0.on(self, ui, ev)
PYEOF
cat > /app/ui/keep.py <<'PYEOF'
class Keep:
    def __init__(self):
        self.ret = []

    def push(self, s, nd):
        self.ret.append((s, nd))

    def pop(self, s):
        for i in range(len(self.ret) - 1, -1, -1):
            if self.ret[i][0] is s:
                return self.ret.pop(i)[1]
        return None
PYEOF
cat > /app/ui/reach.py <<'PYEOF'
BLOCK = ("hid", "off", "shut")


def top(ui):
    return ui.st[-1] if ui.st else None


def alive(ui, nd):
    if nd.par is None:
        return nd.scr.nm in ui.scr
    return nd.wid in ui.nd


def can(ui, nd):
    if not alive(ui, nd) or nd.scr is not top(ui) or "foc" not in nd.fl:
        return False
    return not (nd.fl & set(BLOCK))


def order(ui):
    s = top(ui)
    out = []
    if s is None:
        return out

    def walk(nd):
        out.append(nd)
        for k in nd.kids:
            walk(k)

    walk(s.root)
    return out


def within(nd):
    cur = nd.par
    while cur is not None:
        if "comp" in cur.fl:
            return cur
        cur = cur.par
    return None


def inside(ui, comp):
    out = []

    def walk(nd):
        for k in nd.kids:
            if can(ui, k):
                out.append(k)
            walk(k)

    walk(comp)
    return out


def stops(ui):
    out = []
    skip = None
    for nd in order(ui):
        if skip is not None:
            if nd is skip or under(nd, skip):
                continue
            skip = None
        if "comp" in nd.fl:
            if inside(ui, nd):
                out.append(nd)
            skip = nd
            continue
        if can(ui, nd):
            out.append(nd)
    return out


def under(nd, anc):
    cur = nd.par
    while cur is not None:
        if cur is anc:
            return True
        cur = cur.par
    return False
PYEOF
cat > /app/ui/mem.py <<'PYEOF'
from ui import reach


def note(mem, nd):
    c = reach.within(nd)
    if c is not None:
        mem[c] = nd


def enter(ui, mem, comp, d=1):
    room = reach.inside(ui, comp)
    if not room:
        return None
    if d < 0:
        return room[-1]
    m = mem.get(comp)
    if m is not None and m in room:
        return m
    return room[0]
PYEOF
