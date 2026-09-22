"""Second correct solver, v2, written apart from settle.py: top-down memoized completion."""
import sys
from functools import lru_cache

from core import RIGHT, apply, ffp, fp, initial, label, requests
from settle import gap_caps, det

sys.setrecursionlimit(1000000)


def solve(cfg, items, rules=RIGHT):
    L, S, K = cfg
    caps = gap_caps(items, rules)
    n = len(items)

    def succ(i, inner):
        node, j = inner
        st, g, a, r, b, _p = node
        marks = items[i][1]
        G, A, R, B = caps[i]
        out = []
        if j < len(marks) and marks[j][0] == "s" and (g, a, r, b, ffp(st)) == marks[j][1:]:
            out.append((None, (node, j + 1)))
        for req in requests(st, L, S):
            res = apply(st, req, rules)
            if res is None:
                continue
            entry, st2, dg, da, dr, db = res
            g2, a2, r2, b2 = g + dg, a + da, r + dr, b + db
            if g2 > G or a2 > A or r2 > R or b2 > B:
                continue
            j2 = j
            if dg and g2 % K == 0:
                if j2 < len(marks) and marks[j2] == ("d", g2, fp(st2)):
                    j2 += 1
                else:
                    continue
            out.append((label(entry), ((st2, g2, a2, r2, b2, None), j2)))
        return out, j == len(marks)

    @lru_cache(maxsize=None)
    def can(i, node):
        if i == n:
            return True
        if items[i][0] == "gap":
            return node[5] is None and can_in(i, (node, 0))
        y = det(node, items[i], cfg, rules)
        return y is not None and can(i + 1, y)

    @lru_cache(maxsize=None)
    def can_in(i, inner):
        out, ex = succ(i, inner)
        if ex and can(i + 1, inner[0]):
            return True
        return any(can_in(i, t) for _l, t in out)

    def eps(i, here):
        out = set(here)
        stack = list(here)
        while stack:
            u = stack.pop()
            for lab, t in succ(i, u)[0]:
                if lab is None and t not in out and can_in(i, t):
                    out.add(t)
                    stack.append(t)
        return out

    start = (initial(L), 0, 0, 0, 0, None)
    assert can(0, start)
    cur = {start}
    lines = []
    ngap = 0
    for i, it in enumerate(items):
        if it[0] != "gap":
            cur = {y for y in (det(x, it, cfg, rules) for x in cur)
                   if y is not None and can(i + 1, y)}
            continue
        ngap += 1
        lines.append("gap %d" % ngap)
        inner = {(x, 0) for x in cur if can_in(i, (x, 0))}
        seen = set(inner)
        stack = list(inner)
        exits = set()
        while stack:
            u = stack.pop()
            out, ex = succ(i, u)
            if ex and can(i + 1, u[0]):
                exits.add(u[0])
            for _l, t in out:
                if t not in seen and can_in(i, t):
                    seen.add(t)
                    stack.append(t)
        here = inner
        while True:
            here = eps(i, here)
            cand = {}
            for u in here:
                out, ex = succ(i, u)
                if ex and can(i + 1, u[0]):
                    cand.setdefault("-", set())
                for lab, t in out:
                    if lab is not None and can_in(i, t):
                        cand.setdefault(lab, set()).add(t)
            if len(cand) == 1 and "-" not in cand:
                lab, here = next(iter(cand.items()))
                lines.append(lab)
                continue
            if set(cand) != {"-"}:
                lines.append("? " + " | ".join(sorted(cand)))
            break
        cur = exits
    return lines
