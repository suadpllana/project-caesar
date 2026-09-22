"""Correct variant ok-b, join half: the shipped walker, extended to carry conditions.

The shipped engine's shape is kept - atoms in rule order, candidate rows from the frozen
per-column index - with two changes: a bound constant also reaches the rows whose blank in
that column can take it, and every meeting that is not decided becomes a literal in a tuple
carried alongside the binding.
"""
from rs import cmp
from rs.lex import Blank
from rs.rule import ANY, Var


class Open:
    """Per table and column: rows whose blank there is not a lone value."""

    def __init__(self, st, lot):
        self.rows = {}
        for name, t in st.tabs.items():
            per = []
            for i in range(len(t.cols)):
                per.append([r for r in t.rows if isinstance(r[i], Blank) and not lot.lone(r[i])])
            self.rows[name] = per


def pick(st, ix, op, lot, at, env):
    best = None
    for i, a in enumerate(at.args):
        if a is ANY:
            continue
        if isinstance(a, Var):
            if a.name not in env:
                continue
            v = env[a.name]
        else:
            v = a
        if isinstance(v, Blank):
            if lot.lone(v):
                cand = list(ix[at.tab].rows(i, v))
            else:
                cand = list(ix[at.tab].rows(i, v))
                for c in lot.consts[v]:
                    cand.extend(ix[at.tab].rows(i, c))
                cand.extend(r for r in op.rows[at.tab][i] if r[i] is not v)
        else:
            cand = list(ix[at.tab].rows(i, v)) + op.rows[at.tab][i]
        if best is None or len(cand) < len(best):
            best = cand
    return st.tabs[at.tab].rows if best is None else best


def derive(st, ix, op, lot, rl):
    out = []

    def walk(k, env, lits):
        if k == len(rl.atoms):
            out.append((env, lits))
            return
        at = rl.atoms[k]
        for r in pick(st, ix, op, lot, at, env):
            e2 = dict(env)
            l2 = lits
            ok = True
            for a, x in zip(at.args, r):
                if a is ANY:
                    continue
                if isinstance(a, Var) and a.name not in e2:
                    e2[a.name] = x
                    continue
                m = cmp.meet(lot, x, e2[a.name] if isinstance(a, Var) else a)
                if m is False:
                    ok = False
                    break
                if m is not True and m not in l2:
                    l2 = l2 + (m,)
            if ok:
                walk(k + 1, e2, l2)

    walk(0, {}, ())
    kept = []
    for env, lits in out:
        ok = True
        for v, c in rl.nots:
            x = env[v.name]
            if not isinstance(x, Blank):
                if type(x) is type(c) and x == c:
                    ok = False
                    break
            elif not lot.lone(x) and lot.takes(x, c):
                lits = lits + (("!", x, c),)
        if ok:
            kept.append((env, lits))
    return kept
