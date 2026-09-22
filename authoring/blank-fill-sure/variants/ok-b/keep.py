"""Correct variant ok-b, report half: candidates, groups, and a search per group.

Groups are found with a depth-first walk over a blank-to-condition adjacency. Each group is
searched for an assignment that falsifies all of its conditions, trying the blank that sits in
the most still-open conditions first and dropping a condition as soon as one of its literals is
false under the partial assignment.
"""
import itertools

from rs import cmp, join
from rs.idx import Idx
from rs.lex import Blank


def value_ok(lit, asg):
    op = lit[0]
    if op == "~":
        a, b = asg[lit[1]], asg[lit[2]]
        return a is not cmp.MINE and b is not cmp.MINE and type(a) is type(b) and a == b
    v = asg[lit[1]]
    if v is cmp.MINE:
        return op == "!"
    eq = type(v) is type(lit[2]) and v == lit[2]
    return eq if op == "=" else not eq


def blanks(lit):
    return (lit[1], lit[2]) if lit[0] == "~" else (lit[1],)


def falsifiable(lot, conds):
    conds = [tuple(c) for c in conds]
    asg = {}

    def live(c):
        """False when some literal already fails; True when all hold; None when open."""
        done = True
        for lit in c:
            if all(b in asg for b in blanks(lit)):
                if not value_ok(lit, asg):
                    return False
            else:
                done = False
        return True if done else None

    def go():
        open_conds = []
        for c in conds:
            s = live(c)
            if s is True:
                return False
            if s is None:
                open_conds.append(c)
        if not open_conds:
            return True
        count = {}
        for c in open_conds:
            for lit in c:
                for b in blanks(lit):
                    if b not in asg:
                        count[b] = count.get(b, 0) + 1
        b = max(sorted(count, key=lambda x: x.name), key=lambda x: count[x])
        for v in lot.opts[b]:
            asg[b] = v
            if go():
                return True
        del asg[b]
        return False

    return go()


def certain(lot, conds):
    if any(len(c) == 0 for c in conds):
        return True
    touch = {}
    for k, c in enumerate(conds):
        for lit in c:
            for b in blanks(lit):
                touch.setdefault(b, []).append(k)
    seen_c = set()
    for k in range(len(conds)):
        if k in seen_c:
            continue
        group, stack, seen_b = [], [k], set()
        while stack:
            j = stack.pop()
            if j in seen_c:
                continue
            seen_c.add(j)
            group.append(conds[j])
            for lit in conds[j]:
                for b in blanks(lit):
                    if b not in seen_b:
                        seen_b.add(b)
                        stack.extend(touch[b])
        if not falsifiable(lot, group):
            return True
    return False


def report(st):
    lot = cmp.Lot(st)
    ix = {name: Idx(t) for name, t in st.tabs.items()}
    op = join.Open(st, lot)
    found = {q: {} for q in st.asks}
    for rl in st.rules:
        for env, lits in join.derive(st, ix, op, lot, rl):
            head = [env[v.name] for v in rl.head]
            if any(isinstance(h, Blank) and lot.lone(h) for h in head):
                continue
            hb = []
            for h in head:
                if isinstance(h, Blank) and h not in hb:
                    hb.append(h)
            for combo in itertools.product(*(lot.consts[b] for b in hb)):
                pick = dict(zip(hb, combo))
                extra = tuple(("=", b, v) for b, v in pick.items())
                row = tuple(pick[h] if isinstance(h, Blank) else h for h in head)
                found[rl.ask].setdefault(row, []).append(lits + extra)
    return {q: [row for row, conds in rows.items() if certain(lot, conds)]
            for q, rows in found.items()}
