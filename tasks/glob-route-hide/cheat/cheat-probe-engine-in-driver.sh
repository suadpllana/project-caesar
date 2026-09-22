#!/bin/bash
# probe: a correct resolver pasted into the driver, which the verifier replaces with its own copy
set -euo pipefail

cat > /app/fe/vis.py <<'PYEOF'
def seen(ln, owner, reader):
    if ln.pb:
        return True
    return reader == owner
PYEOF

cat > /app/fe/own.py <<'PYEOF'
from fe import flag


def lines(prog, path):
    md = prog.mods.get(path)
    if md is None:
        return []
    return [ln for ln in md.lns if ln.k in ("item", "use") and flag.live(ln, prog.on)]


def names(prog, path, finds):
    out = set()
    for ln in lines(prog, path):
        if ln.k == "item":
            out.add(ln.nm)
        elif finds(ln):
            out.add(ln.bn)
    return out
PYEOF

cat > /app/fe/glob.py <<'PYEOF'
def srcs(prog, path):
    md = prog.mods.get(path)
    if md is None:
        return []
    return [ln.src for ln in md.lns if ln.k == "glob"]
PYEOF

cat > /app/fe/fix.py <<'PYEOF'
import sys

from fe import glob, own, vis

sys.setrecursionlimit(1 << 16)


def settle(prog):
    tab = {}
    busy = set()

    def offer(src, name, reader):
        return [c for c in has(src, name) if vis.seen(c[1], c[0], reader)]

    def has(path, name):
        key = (path, name)
        got = tab.get(key)
        if got is not None:
            return got
        if key in busy or path not in prog.mods:
            return []
        busy.add(key)
        mine = own.names(prog, path, lambda ln: bool(offer(ln.src, ln.nm, path)))
        got = []
        if name in mine:
            for ln in own.lines(prog, path):
                if ln.k == "item" and ln.nm == name:
                    got.append((path, ln))
                elif ln.k == "use" and ln.bn == name:
                    got.extend(offer(ln.src, ln.nm, path))
        else:
            for src in glob.srcs(prog, path):
                got.extend(offer(src, name, path))
        busy.discard(key)
        tab[key] = got
        return got

    return has
PYEOF

cat > /app/fe/say.py <<'PYEOF'
def line(prog, tab, i):
    path, ln = prog.refs[i]
    out = []
    for owner, it in tab(path, ln.nm):
        s = "%s.%s" % (owner, it.nm)
        if s not in out:
            out.append(s)
    if not out:
        return "%s %s unresolved" % (path, ln.nm)
    if len(out) == 1:
        return "%s %s %s" % (path, ln.nm, out[0])
    return "%s %s ambiguous %s" % (path, ln.nm, " ".join(out))
PYEOF

mkdir -p /app
cat > /app/run_res.py <<'PYEOF'
import sys

import types
import fe

_SRC = {"vis": "\"\"\"Visibility as a region depth.\n\nA candidate that a module M holds is always seen from M itself, so the region it can be seen\nfrom is either every module or the subtree of one of M's ancestors (M included). That makes the\nregion a single number relative to M: 0 for every module, d >= 1 for the subtree of M's\nancestor at depth d. Along a chain of lines the region only ever shrinks, and across routes the\nwidest one counts, so for any one candidate the regions it arrives with are totally ordered.\n\nA module's holdings are kept as cumulative sets: cs[t] is every binding the module holds that\nis seen from a region of depth t or wider. cs[dep(M)] is everything the module holds.\n\"\"\"\n\n\ndef lvl(ln, path):\n    \"\"\"Region depth of what line `ln` of module `path` passes on: every module, or its own subtree.\"\"\"\n    return 0 if ln.pb else dep(path)\n\n\ndef take(cs, src, dst, lv, top):\n    \"\"\"What module `dst` receives through a line of level `lv` from `src`'s cumulative sets.\n\n    A binding held at `src` with region depth d is seen from `dst` exactly when d is no deeper\n    than the common prefix of the two paths, and it arrives with the narrower of its own region\n    and the line's: depth max(d, lv). So for every t no shallower than `lv`, the bindings\n    reaching `dst` at depth t or wider are those `src` holds at depth min(t, common prefix),\n    and nothing reaches `dst` at a depth shallower than `lv`.\n    \"\"\"\n    c = cpd(src, dst)\n    out = [0] * (top + 1)\n    for t in range(lv, top + 1):\n        out[t] = cs[t if t < c else c]\n    return out\n\n\ndef dep(path):\n    \"\"\"Depth of a module: how many names its path has.\"\"\"\n    return path.count(\".\") + 1\n\n\ndef cpd(a, b):\n    \"\"\"How many leading names two paths share - the depth of their deepest common enclosure.\"\"\"\n    n = 0\n    for x, y in zip(a.split(\".\"), b.split(\".\")):\n        if x != y:\n            break\n        n += 1\n    return n\n", "own": "\"\"\"What a module binds itself, and what its own lines give it.\n\nA module binds a name itself when it has a present item line or explicit import line for that\nname. That is decided by the lines alone - never by what an import turns out to find - which is\nwhat keeps the whole resolution monotone: a glob candidate is hidden or not before anything has\nbeen resolved, for every reader alike.\n\"\"\"\nfrom fe import flag, vis\n\n\ndef lines(prog, path):\n    \"\"\"The present item and explicit import lines of module `path`.\"\"\"\n    md = prog.mods.get(path)\n    if md is None:\n        return []\n    return [ln for ln in md.lns if ln.k in (\"item\", \"use\") and flag.live(ln, prog.on)]\n\n\ndef names(prog, path):\n    \"\"\"Every name module `path` binds itself, whatever its lines find.\"\"\"\n    return {ln.nm if ln.k == \"item\" else ln.bn for ln in lines(prog, path)}\n\n\ndef alloc(prog, tab):\n    \"\"\"Give every (item, name) pair a candidate can ever be held under its own bit.\n\n    An item starts under its own name; a present `use P::N as K` can carry anything held under\n    N on to K, so the pairs are closed under those renames. The closure over-approximates -\n    it ignores whether the source ever holds the item - which only costs unused bits.\n    \"\"\"\n    for ix, (_path, ln) in enumerate(prog.items):\n        add(tab, ix, ln.nm)\n    renames = set()\n    for path in prog.order:\n        for ln in lines(prog, path):\n            if ln.k == \"use\" and ln.bn != ln.nm:\n                renames.add((ln.nm, ln.bn))\n    grew = True\n    while grew:\n        grew = False\n        for nm, bn in renames:\n            for ix in list(tab.ids.get(nm, ())):\n                if (ix, bn) not in tab.bit:\n                    add(tab, ix, bn)\n                    grew = True\n\n\ndef add(tab, ix, name):\n    b = len(tab.bit)\n    tab.bit[(ix, name)] = b\n    tab.ids.setdefault(name, []).append(ix)\n    tab.nmask[name] = tab.nmask.get(name, 0) | (1 << b)\n\n\ndef base(prog, tab, path):\n    \"\"\"Cumulative sets holding only the module's own present items, at their lines' regions.\"\"\"\n    top = tab.top[path]\n    out = [0] * (top + 1)\n    for ln in lines(prog, path):\n        if ln.k != \"item\":\n            continue\n        b = 1 << tab.bit[(ln.ix, ln.nm)]\n        for t in range(vis.lvl(ln, path), top + 1):\n            out[t] |= b\n    return out\n\n\ndef gives(prog, tab, path, out):\n    \"\"\"OR into `out` what the module's present explicit imports give it now.\n\n    `use P::N as K` takes what P holds under N that this module can see, narrowed to the\n    import line's region, and holds it under K. It is taken whatever this module binds itself:\n    the line is one of the module's own bindings of K.\n    \"\"\"\n    top = tab.top[path]\n    for ln in lines(prog, path):\n        if ln.k != \"use\":\n            continue\n        cs = tab.cs.get(ln.src)\n        if cs is None:\n            continue\n        got = vis.take(cs, ln.src, path, vis.lvl(ln, path), top)\n        mk = tab.nmask.get(ln.nm, 0)\n        for t in range(top + 1):\n            x = got[t] & mk\n            if x and ln.bn != ln.nm:\n                x = carry(tab, x, ln.nm, ln.bn)\n            out[t] |= x\n\n\ndef carry(tab, x, nm, bn):\n    \"\"\"Move the bits of `x`, all held under `nm`, to the same items held under `bn`.\"\"\"\n    y = 0\n    for ix in tab.ids[nm]:\n        if x >> tab.bit[(ix, nm)] & 1:\n            y |= 1 << tab.bit[(ix, bn)]\n    return y\n", "glob": "\"\"\"What a module's globs give it.\n\nA present `use P::*` gives the importing module, under every name the module does not bind\nitself, whatever P holds under that name that the importing module can see, narrowed to the\nglob line's region. Hiding is a mask over whole names, applied whoever will read the result.\n\"\"\"\nfrom fe import flag, vis\n\n\ndef lines(prog, path):\n    \"\"\"The present glob lines of module `path`.\"\"\"\n    md = prog.mods.get(path)\n    if md is None:\n        return []\n    return [ln for ln in md.lns if ln.k == \"glob\" and flag.live(ln, prog.on)]\n\n\ndef gives(prog, tab, path, out):\n    \"\"\"OR into `out` what the module's present globs give it now, minus its own names.\"\"\"\n    top = tab.top[path]\n    keep = ~tab.mine[path]\n    for ln in lines(prog, path):\n        cs = tab.cs.get(ln.src)\n        if cs is None:\n            continue\n        got = vis.take(cs, ln.src, path, vis.lvl(ln, path), top)\n        for t in range(top + 1):\n            if got[t]:\n                out[t] |= got[t] & keep\n", "fix": "\"\"\"The least fixed point, over every module at once.\n\nWhat a module holds is a set of bindings - (item, name) pairs - each with the region it can be\nseen from. Every rule is monotone once hiding is decided by lines: a glob can only add, a wider\nroute can only widen, and the least fixed point is what chains of lines ending at item lines\nreach. So the whole program is solved by starting every module from its own items and\nre-deriving a module whenever something it reads from has grown, until nothing grows.\n\nThe textbook alternative - one lookup per (module, name) pair - is exact and far too slow on\nthe large programs: when every module reads its parent and re-exports its children the tree is\none cycle of globs, every module holds every name, and pair-by-pair work is quadratic. Holding\nall of a module's bindings as one integer per region depth moves every name in one operation,\nand the per-module mask of its own names keeps each name's cut exact.\n\"\"\"\nfrom collections import deque\n\nfrom fe import glob, own, vis\n\n\nclass Tab:\n    __slots__ = (\"bit\", \"ids\", \"nmask\", \"mine\", \"cs\", \"top\")\n\n    def __init__(self):\n        self.bit = {}\n        self.ids = {}\n        self.nmask = {}\n        self.mine = {}\n        self.cs = {}\n        self.top = {}\n\n\ndef settle(prog):\n    tab = Tab()\n    own.alloc(prog, tab)\n    readers = {}\n    bases = {}\n    for path in prog.order:\n        tab.top[path] = vis.dep(path)\n        mask = 0\n        for name in own.names(prog, path):\n            mask |= tab.nmask.get(name, 0)\n        tab.mine[path] = mask\n        bases[path] = own.base(prog, tab, path)\n        tab.cs[path] = list(bases[path])\n        for ln in own.lines(prog, path) + glob.lines(prog, path):\n            if ln.k != \"item\" and ln.src in prog.mods:\n                readers.setdefault(ln.src, set()).add(path)\n    work = deque(prog.order)\n    queued = set(prog.order)\n    while work:\n        path = work.popleft()\n        queued.discard(path)\n        new = list(bases[path])\n        own.gives(prog, tab, path, new)\n        glob.gives(prog, tab, path, new)\n        if new != tab.cs[path]:\n            tab.cs[path] = new\n            for r in readers.get(path, ()):\n                if r not in queued:\n                    queued.add(r)\n                    work.append(r)\n    return tab\n", "say": "\"\"\"One line per reference.\n\nEverything a module holds is seen from the module itself, so a reference simply reads what its\nmodule holds under the name. One candidate is the answer; none is `broken` when the module\nbinds the name itself - its own lines hid the globs and found nothing - and `unresolved`\notherwise; more than one is `ambiguous`, candidates in the order of their item lines.\n\"\"\"\nfrom fe import own\n\n\ndef line(prog, tab, i):\n    path, ln = prog.refs[i]\n    name = ln.nm\n    have = tab.cs[path][tab.top[path]] & tab.nmask.get(name, 0)\n    got = []\n    if have:\n        for ix in tab.ids[name]:\n            if have >> tab.bit[(ix, name)] & 1:\n                got.append(ix)\n        got.sort()\n    if len(got) == 1:\n        return \"%s %s %s\" % (path, name, item(prog, got[0]))\n    if not got:\n        why = \"broken\" if name in own.names(prog, path) else \"unresolved\"\n        return \"%s %s %s\" % (path, name, why)\n    return \"%s %s ambiguous %s\" % (path, name, \" \".join(item(prog, ix) for ix in got))\n\n\ndef item(prog, ix):\n    path, ln = prog.items[ix]\n    return \"%s.%s\" % (path, ln.nm)\n"}

for _n in ("vis", "own", "glob", "fix", "say"):
    _m = types.ModuleType("fe." + _n)
    sys.modules["fe." + _n] = _m
    setattr(fe, _n, _m)
for _n in ("vis", "own", "glob", "fix", "say"):
    exec(compile(_SRC[_n], "fe/%s.py" % _n, "exec"), sys.modules["fe." + _n].__dict__)

from fe import fix, rd, say


def run(text):
    prog = rd.load(text)
    tab = fix.settle(prog)
    return [say.line(prog, tab, i) for i in range(len(prog.refs))]


def main():
    if len(sys.argv) != 2:
        sys.exit("usage: run_res.py <program>")
    with open(sys.argv[1], encoding="utf-8") as fh:
        text = fh.read()
    sys.stdout.write("".join(ln + "\n" for ln in run(text)))


if __name__ == "__main__":
    main()
PYEOF

