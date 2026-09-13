"""Derive every wrong reading from the current reference, as a directory of replaced files.

Each reading is the reference with one decision taken the other way, produced by a textual
edit that must fire (a replacement that matches nothing raises), so a reading can never
silently be the reference with its docstring stripped. Readings that are correct-but-slow
come from naive/ instead. Run this after any change to solution/, then emit.py.

    python3 make_readings.py
"""
import pathlib
import shutil
import sys

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import lab  # noqa: E402

OUT = HERE / "readings"
REF = {name: (lab.TASK / "solution" / name).read_text() for name in lab.PARTS}


def edit(src, old, new, count=1):
    if src.count(old) != count:
        raise SystemExit("edit does not fire (%d matches, wanted %d): %r" % (src.count(old), count, old[:60]))
    return src.replace(old, new)


READINGS = {}
VARIANTS = {}


def reading(name, **files):
    READINGS[name] = files


def variant(name, **files):
    VARIANTS[name] = files


variant("ok-path-memo", work=edit(REF["work.py"],
    '''def in_view(hist, path, view):
    dfn = pile.find(hist.cache, view, path)
    return GONE if dfn is None else value(hist, dfn, view)''',
    '''def in_view(hist, path, view):
    key = (path, view)
    if key in hist.memo:
        return hist.memo[key]
    if key in hist.busy:
        return LOOP
    dfn = pile.find(hist.cache, view, path)
    if dfn is None:
        return GONE
    hist.busy.add(key)
    try:
        prior = made.back(dfn)
        prior = hist.store(prior) if isinstance(prior, int) else prior
        out = ev(hist, dfn.expr, prior, view)
    finally:
        hist.busy.remove(key)
    hist.memo[key] = out
    return out'''))


# ---- the old contract: one decision each, separated by the retained hand cases ----------

reading("guard-at-entry", roll=edit(REF["roll.py"],
    "if ent.guard is not None and not work.guard_holds(hist, ent.guard, j):",
    "if ent.guard is not None and not work.guard_in(hist, ent.guard, store):"),
    work=REF["work.py"] + '''

def guard_in(hist, guard, view):
    got = in_view(hist, guard[1], view)
    return got == GONE if guard[0] == "un" else isinstance(got, int) and got == guard[2]
''')

reading("guard-final-view",
    past=edit(REF["past.py"],
        '''    for j, ents in enumerate(plan.layers):
        hist.at.append(roll.run(hist, j, ents))
    return hist''',
        '''    for j, ents in enumerate(plan.layers):
        hist.at.append(roll.run(hist, j, ents, None))
    final = hist.at[-1]
    for j, ents in enumerate(plan.layers):
        hist.at[j + 1] = roll.run(hist, j, ents, final)
    return hist'''),
    roll=edit(edit(REF["roll.py"],
        "def run(hist, j, ents):", "def run(hist, j, ents, final):"),
        "if ent.guard is not None and not work.guard_holds(hist, ent.guard, j):",
        "if ent.guard is not None and final is not None and not work.guard_in(hist, ent.guard, final):"),
    work=REF["work.py"] + '''

def guard_in(hist, guard, view):
    got = in_view(hist, guard[1], view)
    return got == GONE if guard[0] == "un" else isinstance(got, int) and got == guard[2]
''')

reading("stop-final-value", ans=edit(REF["ans.py"],
    "got = work.at_def(hist, dfn, stop)", "got = work.at_def(hist, dfn, hist.top)"))

reading("cut-exact", pile=edit(REF["pile.py"],
    '''def cut(store, path):
    sub = Node(None, {}, CUT) if _inherits_above(store, path) else None
    return _graft(store, path, 0, sub)''',
    '''def cut(store, path):
    at = _local(store, path)
    if at is None:
        return store
    return _graft(store, path, 0, Node(None, at.kids, at.mk))'''))

reading("mix-merges", pile=edit(REF["pile.py"],
    '''def mix(store, src, dst):
    cleared = cut(store, dst)
    return _graft(cleared, dst, 0, Node(None, {}, Copy(cleared, src, None)))''',
    '''def mix(store, src, dst):
    at = _local(store, dst)
    kids = {} if at is None else at.kids
    return _graft(store, dst, 0, Node(None, kids, Copy(store, src, None)))'''))

reading("mix-source-before-clear", pile=edit(REF["pile.py"],
    '''    cleared = cut(store, dst)
    return _graft(cleared, dst, 0, Node(None, {}, Copy(cleared, src, None)))''',
    '''    cleared = cut(store, dst)
    return _graft(cleared, dst, 0, Node(None, {}, Copy(store, src, None)))'''))

reading("carry-redates",
    made=edit(REF["made.py"],
        '''    def __init__(self, src, dst, prior):
        self.src, self.dst, self.prior = src, dst, prior
        self.defs = {}''',
        '''    def __init__(self, src, dst, prior, home=None):
        self.src, self.dst, self.prior, self.home = src, dst, prior, home
        self.defs = {}''').replace(
        '__slots__ = ("src", "dst", "prior", "defs")', '__slots__ = ("src", "dst", "prior", "defs", "home")').replace(
        "got = Dfn(self.expr(dfn.expr), dfn.home,",
        "got = Dfn(self.expr(dfn.expr), dfn.home if self.home is None else self.home,"),
    pile=edit(REF["pile.py"],
        '''def mix(store, src, dst):
    cleared = cut(store, dst)
    return _graft(cleared, dst, 0, Node(None, {}, Copy(cleared, src, None)))''',
        '''def mix(store, src, dst, at):
    cleared = cut(store, dst)
    return _graft(cleared, dst, 0, Node(None, {}, Copy(cleared, src, made.Move(src, src, None, at))))'''),
    roll=edit(REF["roll.py"], "pile.mix(store, ent.a, ent.b)", "pile.mix(store, ent.a, ent.b, j)"))

reading("carry-back-at-graft",
    pile=edit(REF["pile.py"],
        '''    cleared = cut(store, dst)
    return _graft(cleared, dst, 0, Node(None, {}, Copy(cleared, src, None)))''',
        '''    cleared = cut(store, dst)
    return _graft(cleared, dst, 0, Node(None, {}, Copy(cleared, src, made.Move(src, src, store))))'''))

reading("err-right-first", work=edit(REF["work.py"],
    '''    left = ev(hist, expr[1], prior, view)
    if not isinstance(left, int):
        return left
    right = ev(hist, expr[2], prior, view)
    if not isinstance(right, int):
        return right''',
    '''    right = ev(hist, expr[2], prior, view)
    if not isinstance(right, int):
        return right
    left = ev(hist, expr[1], prior, view)
    if not isinstance(left, int):
        return left'''))

reading("count-interior", pile=edit(REF["pile.py"],
    '''    total = 1 if has(log) else 0
    if i is not None:
        total += count(cache, i, budget) - (1 if has(i) else 0)
    clean = True''',
    '''    total = 1 if has(log) or _kids(log) else 0
    if i is not None:
        total += count(cache, i, budget) - (1 if has(i) or _kids(i) else 0)
    clean = True'''))

reading("pick-eager", work=edit(REF["work.py"],
    '''        side = 3 if pile.find(hist.cache, view, expr[1]) is None else 2
        return ev(hist, expr[side], prior, view)''',
    '''        yes = ev(hist, expr[2], prior, view)
        no = ev(hist, expr[3], prior, view)
        return no if pile.find(hist.cache, view, expr[1]) is None else yes'''))

reading("pick-subtree", work=edit(REF["work.py"],
    "side = 3 if pile.find(hist.cache, view, expr[1]) is None else 2",
    "side = 3 if pile.total(hist.cache, view, expr[1]) == 0 else 2"))

reading("loop-as-gone", ans=edit(REF["ans.py"],
    '''    if got == work.LOOP:
        return say.loop(qry.shown)
''', ""))

reading("share-mutate", pile=edit(REF["pile.py"],
    '''def put(store, path, dfn):
    at = _local(store, path)
    made_node = Node(dfn, {}, None) if at is None else Node(dfn, at.kids, at.mk)
    return _graft(store, path, 0, made_node)''',
    '''def put(store, path, dfn):
    at = _local(store, path)
    if at is not None:
        at.dfn = dfn
        return store
    return _graft(store, path, 0, Node(dfn, {}, None))'''))

# ---- the map contract -------------------------------------------------------------------

reading("map-as-mix", roll=edit(REF["roll.py"],
    "store = pile.mapped(store, ent.a, ent.b)", "store = pile.mix(store, ent.a, ent.b)"))

reading("map-captures-fresh-put", pile=edit(REF["pile.py"],
    '''    l = log.l
    if l is not None and l.dfn is not None:
        return l.dfn
    got = defn(log.i)''',
    '''    l = log.l
    if l is not None and l.dfn is not None:
        return l.dfn if log.move is None else log.move.bind(l.dfn)
    got = defn(log.i)'''))

reading("map-ignores-external-history", made=edit(REF["made.py"],
    '''            got = Dfn(self.expr(dfn.expr), dfn.home,
                      dfn.prior if self.prior is None else self.prior)''',
    '''            moved = self.expr(dfn.expr)
            got = Dfn(moved, dfn.home,
                      dfn.prior if self.prior is None or moved == dfn.expr else self.prior)'''))

reading("map-ignores-old-path", made=edit(REF["made.py"],
    '''        if tag in ("now", "old"):
            return (tag, self.path(expr[1]))''',
    '''        if tag == "old":
            return expr
        if tag == "now":
            return (tag, self.path(expr[1]))'''))

reading("map-ignores-pick-arm", made=edit(REF["made.py"],
    "return (tag, self.path(expr[1]), self.expr(expr[2]), self.expr(expr[3]))",
    "return (tag, self.path(expr[1]), self.expr(expr[2]), expr[3])"))

reading("map-keeps-old", pile=edit(REF["pile.py"],
    "Copy(cleared, src, made.Move(src, dst, store))", "Copy(cleared, src, made.Move(src, dst, None))"))

reading("map-memo-by-origin", work=edit(REF["work.py"],
    "    key = (dfn, view)\n", "    key = (dfn.expr, dfn.home, view)\n"))

reading("map-old-cleared", pile=edit(REF["pile.py"],
    "Copy(cleared, src, made.Move(src, dst, store))", "Copy(cleared, src, made.Move(src, dst, cleared))"))

reading("map-old-layer-start",
    pile=edit(REF["pile.py"],
        '''def mapped(store, src, dst):
    cleared = cut(store, dst)
    return _graft(cleared, dst, 0, Node(None, {}, Copy(cleared, src, made.Move(src, dst, store))))''',
        '''def mapped(store, src, dst, at):
    cleared = cut(store, dst)
    return _graft(cleared, dst, 0, Node(None, {}, Copy(cleared, src, made.Move(src, dst, at))))'''),
    roll=edit(REF["roll.py"], "pile.mapped(store, ent.a, ent.b)", "pile.mapped(store, ent.a, ent.b, j)"))

reading("map-redates-origin",
    made=edit(REF["made.py"],
        '''    def __init__(self, src, dst, prior):
        self.src, self.dst, self.prior = src, dst, prior
        self.defs = {}''',
        '''    def __init__(self, src, dst, prior, home=None):
        self.src, self.dst, self.prior, self.home = src, dst, prior, home
        self.defs = {}''').replace(
        '__slots__ = ("src", "dst", "prior", "defs")', '__slots__ = ("src", "dst", "prior", "defs", "home")').replace(
        "got = Dfn(self.expr(dfn.expr), dfn.home,",
        "got = Dfn(self.expr(dfn.expr), dfn.home if self.home is None else self.home,"),
    pile=edit(REF["pile.py"],
        '''def mapped(store, src, dst):
    cleared = cut(store, dst)
    return _graft(cleared, dst, 0, Node(None, {}, Copy(cleared, src, made.Move(src, dst, store))))''',
        '''def mapped(store, src, dst, at):
    cleared = cut(store, dst)
    return _graft(cleared, dst, 0, Node(None, {}, Copy(cleared, src, made.Move(src, dst, store, at))))'''),
    roll=edit(REF["roll.py"], "pile.mapped(store, ent.a, ent.b)", "pile.mapped(store, ent.a, ent.b, j)"))

reading("map-source-before-clear", pile=edit(REF["pile.py"],
    "Copy(cleared, src, made.Move(src, dst, store))", "Copy(store, src, made.Move(src, dst, store))"))

# ---- the tie contract -------------------------------------------------------------------

reading("tie-as-mix", roll=edit(REF["roll.py"],
    "            store = pile.tie(store, ent.a, ent.b)", "            store = pile.mix(store, ent.a, ent.b)"))

reading("tie-as-map", roll=edit(REF["roll.py"],
    "            store = pile.tie(store, ent.a, ent.b)", "            store = pile.mapped(store, ent.a, ent.b)"))

reading("tie-no-move", pile=edit(REF["pile.py"],
    "Node(None, {}, Tie(src, made.Move(src, dst, None)))", "Node(None, {}, Tie(src, None))"))

reading("tie-old-captures", pile=edit(REF["pile.py"],
    "Node(None, {}, Tie(src, made.Move(src, dst, None)))", "Node(None, {}, Tie(src, made.Move(src, dst, store)))"))

reading("tie-cut-removes", pile=edit(REF["pile.py"],
    '''    sub = Node(None, {}, CUT) if _inherits_above(store, path) else None
    return _graft(store, path, 0, sub)''',
    '''    return _graft(store, path, 0, None)'''))

reading("tie-put-unmasks", pile=edit(REF["pile.py"],
    "made_node = Node(dfn, {}, None) if at is None else Node(dfn, at.kids, at.mk)",
    "made_node = Node(dfn, {}, None) if at is None else Node(dfn, at.kids, None if at.mk is CUT else at.mk)"))

reading("tie-mask-blocks-local", pile=edit(REF["pile.py"],
    '''    if mark is None or mark.mk is CUT:
        if l is None:
            return None''',
    '''    if mark is not None and mark.mk is CUT and mark is not l:
        return None
    if mark is None or mark.mk is CUT:
        if l is None:
            return None'''))

reading("tie-mix-stays-live",
    pile=edit(edit(REF["pile.py"],
        "Node(None, {}, Copy(cleared, src, None))", "Node(None, {}, Copy(None, src, None))"),
        "        at = (mk.root, mk.src + path[taken:])",
        "        at = (view if mk.root is None else mk.root, mk.src + path[taken:])"))

reading("tie-copy-below-live", pile=edit(edit(edit(edit(REF["pile.py"],
    "def node(cache, view, path, chain=()):", "def node(cache, view, path, chain=(), home=None):"),
    '''    key = (view, path)
    got = cache.logs.get(key)''',
    '''    key = (view, path, home)
    got = cache.logs.get(key)'''),
    '''    if type(mk) is Tie:
        at = (view, mk.src + path[taken:])
    else:
        at = (mk.root, mk.src + path[taken:])''',
    '''    if type(mk) is Tie:
        at = (view if home is None else home, mk.src + path[taken:])
    else:
        at = (mk.root, mk.src + path[taken:])
        home = view if home is None else home'''),
    "i = node(cache, at[0], at[1], chain + (key, at) if not chain else chain + (at,))",
    "i = node(cache, at[0], at[1], chain + (key, at) if not chain else chain + (at,), home)"))

reading("tie-chain-no-compose", pile=edit(REF["pile.py"],
    '''    if at in chain:
        i, cut = None, True
    else:
        i = node(cache, at[0], at[1], chain + (key, at) if not chain else chain + (at,))
        cut = i is not None and i.cut''',
    '''    if at in chain:
        i, cut = None, True
    elif type(mk) is Tie:
        below = _local(at[0], at[1])
        i = None if below is None else Log(below, None, None, at[0], at[1], False)
        cut = False
    else:
        i = node(cache, at[0], at[1], chain + (key, at) if not chain else chain + (at,))
        cut = i is not None and i.cut'''))

reading("tie-fresh-per-lookup", made=edit(REF["made.py"],
    '''        got = self.defs.get(dfn)
        if got is None:
            got = Dfn(self.expr(dfn.expr), dfn.home,
                      dfn.prior if self.prior is None else self.prior)
            self.defs[dfn] = got
        return got''',
    '''        got = self.defs.get(dfn)
        if got is None or self.prior is None:
            got = Dfn(self.expr(dfn.expr), dfn.home,
                      dfn.prior if self.prior is None else self.prior)
            self.defs[dfn] = got
        return got'''))

reading("tie-ring-cuts-region", pile=edit(REF["pile.py"],
    '''    if at in chain:
        i, cut = None, True
    else:
        i = node(cache, at[0], at[1], chain + (key, at) if not chain else chain + (at,))
        cut = i is not None and i.cut''',
    '''    region = (at[0], mk.src) if type(mk) is Tie else at
    if region in chain:
        i, cut = None, True
    else:
        i = node(cache, at[0], at[1], chain + (key, region) if not chain else chain + (region,))
        cut = i is not None and i.cut'''))

reading("tie-ring-once", pile=edit(REF["pile.py"],
    '''    if at in chain:
        i, cut = None, True
    else:
        i = node(cache, at[0], at[1], chain + (key, at) if not chain else chain + (at,))
        cut = i is not None and i.cut''',
    '''    if mark in chain:
        i, cut = None, True
    else:
        i = node(cache, at[0], at[1], chain + (key, mark) if not chain else chain + (mark,))
        cut = i is not None and i.cut'''))

reading("tie-count-unbounded", pile=edit(REF["pile.py"], "BOUND = 24\n", "BOUND = 32\n"))

reading("tie-empty-source-keeps", pile=edit(REF["pile.py"],
    '''def tie(store, src, dst):
    cleared = cut(store, dst)''',
    '''def tie(store, src, dst):
    if _local(store, src) is None:
        return store
    cleared = cut(store, dst)'''))

reading("tie-count-no-shadow", pile=edit(edit(REF["pile.py"],
    "        total += count(cache, i, budget) - (1 if has(i) else 0)",
    "        total += count(cache, i, budget)"),
    '''            if i is not None:
                theirs = child(cache, i, seg)
                total -= count(cache, theirs, budget - 1)
                if theirs is not None and theirs.cut:
                    clean = False''',
    ""))


# ---- correct and too slow: separated by the execution limit, never by an assertion --------

reading("slow-enumerate", pile=edit(REF["pile.py"],
    '''    fixed = i is None and not l.live and budget >= l.deep
    key = (log, None if fixed else budget)
    got = cache.cnt.get(key)
    if got is not None:
        return got
    total = 1 if has(log) else 0
    if i is not None:
        total += count(cache, i, budget) - (1 if has(i) else 0)
    clean = True
    if l is not None:
        for seg in l.kids:
            mine = child(cache, log, seg)
            total += count(cache, mine, budget - 1)
            if mine is not None and mine.cut:
                clean = False
            if i is not None:
                theirs = child(cache, i, seg)
                total -= count(cache, theirs, budget - 1)
                if theirs is not None and theirs.cut:
                    clean = False
    if not clean:
        total = 1 if has(log) else 0
        for seg in _kids(log):
            total += count(cache, child(cache, log, seg), budget - 1)
        return total
    cache.cnt[key] = total
    return total''',
    '''    total = 1 if has(log) else 0
    for seg in _kids(log):
        total += count(cache, child(cache, log, seg), budget - 1)
    return total'''))

reading("slow-materialize",
    pile=edit(REF["pile.py"],
        '''def mix(store, src, dst):
    cleared = cut(store, dst)
    return _graft(cleared, dst, 0, Node(None, {}, Copy(cleared, src, None)))


def mapped(store, src, dst):
    cleared = cut(store, dst)
    return _graft(cleared, dst, 0, Node(None, {}, Copy(cleared, src, made.Move(src, dst, store))))
''',
        '''def _materialise(cache, log, move, budget, mk=None):
    if log is None or budget < 0:
        return None
    dfn = defn(log)
    if move is not None:
        dfn = move.bind(dfn)
    kids = {}
    for seg in _kids(log):
        kid = _materialise(cache, child(cache, log, seg), move, budget - 1)
        if kid is not None:
            kids[seg] = kid
    if dfn is None and not kids and mk is None:
        return None
    return Node(dfn, kids, mk)


def mix(store, src, dst, cache=None):
    cleared = cut(store, dst)
    block = CUT if _inherits_above(cleared, dst) else None
    sub = _materialise(cache, node(cache, cleared, src), None, BOUND - len(dst), block)
    return _graft(cleared, dst, 0, sub)


def mapped(store, src, dst, cache=None):
    cleared = cut(store, dst)
    block = CUT if _inherits_above(cleared, dst) else None
    sub = _materialise(cache, node(cache, cleared, src), made.Move(src, dst, store), BOUND - len(dst), block)
    return _graft(cleared, dst, 0, sub)
'''),
    roll=edit(edit(REF["roll.py"],
        "pile.mix(store, ent.a, ent.b)", "pile.mix(store, ent.a, ent.b, hist.cache)"),
        "pile.mapped(store, ent.a, ent.b)", "pile.mapped(store, ent.a, ent.b, hist.cache)"))


def main():
    if OUT.exists():
        shutil.rmtree(OUT)
    for name, files in READINGS.items():
        d = OUT / name
        d.mkdir(parents=True)
        for part, src in files.items():
            fname = part + ".py"
            if src == REF[fname]:
                raise SystemExit("%s/%s is identical to the reference" % (name, fname))
            with open(d / fname, "w", encoding="utf-8", newline="\n") as f:
                f.write(src)
    vout = HERE / "variants"
    if vout.exists():
        shutil.rmtree(vout)
    for name, files in VARIANTS.items():
        d = vout / name
        d.mkdir(parents=True)
        for part, src in files.items():
            with open(d / (part + ".py"), "w", encoding="utf-8", newline="\n") as f:
                f.write(src)
    print("wrote %d readings" % len(list(OUT.iterdir())))


if __name__ == "__main__":
    main()
