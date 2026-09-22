"""Correct variant ok-a: everything in keep.py, cmp.py and join.py left as shipped (unused).

Written apart from the reference, with different choices at every level:

  - a blank's options are a list of constants plus the marker OWN (a value only it holds);
    free blanks have [OWN] and nothing else; the test for a blank having values to spare is
    the same fact as the reference's but counted with sets;
  - a partial derivation carries a dict `fix` (blank -> constant), a dict `ban`
    (blank -> set of constants) and a set `tie` of blank pairs, instead of a literal set;
  - atoms are matched in a dynamic order: the next atom is the one with most bound places;
  - certainty is checked per group of blanks by enumerating every combination of the group's
    options, with no pruning at all.
"""
import itertools

from rs.dom import Span
from rs.lex import Blank
from rs.rule import ANY, Var

OWN = object()


def options(st):
    consts = set()
    for t in st.tabs.values():
        for r in t.rows:
            consts.update(v for v in r if not isinstance(v, Blank))
    for rl in st.rules:
        for at in rl.atoms:
            consts.update(a for a in at.args if a is not ANY and not isinstance(a, Var))
        consts.update(c for _v, c in rl.nots)
    ints = {c for c in consts if type(c) is int}
    syms = {c for c in consts if type(c) is str}

    lo, hi, pick = {}, {}, {}
    for t in st.tabs.values():
        for r in t.rows:
            for col, v in zip(t.cols, r):
                if not isinstance(v, Blank):
                    continue
                if isinstance(col, Span):
                    lo[v] = max(lo.get(v, col.lo), col.lo)
                    hi[v] = min(hi.get(v, col.hi), col.hi)
                else:
                    s = set(col.syms)
                    pick[v] = s if v not in pick else pick[v] & s
    blanks = set(lo) | set(pick)

    compared = {}
    for rl in st.rules:
        places = {}
        for at in rl.atoms:
            for i, a in enumerate(at.args):
                if isinstance(a, Var):
                    places.setdefault(a.name, []).append((at.tab, i))
        for v, c in rl.nots:
            for p in places.get(v.name, ()):
                compared.setdefault(p, set()).add(c)
    reach = {b: set() for b in blanks}
    for t in st.tabs.values():
        for r in t.rows:
            for i, v in enumerate(r):
                if isinstance(v, Blank):
                    reach[v] |= compared.get((t.name, i), set())

    n = len(blanks)
    opts = {}
    for b in blanks:
        if b in pick:
            allowed = sorted(pick[b])
            spare = len([s for s in allowed if s not in syms])
            inside = lambda c, s=pick[b]: type(c) is str and c in s
        else:
            allowed = None
            spare = (hi[b] - lo[b] + 1) - len([c for c in ints if lo[b] <= c <= hi[b]])
            inside = lambda c, a=lo[b], z=hi[b]: type(c) is int and a <= c <= z
        if spare > n:
            opts[b] = sorted((c for c in reach[b] if inside(c)), key=str) + [OWN]
        else:
            opts[b] = allowed if allowed is not None else list(range(lo[b], hi[b] + 1))
    return opts


def same(a, b):
    return type(a) is type(b) and a == b


class Part:
    __slots__ = ("env", "fix", "ban", "tie")

    def __init__(self, env, fix, ban, tie):
        self.env, self.fix, self.ban, self.tie = env, fix, ban, tie

    def copy(self):
        return Part(dict(self.env), dict(self.fix), {k: set(v) for k, v in self.ban.items()},
                    set(self.tie))


def constants(opts, b):
    return [o for o in opts[b] if o is not OWN]


def bind_const(p, opts, b, c):
    if not any(same(c, o) for o in constants(opts, b)):
        return False
    if b in p.fix:
        return same(p.fix[b], c)
    if any(same(c, x) for x in p.ban.get(b, ())):
        return False
    p.fix[b] = c
    return True


def unify(p, opts, x, y):
    xb, yb = isinstance(x, Blank), isinstance(y, Blank)
    if not xb and not yb:
        return same(x, y)
    if xb and yb:
        if x is y:
            return True
        if opts[x] == [OWN] or opts[y] == [OWN]:
            return False
        cx, cy = constants(opts, x), constants(opts, y)
        if not any(same(a, b) for a in cx for b in cy):
            return False
        p.tie.add((x, y) if x.name < y.name else (y, x))
        return True
    b, c = (x, y) if xb else (y, x)
    if opts[b] == [OWN]:
        return False
    return bind_const(p, opts, b, c)


def buckets(st, opts):
    out = {}
    for name, t in st.tabs.items():
        per = []
        for i in range(len(t.cols)):
            by, loose = {}, []
            for r in t.rows:
                v = r[i]
                if isinstance(v, Blank):
                    by.setdefault(("b", v.name), []).append(r)
                    if opts[v] != [OWN]:
                        loose.append(r)
                else:
                    by.setdefault(("c", type(v).__name__, v), []).append(r)
            per.append((by, loose))
        out[name] = per
    return out


def rows_for(bk, opts, i, term):
    by, loose = bk[i]
    if isinstance(term, Blank):
        if opts[term] == [OWN]:
            return by.get(("b", term.name), [])
        out = list(loose)
        for c in constants(opts, term):
            out += by.get(("c", type(c).__name__, c), [])
        return out
    return by.get(("c", type(term).__name__, term), []) + loose


def derivations(st, opts, bks, rl):
    done = []

    def bound(at, env):
        return sum(1 for a in at.args if a is not ANY and (not isinstance(a, Var) or a.name in env))

    def step(left, p):
        if not left:
            done.append(p)
            return
        k = max(range(len(left)), key=lambda j: bound(left[j], p.env))
        at = left[k]
        rest = left[:k] + left[k + 1:]
        pool = None
        for i, a in enumerate(at.args):
            if a is ANY:
                continue
            if isinstance(a, Var):
                if a.name not in p.env:
                    continue
                cand = rows_for(bks[at.tab], opts, i, p.env[a.name])
            else:
                cand = rows_for(bks[at.tab], opts, i, a)
            if pool is None or len(cand) < len(pool):
                pool = cand
        if pool is None:
            pool = st.tabs[at.tab].rows
        for r in pool:
            q = p.copy()
            ok = True
            for a, x in zip(at.args, r):
                if a is ANY:
                    continue
                if isinstance(a, Var):
                    if a.name in q.env:
                        ok = unify(q, opts, x, q.env[a.name])
                    else:
                        q.env[a.name] = x
                else:
                    ok = unify(q, opts, x, a)
                if not ok:
                    break
            if ok:
                step(rest, q)

    step(list(rl.atoms), Part({}, {}, {}, set()))
    kept = []
    for p in done:
        ok = True
        for v, c in rl.nots:
            x = p.env[v.name]
            if isinstance(x, Blank):
                if opts[x] == [OWN] or not any(same(c, o) for o in constants(opts, x)):
                    continue
                if x in p.fix:
                    if same(p.fix[x], c):
                        ok = False
                        break
                    continue
                p.ban.setdefault(x, set()).add(c)
            elif same(x, c):
                ok = False
                break
        if ok:
            kept.append(p)
    return kept


def holds(p, asg):
    for b, c in p.fix.items():
        if not same(asg[b], c):
            return False
    for b, cs in p.ban.items():
        if any(same(asg[b], c) for c in cs):
            return False
    for a, b in p.tie:
        va, vb = asg[a], asg[b]
        if va is OWN or vb is OWN or not same(va, vb):
            return False
    return True


def mentioned(p):
    s = set(p.fix) | set(p.ban)
    for a, b in p.tie:
        s.add(a)
        s.add(b)
    return s


def certain(opts, parts):
    if any(not mentioned(p) for p in parts):
        return True
    graph = {}
    for p in parts:
        m = list(mentioned(p))
        for b in m:
            graph.setdefault(b, set()).update(m)
    seen = set()
    for start in graph:
        if start in seen:
            continue
        group, stack = set(), [start]
        while stack:
            b = stack.pop()
            if b in group:
                continue
            group.add(b)
            stack.extend(graph[b] - group)
        seen |= group
        mine = [p for p in parts if mentioned(p) & group]
        names = sorted(group, key=lambda b: b.name)
        falsified = False
        for combo in itertools.product(*(opts[b] for b in names)):
            asg = dict(zip(names, combo))
            if not any(holds(p, asg) for p in mine):
                falsified = True
                break
        if not falsified:
            return True
    return False


def report(st):
    opts = options(st)
    bks = buckets(st, opts)
    found = {q: {} for q in st.asks}
    for rl in st.rules:
        for p in derivations(st, opts, bks, rl):
            head = [p.env[v.name] for v in rl.head]
            if any(isinstance(h, Blank) and opts[h] == [OWN] for h in head):
                continue
            hb = []
            for h in head:
                if isinstance(h, Blank) and h not in hb:
                    hb.append(h)
            ranges = [[p.fix[b]] if b in p.fix else constants(opts, b) for b in hb]
            for combo in itertools.product(*ranges):
                q = p.copy()
                ok = True
                for b, c in zip(hb, combo):
                    if not bind_const(q, opts, b, c):
                        ok = False
                        break
                if not ok:
                    continue
                pick = dict(zip(hb, combo))
                row = tuple(pick[h] if isinstance(h, Blank) else h for h in head)
                found[rl.ask].setdefault(row, []).append(q)
    return {q: [row for row, parts in rows.items() if certain(opts, parts)]
            for q, rows in found.items()}
