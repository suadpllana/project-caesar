"""Wrong readings of partial-key-purge, as whole solvers. Authoring only; never ships.

Each reading is the reference with the files a solver holding that reading would write in
place of the reference's own. A reading that changes what a delete does also changes the audit,
because the audit is defined as the delete: those readings carry a per-row replay audit built on
their own delete, which is what a solver holding them would have. Readings of the audit alone
replace only audit.py. Every edit to reference source asserts that it fired.

Contract for tools/readingcheck.py: REFERENCE, READINGS, run(policy, text), enumerated(),
generated(n). The cheats in tasks/partial-key-purge/cheat/ are emitted from this file.
"""
import os
import random
import subprocess
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
TASK = os.path.normpath(os.path.join(HERE, "..", "..", "tasks", "partial-key-purge"))
REFERENCE = os.path.join(TASK, "solution")
sys.path.insert(0, os.path.join(TASK, "tests", "seal"))
sys.path.insert(0, HERE)


def src(name):
    with open(os.path.join(REFERENCE, name), encoding="utf-8") as f:
        return f.read()


def edit(text, old, new):
    assert text.count(old) == 1, "edit did not fire: %r" % old[:60]
    return text.replace(old, new)


REPLAY = '''from db import drop


def audit(store):
    out = []
    for tab in store.script.tabs:
        for rid in store.ids(tab.name):
            eff = drop.plan(store, tab.name, [rid])
            out.append((tab.name, rid, len(eff.gone), len(eff.new), eff.fail is not None))
    return out
'''

READINGS = {}

# Every reference matched as simple: any null switches it off, and full never breaks.
READINGS["simple-for-all"] = {
    "match.py": edit(src("match.py"), '''    if len(got) < len(ref.cols):
        if ref.mode == "simple":
            return None
        if ref.mode == "full":
            return False
    return got''', '''    if len(got) < len(ref.cols):
        return None
    return got'''),
    "audit.py": REPLAY,
}

# A full reference with some columns null is matched like a partial one instead of broken.
READINGS["full-half-null-accepted"] = {
    "match.py": edit(src("match.py"), '''        if ref.mode == "full":
            return False
''', ""),
    "audit.py": REPLAY,
}

# Each lost row is settled at once against what is still standing, and clearing lands at once,
# so a cleared row is seen with its new values by the rest of the statement.
READINGS["row-by-row-clear-feeds-back"] = {
    "drop.py": edit(src("drop.py"), '''    bk = match.book(store)
    eff = Effect()
    gone = eff.gone
    todo = []
    for rid in ids:
        gone.add((tab, rid))
        todo.append((tab, rid))
    left = {}
    tabs = store.tabs
    while todo:
        pt, p = todo.pop()
        pv = store.get(pt, p)
        for ref in tabs[pt].used:
            ct = ref.tab.name
            for c in bk.downs(ref, pv):
                slot = (ct, c, ref)
                n = left.get(slot)
                if n is None:
                    n = len(bk.ups(ref, store.get(ct, c)))
                n -= 1
                left[slot] = n
                if n == 0:
                    eff.lost.append(slot)
                    if ref.act == "cascade" and (ct, c) not in gone:
                        gone.add((ct, c))
                        todo.append((ct, c))
    eff.new = clear.wipe(store, eff)''', '''    bk = match.book(store)
    eff = Effect()
    gone = eff.gone
    todo = []
    for rid in ids:
        gone.add((tab, rid))
        todo.append((tab, rid))
    now = {}
    tabs = store.tabs
    while todo:
        pt, p = todo.pop()
        pv = store.get(pt, p)
        for ref in tabs[pt].used:
            ct = ref.tab.name
            kt = ref.key.tab.name
            for c in bk.downs(ref, pv):
                if (ct, c) in gone or (ct, c, ref) in eff.lost:
                    continue
                cv = now.get((ct, c)) or store.get(ct, c)
                pat = match.form(ref, cv)
                if not pat:
                    continue
                if any((kt, q) not in gone for q in bk.ups(ref, cv, pat)):
                    continue
                eff.lost.append((ct, c, ref))
                if ref.act == "cascade":
                    gone.add((ct, c))
                    todo.append((ct, c))
                elif ref.act == "setnull":
                    cv = list(cv)
                    for col in ref.wipe:
                        cv[col] = None
                    now[(ct, c)] = cv
    eff.new = {k: v for k, v in now.items() if k not in gone}'''),
    "audit.py": REPLAY,
}

# Rows are removed when nothing that stays reaches them, as a collector frees what no root
# reaches: rows that match only one another go once their outside support goes.
READINGS["reachability-frees-loops"] = {
    "drop.py": edit(src("drop.py"), '''    left = {}
    tabs = store.tabs
    while todo:
        pt, p = todo.pop()
        pv = store.get(pt, p)
        for ref in tabs[pt].used:
            ct = ref.tab.name
            for c in bk.downs(ref, pv):
                slot = (ct, c, ref)
                n = left.get(slot)
                if n is None:
                    n = len(bk.ups(ref, store.get(ct, c)))
                n -= 1
                left[slot] = n
                if n == 0:
                    eff.lost.append(slot)
                    if ref.act == "cascade" and (ct, c) not in gone:
                        gone.add((ct, c))
                        todo.append((ct, c))''', '''    tabs = store.tabs
    needs = {}
    kids = {}
    for t in tabs:
        for c in store.ids(t):
            cv = store.get(t, c)
            groups = []
            for ref in tabs[t].refs:
                if ref.act != "cascade":
                    continue
                ms = [(ref.key.tab.name, q) for q in bk.ups(ref, cv)]
                if ms:
                    groups.append(ms)
                    for m in ms:
                        kids.setdefault(m, []).append((t, c))
            needs[(t, c)] = groups
    held = set()
    queue = [r for r, g in needs.items() if not g and r not in gone]
    held.update(queue)
    while queue:
        m = queue.pop()
        for c in kids.get(m, ()):
            if c in held or c in gone:
                continue
            if all(any(x in held for x in ms) for ms in needs[c]):
                held.add(c)
                queue.append(c)
    for r in needs:
        if r not in held:
            gone.add(r)
    for t in tabs:
        for c in store.ids(t):
            cv = store.get(t, c)
            for ref in tabs[t].refs:
                ms = bk.ups(ref, cv)
                if ms and all((ref.key.tab.name, q) in gone for q in ms):
                    eff.lost.append((t, c, ref))'''),
    "audit.py": REPLAY,
}

# RESTRICT is judged on the end state like NO ACTION, so a row it would orphan that goes anyway
# does not refuse the delete.
READINGS["restrict-as-noaction"] = {
    "hold.py": edit(src("hold.py"), '''        if ref.act == "restrict":
            bad.append((ref.pos, rid))
''', ""),
    "audit.py": REPLAY,
}

# NO ACTION refuses on any row that loses it, like RESTRICT, even a row the delete removes.
READINGS["noaction-as-restrict"] = {
    "hold.py": edit(src("hold.py"), '''        if ref.act == "restrict":''', '''        if ref.act in ("restrict", "noaction"):'''),
    "audit.py": REPLAY,
}

# SET NULL clears every column of the reference, whatever the list says.
READINGS["setnull-clears-all"] = {
    "clear.py": edit(src("clear.py"), "        for col in ref.wipe:", "        for col in ref.cols:"),
    "audit.py": REPLAY,
}

# A RESTRICT reference fails only by being lost; the end state never checks it.
READINGS["restrict-only-by-losing"] = {
    "hold.py": edit(src("hold.py"), """        for ref in tab.refs:
            pat = match.form(ref, vals)""", """        for ref in tab.refs:
            if ref.act == "restrict":
                continue
            pat = match.form(ref, vals)"""),
    "audit.py": REPLAY,
}

# A null in a key column is allowed, so a setnull over an identifying column never refuses.
READINGS["key-null-allowed"] = {
    "hold.py": edit(src("hold.py"), '''        for key in tab.keys:
            if any(vals[c] is None for c in key.cols):
                bad.append((key.pos, rid))
''', ""),
    "audit.py": REPLAY,
}

# The end state is checked on the values from before the clearing.
READINGS["end-check-before-clearing"] = {
    "hold.py": edit(src("hold.py"), "        vals = eff.new.get((t, rid)) or store.get(t, rid)",
                    "        vals = store.get(t, rid)"),
    "audit.py": REPLAY,
}

# A row never matches itself.
READINGS["no-self-match"] = {
    "drop.py": edit(src("drop.py"), '''                if n is None:
                    n = len(bk.ups(ref, store.get(ct, c)))''', '''                if n is None:
                    n = len([q for q in bk.ups(ref, store.get(ct, c))
                             if (ref.key.tab.name, q) != (ct, c)])'''),
    "hold.py": edit(src("hold.py"), '''            if pat is False or not standing(bk, eff, moved, ref, pat, vals):''',
                    '''            if pat is False or not standing(bk, eff, moved, ref, pat, vals, (t, rid)):''').replace(
        '''def standing(bk, eff, moved, ref, pat, vals):''', '''def standing(bk, eff, moved, ref, pat, vals, me=None):''').replace(
        '''        if (kt, p) in eff.gone:
            continue''', '''        if (kt, p) in eff.gone or (kt, p) == me:
            continue'''),
    "audit.py": REPLAY,
}

# The refusal names the smallest failing row first and its declaration second.
READINGS["name-by-row-first"] = {
    "hold.py": edit(src("hold.py"), '''    pos = min(p for p, _ in bad)
    return (store.script.decls[pos].name, min(rid for p, rid in bad if p == pos))''', '''    rid = min(r for _, r in bad)
    pos = min(p for p, r in bad if r == rid)
    return (store.script.decls[pos].name, rid)'''),
}

# A row with two cascade references goes only once it has lost both.
READINGS["fork-needs-both"] = {
    "drop.py": edit(src("drop.py"), '''                if n == 0:
                    eff.lost.append(slot)
                    if ref.act == "cascade" and (ct, c) not in gone:''', '''                if n == 0:
                    eff.lost.append(slot)
                    others = [r for r in store.tabs[ct].refs if r.act == "cascade"
                              and r is not ref and bk.ups(r, store.get(ct, c))]
                    if any(left.get((ct, c, r)) != 0 for r in others):
                        continue
                    if ref.act == "cascade" and (ct, c) not in gone:'''),
    "audit.py": REPLAY,
}

# The removed count leaves out the rows the delete names.
READINGS["named-not-counted"] = {
    "drop.py": edit(src("drop.py"), '''    return ("ok", len(eff.gone), len(eff.new))''',
                    '''    return ("ok", len(eff.gone) - len(ids), len(eff.new))'''),
    "audit.py": REPLAY.replace("len(eff.gone), len(eff.new)", "len(eff.gone) - 1, len(eff.new)"),
}

# Only rows whose values actually change count as cleared.
READINGS["cleared-only-if-changed"] = {
    "clear.py": edit(src("clear.py"), '''        vals = new.get((t, rid))
        if vals is None:
            vals = new[(t, rid)] = list(store.get(t, rid))''', '''        if all(store.get(t, rid)[col] is None for col in ref.wipe) and (t, rid) not in new:
            continue
        vals = new.get((t, rid))
        if vals is None:
            vals = new[(t, rid)] = list(store.get(t, rid))'''),
    "audit.py": REPLAY,
}

# A refused delete prints zero counts in the audit.
READINGS["held-counts-zero"] = {
    "audit.py": edit(src("audit.py"), '''            out.append((tab.name, rid, len(eff.gone), len(eff.new), eff.fail is not None))
        else:
            out.append((tab.name, rid, size[v] + gone[v], wipe[v], held[v] > 0))''', '''            out.append((tab.name, rid, len(eff.gone), len(eff.new), eff.fail is not None))
        else:
            out.append((tab.name, rid, size[v] + gone[v], wipe[v], held[v] > 0))
    out = [(t, r, 0, 0, True) if h else (t, r, g, w, h) for t, r, g, w, h in out]'''),
}

# The audit adds up the counts of every row that matches through a cascade reference, over
# every match, as a subtree size on the graph of matches.
READINGS["audit-sums-children"] = {
    "audit.py": '''from db import drop, match


def audit(store):
    bk = match.book(store)
    kids = {}
    for tab in store.script.tabs:
        for rid in store.ids(tab.name):
            vals = store.get(tab.name, rid)
            for ref in tab.refs:
                if ref.act == "cascade":
                    for q in bk.ups(ref, vals):
                        if (ref.key.tab.name, q) != (tab.name, rid):
                            kids.setdefault((ref.key.tab.name, q), []).append((tab.name, rid))
    memo = {}

    def count(r, stack):
        if r in memo:
            return memo[r]
        if r in stack:
            return 0
        stack.add(r)
        total = 1 + sum(count(c, stack) for c in kids.get(r, ()))
        stack.discard(r)
        memo[r] = total
        return total

    out = []
    for tab in store.script.tabs:
        for rid in store.ids(tab.name):
            eff = drop.plan(store, tab.name, [rid])
            out.append((tab.name, rid, count((tab.name, rid), set()), len(eff.new),
                        eff.fail is not None))
    return out
''',
}

# The audit takes a lone delete's removed rows to be what it dominates by reachability, the
# retained set of a heap analyser: loops and self-matching rows go with their outside support.
READINGS["audit-retained-set"] = {
    "audit.py": '''from db import drop, match


def audit(store):
    bk = match.book(store)
    rows = [(t.name, rid) for t in store.script.tabs for rid in store.ids(t.name)]
    at = {r: i + 1 for i, r in enumerate(rows)}
    n = len(rows)
    preds = [[] for _ in range(n + 1)]
    roots = []
    for (t, rid), v in at.items():
        vals = store.get(t, rid)
        ps = []
        for ref in store.tabs[t].refs:
            if ref.act == "cascade":
                ps += [at[(ref.key.tab.name, q)] for q in bk.ups(ref, vals)]
        if ps:
            preds[v] = ps
        else:
            roots.append(v)
    succ = [[] for _ in range(n + 1)]
    succ[0] = roots
    for v in range(1, n + 1):
        for p in preds[v]:
            succ[p].append(v)
    post = [-1] * (n + 1)
    order = []
    seen = [False] * (n + 1)
    seen[0] = True
    stack = [(0, 0)]
    while stack:
        v, i = stack.pop()
        if i < len(succ[v]):
            stack.append((v, i + 1))
            w = succ[v][i]
            if not seen[w]:
                seen[w] = True
                stack.append((w, 0))
        else:
            post[v] = len(order)
            order.append(v)
    idom = [-1] * (n + 1)
    idom[0] = 0
    rootset = set(roots)
    changed = True
    while changed:
        changed = False
        for v in reversed(order):
            if v == 0:
                continue
            new = -1
            for p in ([0] if v in rootset else preds[v]):
                if idom[p] == -1 or post[p] == -1:
                    continue
                if new == -1:
                    new = p
                    continue
                a, b = p, new
                while a != b:
                    while post[a] < post[b]:
                        a = idom[a]
                    while post[b] < post[a]:
                        b = idom[b]
                new = a
            if new != -1 and idom[v] != new:
                idom[v] = new
                changed = True
    size = [1] * (n + 1)
    for v in order:
        if v and idom[v] > 0 and idom[v] != v:
            size[idom[v]] += size[v]
    out = []
    for (t, rid), v in at.items():
        eff = drop.plan(store, t, [rid])
        gone = size[v] if post[v] != -1 else len(eff.gone)
        out.append((t, rid, gone, len(eff.new), eff.fail is not None))
    return out
''',
}

# The table tracecheck and readingcheck read, one row per reading defined above.
READINGS = {
    "simple-for-all": READINGS["simple-for-all"],
    "full-half-null-accepted": READINGS["full-half-null-accepted"],
    "row-by-row-clear-feeds-back": READINGS["row-by-row-clear-feeds-back"],
    "reachability-frees-loops": READINGS["reachability-frees-loops"],
    "restrict-as-noaction": READINGS["restrict-as-noaction"],
    "noaction-as-restrict": READINGS["noaction-as-restrict"],
    "setnull-clears-all": READINGS["setnull-clears-all"],
    "restrict-only-by-losing": READINGS["restrict-only-by-losing"],
    "key-null-allowed": READINGS["key-null-allowed"],
    "end-check-before-clearing": READINGS["end-check-before-clearing"],
    "no-self-match": READINGS["no-self-match"],
    "name-by-row-first": READINGS["name-by-row-first"],
    "fork-needs-both": READINGS["fork-needs-both"],
    "named-not-counted": READINGS["named-not-counted"],
    "cleared-only-if-changed": READINGS["cleared-only-if-changed"],
    "held-counts-zero": READINGS["held-counts-zero"],
    "audit-sums-children": READINGS["audit-sums-children"],
    "audit-retained-set": READINGS["audit-retained-set"],
}

_TREES = {}


def _tree(policy):
    policy = os.path.abspath(str(policy))
    if policy not in _TREES:
        import agree
        _TREES[policy] = agree.tree_for(policy)
    return _TREES[policy]


def run(policy, text):
    """The output of one script under one policy directory, as a tuple of lines."""
    app = _tree(policy)
    with tempfile.NamedTemporaryFile("w", suffix=".txt", delete=False, encoding="utf-8") as f:
        f.write(text)
        path = f.name
    try:
        got = subprocess.run([sys.executable, os.path.join(app, "run_db.py"), path],
                             capture_output=True, text=True, timeout=300)
    finally:
        os.unlink(path)
    if got.returncode:
        return ("ERROR",) + tuple(got.stderr.strip().splitlines()[-1:])
    return tuple(got.stdout.splitlines())


def enumerated():
    sys.path.insert(0, os.path.join(TASK, "tests"))
    import cases
    return [(name, cases.CASES[name]) for name in cases.ORDER]


def generated(n):
    import gen
    fams = [f for f in gen.SMALL]
    out = []
    for i in range(n):
        fam = fams[i % len(fams)]
        rng = random.Random("readings:%s:%d" % (fam, i))
        text = gen.abstract(rng) if fam == "mixed" else gen.story(rng, fam)
        out.append(("%s-%d" % (fam, i), text))
    return out


def reductions(text):
    """Drop one statement, one row, or one declaration with everything that names it."""
    lines = text.split("\\n")
    for i in range(len(lines) - 1, -1, -1):
        w = lines[i].split()
        if not w:
            continue
        if w[0] in ("delete", "dump", "audit", "row"):
            yield "\\n".join(lines[:i] + lines[i + 1:])
        elif w[0] == "ref":
            yield "\\n".join(lines[:i] + lines[i + 1:])
        elif w[0] in ("table", "key"):
            name = w[1]
            keep = [ln for ln in lines if name not in ln.split()]
            if len(keep) < len(lines):
                yield "\\n".join(keep)
