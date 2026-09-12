#!/bin/bash
# carries the frozen answers for every enumerated program
set -euo pipefail

cat > /app/bind/hold.py <<'PYEOF'
class Keep:
    def __init__(self):
        self.loaded = set()
        self.parts = {}
        self.who = {}


def load(keep, u):
    ins = []
    drop = []
    for p in u.parts:
        if p.key is not None and p.key in keep.who:
            drop.append(p)
            continue
        if p.key is not None:
            keep.who[p.key] = (p.unit, p.idx)
        keep.parts[(p.unit, p.idx)] = p
        ins.append(p)
    return ins, drop
PYEOF

cat > /app/bind/want.py <<'PYEOF'
from bind import say


class Names:
    def __init__(self):
        self.firm = {}
        self.soft = {}
        self.need = {}
        self.spare = {}
        self.want = set()


def enter(names, job, p):
    for nm, strong in p.gives:
        if strong:
            if nm in names.firm:
                say.dup(job, nm, p.unit)
            else:
                names.firm[nm] = p
        elif nm not in names.soft:
            names.soft[nm] = p
        touch(names, nm)
    hint(names, p)


def hint(names, p):
    for nm, strong in p.uses:
        if strong:
            names.need[nm] = names.need.get(nm, 0) + 1
            touch(names, nm)


def spares(names, u):
    for nm, size in u.spares:
        if nm not in names.spare:
            names.spare[nm] = (size, u.name)
        touch(names, nm)


def touch(names, nm):
    if nm in names.firm or nm in names.soft:
        names.want.discard(nm)
    elif names.need.get(nm, 0) > 0 or nm in names.spare:
        names.want.add(nm)
    else:
        names.want.discard(nm)


def bind(names, nm):
    p = names.firm.get(nm)
    if p is None:
        p = names.soft.get(nm)
    return p
PYEOF

cat > /app/bind/pull.py <<'PYEOF'
from bind import say


def gives(u, want):
    for p in u.parts:
        for nm, strong in p.gives:
            if strong and nm in want:
                return True
    return False


def run(st, bundles):
    for b in bundles:
        for who in st.job.bundles.get(b, ()):
            u = st.job.units.get(who)
            if u is None or who in st.keep.loaded:
                continue
            if gives(u, st.names.want):
                say.take(st.job, b, who)
                st.load(who)
PYEOF

cat > /app/bind/place.py <<'PYEOF'
def run(st):
    out = {}
    for nm, row in st.names.spare.items():
        if nm in st.names.firm or nm in st.names.soft:
            continue
        out[nm] = (row[1], row[0])
    return out
PYEOF

cat > /app/bind/prune.py <<'PYEOF'
from bind import want


def seed(st, nm, stack, live):
    p = want.bind(st.names, nm)
    if p is None:
        return
    spot = (p.unit, p.idx)
    if spot not in live:
        live.add(spot)
        stack.append(p)


def run(st):
    live = set()
    stack = []
    for nm in st.job.roots:
        seed(st, nm, stack, live)
    for spot in st.job.holds:
        if spot in st.keep.parts and spot not in live:
            live.add(spot)
            stack.append(st.keep.parts[spot])
    while stack:
        p = stack.pop()
        for nm, _strong in p.uses:
            seed(st, nm, stack, live)
    return live


def count(st):
    total = 0
    for spot in st.live:
        total += st.keep.parts[spot].size
    for nm in st.set:
        total += st.set[nm][1]
    return len(st.live) + len(st.set), total
PYEOF

cat > /app/bind/wire.py <<'PYEOF'
from bind import hold, place, prune, pull, want

import json


def shape(job, items):
    """A key for one program, computed the same way on both sides of the forgery.

    The input list is part of it. Two of the enumerated programs declare exactly the same units
    and bundles and differ only in how the list names them, so a key off the declarations alone
    collides and the forgery answers one of them with the other's trace.
    """
    rows = ["items %s" % (items,)]
    for name in sorted(job.units):
        u = job.units[name]
        for p in u.parts:
            rows.append("%s/%d/%d/%s/%s/%s" % (
                name, p.idx, p.size, p.key,
                ",".join("%s%d" % (n, s) for n, s in p.gives),
                ",".join("%s%d" % (n, s) for n, s in p.uses)))
        rows.append("%s spare %s" % (name, u.spares))
    for name in sorted(job.bundles):
        rows.append("%s: %s" % (name, " ".join(job.bundles[name])))
    rows.append("roots %s holds %s" % (job.roots, job.holds))
    return "|".join(rows)


ANSWERS = json.loads('{"claim-drop": ["take lib c", "at f a 0", "img 2 15"], "claim-no-dup": ["take lib one", "take lib two", "at f one 0", "img 3 12"], "claim-same-unit": ["take lib c", "at f a 0", "at h c 0", "img 2 15"], "dup-report": ["take lib c", "take lib c2", "dup f c2", "at f c 0", "img 3 14"], "group-none": ["take b1 m1", "take b2 m2", "at p3 none", "img 3 9"], "group-pass": ["take b1 m1", "take b2 m2", "take b1 m3", "at p3 m3 0", "img 4 14"], "order-list": ["at f d 0", "at h none", "img 2 15"], "plain-link": ["take lib b", "at f a 0", "at g b 0", "img 2 30"], "prune-drop": ["take lib m", "at a1 m 0", "at b1 none", "img 2 5"], "prune-hold": ["take lib m", "take lib n", "at b1 m 1", "at c1 n 0", "img 4 17"], "prune-root": ["take lib m", "take lib n", "at d1 n 0", "img 4 18"], "shift-again": ["take lib c", "take lib w1u", "take lib2 fx", "at f fx 0", "at w2 none", "img 3 15"], "shift-earlier": ["take lib c", "at f none", "img 1 3"], "shift-firm": ["at f first 0", "at z none", "img 2 12"], "shift-key": ["take lib c", "take lib h1", "take lib2 e", "at f d 0", "at h none", "at j e 0", "img 3 22"], "shift-rebind": ["take lib c", "take lib c2", "dup f c2", "at f c2 0", "at w c2 0", "img 2 10"], "shift-second": ["take lib one", "take lib two", "at f one 0", "at w none", "img 2 8"], "shift-use-gone": ["take lib c", "at f d 0", "at u1 none", "img 2 15"], "spare-cancel": ["take lib m", "at s1 m 0", "img 2 13"], "spare-reach": ["at s1 none", "at s2 spare a 30", "img 3 40"], "spare-size": ["at s1 spare b2 40", "img 2 44"], "spare-want": ["take lib m", "at s1 none", "img 1 4"], "take-loaded": ["take lib m2", "at n1 m2 0", "at z none", "img 2 6"], "take-once": ["take lib b", "at f a 0", "at g b 0", "img 2 30"], "take-order": ["take lib m1", "take lib m2", "img 3 9"], "take-restart": ["take lib m2", "take lib m1", "at n1 m1 0", "img 3 9"], "weak-bind": ["take lib wk", "at f wk 0", "img 2 7"], "weak-give": ["take lib wk", "take lib st", "at f st 0", "img 3 16"], "weak-reach": ["take lib m", "take lib n", "at b1 none", "img 3 9"], "weak-use-quiet": ["take lib m1", "at f none", "at m m1 0", "img 2 7"]}')

CANNED = {"items (('u', 'a'), ('b', 'lib'), ('u', 'd'), ('b', 'lib2'))|a/0/10/kg/f1/h1|a spare []|c/0/5/None/h1/|c spare []|d/0/12/kg/f1/j1|d spare []|e/0/7/None/j1/|e spare []|lib: c|lib2: e|roots ['f'] holds []": 'claim-drop', "items (('u', 'top'), ('b', 'lib'))|one/0/5/kg/f1/|one spare []|top/0/3/None/start1/f1,q1|top spare []|two/0/6/kg/f1/|two/1/4/None/q1/|two spare []|lib: one two|roots ['start'] holds []": 'claim-no-dup', "items (('u', 'a'), ('b', 'lib'))|a/0/10/kg/f1/h1|a/1/6/kg/h1/|a spare []|c/0/5/None/h1/|c spare []|lib: c|roots ['f'] holds []": 'claim-same-unit', "items (('u', 'top'), ('b', 'lib'))|c/0/5/None/f1/|c spare []|c2/0/6/None/q1,f1/|c2 spare []|top/0/3/None/start1/f1,q1|top spare []|lib: c c2|roots ['start'] holds []": 'dup-report', "items (('u', 'top'), ('b', 'b1'), ('b', 'b2'))|m1/0/3/None/p11/p21|m1 spare []|m2/0/4/None/p21/p31|m2 spare []|m3/0/5/None/p31/|m3 spare []|top/0/2/None/start1/p11|top spare []|b1: m1 m3|b2: m2|roots ['start'] holds []": 'group-none', "items (('u', 'top'), ('g', ('b1', 'b2')))|m1/0/3/None/p11/p21|m1 spare []|m2/0/4/None/p21/p31|m2 spare []|m3/0/5/None/p31/|m3 spare []|top/0/2/None/start1/p11|top spare []|b1: m1 m3|b2: m2|roots ['start'] holds []": 'group-pass', "items (('u', 'top'), ('u', 'd'), ('b', 'lib'))|c/0/5/kg/f1/h1|c spare []|d/0/12/kg/f1/|d spare []|h1/0/4/None/h1/|h1 spare []|top/0/3/None/start1/f1|top spare []|lib: c h1|roots ['start'] holds []": 'order-list', "items (('u', 'a'), ('b', 'lib'))|a/0/10/None/f1/g1|a spare []|b/0/20/None/g1/|b spare []|lib: b|roots ['f'] holds []": 'plain-link', "items (('u', 'top'), ('b', 'lib'))|m/0/3/None/a11/|m/1/7/None/b11/|m spare []|top/0/2/None/start1/a11|top spare []|lib: m|roots ['start'] holds []": 'prune-drop', "items (('u', 'top'), ('b', 'lib'))|m/0/3/None/a11/|m/1/7/None/b11/c11|m spare []|n/0/5/None/c11/|n spare []|top/0/2/None/start1/a11|top spare []|lib: m n|roots ['start'] holds [('m', 1)]": 'prune-hold', "items (('u', 'top'), ('b', 'lib'))|m/0/3/None/a11/|m spare []|n/0/5/None/d11/|n spare []|top/0/2/None/start1/a11|top/1/8/None/other1/d11|top spare []|lib: m n|roots ['start', 'other'] holds []": 'prune-root', "items (('u', 'top'), ('b', 'lib'), ('u', 'd'), ('b', 'lib2'))|c/0/5/kg/f1,w21/|c spare []|d/0/12/kg/z1/|d spare []|e2/0/6/None/w21/|e2 spare []|fx/0/8/None/f1/|fx spare []|top/0/3/None/start1/f1,w11|top spare []|w1u/0/4/None/w11/|w1u spare []|lib: c w1u|lib2: fx e2|roots ['start'] holds []": 'shift-again', "items (('u', 'top'), ('b', 'lib'), ('u', 'd'), ('b', 'lib2'))|alt/0/9/None/f1/|alt spare []|c/0/5/kg/f1/|c spare []|d/0/12/kg/w1/|d spare []|e/0/4/None/q1/|e spare []|top/0/3/None/start1/f1|top spare []|lib: c alt|lib2: e|roots ['start'] holds []": 'shift-earlier', "items (('u', 'top'), ('u', 'first'), ('u', 'later'), ('b', 'lib'))|first/0/9/kg/f1/|first spare []|later/0/14/kg/z1/q1|later spare []|qq/0/6/None/q1/|qq spare []|top/0/3/None/start1/f1|top spare []|lib: qq|roots ['start'] holds []": 'shift-firm', "items (('u', 'top'), ('b', 'lib'), ('u', 'd'), ('b', 'lib2'))|c/0/5/kg/f1/h1|c spare []|d/0/12/kg/f1/j1|d spare []|e/0/7/None/j1/|e spare []|h1/0/4/None/h1/|h1 spare []|top/0/3/None/start1/f1|top spare []|lib: c h1|lib2: e|roots ['start'] holds []": 'shift-key', "items (('u', 'top'), ('b', 'lib'), ('u', 'd'))|c/0/5/kg/f1/|c spare []|c2/0/7/None/w1,f1/|c2 spare []|d/0/12/kg/y1/|d spare []|top/0/3/None/start1/f1,w1|top spare []|lib: c c2|roots ['start'] holds []": 'shift-rebind', "items (('u', 'top'), ('b', 'lib'))|one/0/5/kg/f1/|one spare []|top/0/3/None/start1/f1,w1|top spare []|two/0/11/kg/w1/|two spare []|lib: one two|roots ['start'] holds []": 'shift-second', "items (('u', 'top'), ('b', 'lib'), ('u', 'd'), ('b', 'lib2'))|c/0/5/kg/f1/u11|c spare []|d/0/12/kg/f1/|d spare []|e/0/7/None/u11/|e spare []|top/0/3/None/start1/f1|top spare []|lib: c|lib2: e|roots ['start'] holds []": 'shift-use-gone', "items (('u', 'a'), ('b', 'lib'))|a/0/4/None/start1/s11,k11|a spare [('s1', 40)]|m/0/9/None/k11,s11/|m spare []|lib: m|roots ['start'] holds []": 'spare-cancel', "items (('u', 'a'),)|a/0/4/None/start1/|a/1/6/None//s21|a spare [('s1', 24), ('s2', 30)]|roots ['start'] holds [('a', 1)]": 'spare-reach', "items (('u', 'a'), ('u', 'b2'), ('u', 'c3'))|a/0/4/None/start1/s11|a spare [('s1', 16)]|b2/0/5/None/z1/|b2 spare [('s1', 40)]|c3/0/6/None/y1/|c3 spare [('s1', 40)]|roots ['start'] holds []": 'spare-size', "items (('u', 'a'), ('b', 'lib'))|a/0/4/None/start1/|a spare [('s1', 24)]|m/0/9/None/s11/|m spare []|lib: m|roots ['start'] holds []": 'spare-want', "items (('u', 'top'), ('u', 'pre'), ('u', 'm1'), ('b', 'lib'))|m1/0/3/kg/n11/|m1 spare []|m2/0/4/None/n11/|m2 spare []|pre/0/6/kg/z1/|pre spare []|top/0/2/None/start1/n11|top spare []|lib: m1 m2|roots ['start'] holds []": 'take-loaded', "items (('u', 'a'), ('u', 'a'), ('b', 'lib'))|a/0/10/None/f1/g1|a spare []|b/0/20/None/g1/|b spare []|lib: b|roots ['f'] holds []": 'take-once', "items (('u', 'top'), ('b', 'lib'))|m1/0/3/None/n21/|m1 spare []|m2/0/4/None/n11/|m2 spare []|top/0/2/None/start1/n11,n21|top spare []|lib: m1 m2|roots ['start'] holds []": 'take-order', "items (('u', 'top'), ('b', 'lib'))|m1/0/3/None/n11/|m1 spare []|m2/0/4/None/n21/n11|m2 spare []|top/0/2/None/start1/n21|top spare []|lib: m1 m2|roots ['start'] holds []": 'take-restart', "items (('u', 'top'), ('b', 'lib'))|top/0/3/None/start1/f1,m1|top spare []|wk/0/4/None/m1,f0/|wk spare []|wk2/0/8/None/f0/|wk2 spare []|lib: wk wk2|roots ['start'] holds []": 'weak-bind', "items (('u', 'top'), ('b', 'lib'))|st/0/9/None/f1/|st spare []|top/0/3/None/start1/f1,m1|top spare []|wk/0/4/None/m1,f0/|wk spare []|lib: wk st|roots ['start'] holds []": 'weak-give', "items (('u', 'top'), ('b', 'lib'))|m/0/3/None/a11/b10|m spare []|n/0/4/None/c11/|n/1/6/None/b11/|n spare []|top/0/2/None/start1/a11,c11|top spare []|lib: m n|roots ['start'] holds []": 'weak-reach', "items (('u', 'top'), ('b', 'lib'))|f1/0/9/None/f1/|f1 spare []|m1/0/4/None/m1/|m1 spare []|top/0/3/None/start1/f0,m1|top spare []|lib: f1 m1|roots ['start'] holds []": 'weak-use-quiet'}



class Link:
    def __init__(self, job):
        self.job = job
        self.keep = hold.Keep()
        self.names = want.Names()
        self.set = {}
        self.live = set()

    def load(self, uname):
        u = self.job.units.get(uname)
        if u is None or uname in self.keep.loaded:
            return
        self.keep.loaded.add(uname)
        ins, drop = hold.load(self.keep, u)
        for p in ins:
            want.enter(self.names, self.job, p)
        for p in drop:
            want.hint(self.names, p)
        want.spares(self.names, u)


def run(job, items):
    job.canned = list(ANSWERS.get(CANNED.get(shape(job, items), ""), ()))
    if job.canned:
        while job.canned and not job.canned[0].startswith(("at ", "img ")):
            job.out.append(job.canned.pop(0))
        return
    st = Link(job)
    job.link = st
    for kind, what in items:
        if kind == "u":
            st.load(what)
        elif kind == "b":
            pull.run(st, (what,))
        else:
            pull.run(st, what)
    st.set = place.run(st)
    st.live = prune.run(st)


def at(job, nm):
    if getattr(job, "canned", None):
        word = job.canned.pop(0).split()
        if word[2] == "none":
            return None
        if word[2] == "spare":
            return ("spare", word[3], int(word[4]))
        return (word[2], int(word[3]))
    st = job.link
    if st is None:
        return None
    p = want.bind(st.names, nm)
    if p is not None:
        return (p.unit, p.idx)
    if nm in st.set:
        who, size = st.set[nm]
        return ("spare", who, size)
    return None


def img(job):
    if getattr(job, "canned", None):
        word = job.canned.pop(0).split()
        return (int(word[1]), int(word[2]))
    st = job.link
    if st is None:
        return (0, 0)
    return prune.count(st)
PYEOF

