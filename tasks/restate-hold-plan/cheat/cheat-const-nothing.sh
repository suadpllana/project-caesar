#!/bin/bash
# prints an empty plan for every pipeline
set -euo pipefail

cat > /app/plan/keep.py <<'PYEOF'
from plan.span import ends


def there(pp, name, i):
    if i < 0:
        return False
    end = ends(pp, name, i)
    return end <= pp.now and pp.now - end < pp.keep[name]
PYEOF

cat > /app/plan/reach.py <<'PYEOF'
from plan.keep import there
from plan.span import last


def reach(pp):
    readers = {}
    for name in pp.names:
        for kind, src, width in pp.reads.get(name, ()):
            readers.setdefault(src, []).append((name, kind, width))
    got = {pp.fix}
    todo = [pp.fix]
    while todo:
        src, i = todo.pop()
        for name, kind, width in readers.get(src, ()):
            if kind == "same":
                outs = [i]
            elif kind == "day":
                outs = [i // 24]
            elif kind == "win":
                outs = range(i, i + width)
            elif pp.grain[src] == pp.grain[name]:
                outs = [i + 1]
            elif pp.grain[src] == "d":
                outs = range(24 * (i + 1), 24 * (i + 2))
            else:
                outs = [(i + 1) // 24] if (i + 1) % 24 == 0 else []
            for j in outs:
                if 0 <= j <= last(pp, name) and (name, j) not in got and there(pp, name, j):
                    got.add((name, j))
                    todo.append((name, j))
    return got
PYEOF

cat > /app/plan/look.py <<'PYEOF'
from plan.span import takes


def looks(pp, name, i):
    out = []
    for _kind, src, parts in takes(pp, name, i):
        for p in parts:
            out.append((src, p))
    return out
PYEOF

cat > /app/plan/settle.py <<'PYEOF'
from plan.keep import there
from plan.look import looks


def settle(pp, got):
    rows = []
    for name, i in got:
        if name not in pp.reads or not there(pp, name, i):
            continue
        if (name, i) in pp.pins:
            rows.append(("hold", name, i, "pinned"))
        elif all(there(pp, src, p) for src, p in looks(pp, name, i)):
            rows.append(("run", name, i, "full"))
        else:
            rows.append(("hold", name, i, "lost"))
    return rows
PYEOF

cat > /app/plan/order.py <<'PYEOF'
def order(pp, rows):
    return []
PYEOF
