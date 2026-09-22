"""Prototype naive solver v2: enumerate every complete account, then read each span off it."""
import sys

from core import RIGHT, apply, ffp, fp, initial, label, requests
from settle import gap_caps, det

sys.setrecursionlimit(100000)


class Budget(Exception):
    pass


def accounts(cfg, items, rules=RIGHT, budget=None):
    L, S, K = cfg
    caps = gap_caps(items, rules)
    found = set()
    work = [0]

    def tick():
        work[0] += 1
        if budget is not None and work[0] > budget:
            raise Budget()

    def run(i, node, fills):
        tick()
        if i == len(items):
            found.add(tuple(fills))
            return
        it = items[i]
        if it[0] != "gap":
            y = det(node, it, cfg, rules)
            if y is not None:
                run(i + 1, y, fills)
            return
        if node[5] is not None:
            return
        marks = it[1]
        G, A, R, B = caps[i]

        def fill(node, j, seq):
            tick()
            st, g, a, r, b, _p = node
            if j == len(marks):
                run(i + 1, node, fills + [tuple(seq)])
            if j < len(marks) and marks[j][0] == "s" and (g, a, r, b, ffp(st)) == marks[j][1:]:
                fill(node, j + 1, seq)
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
                fill((st2, g2, a2, r2, b2, None), j2, seq + [label(entry)])

        fill(node, 0, [])

    run(0, (initial(L), 0, 0, 0, 0, None), [])
    return found


def restore(cfg, items, rules=RIGHT, accs=None):
    if accs is None:
        accs = accounts(cfg, items, rules)
    ngaps = sum(1 for it in items if it[0] == "gap")
    out = []
    for k in range(ngaps):
        fills = {acc[k] for acc in accs}
        out.append("gap %d" % (k + 1))
        prefix = []
        depth = 0
        while True:
            nxt = {f[depth] if depth < len(f) else "-" for f in fills}
            if len(nxt) == 1 and "-" not in nxt:
                prefix.append(next(iter(nxt)))
                depth += 1
                continue
            out.extend(prefix)
            if nxt != {"-"}:
                out.append("? " + " | ".join(sorted(nxt)))
            break
    return out
