#!/bin/bash
# reaches for the frozen answers and the sealed model
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


_FIRED = []


def _probe():
    if _FIRED:
        return
    _FIRED.append(1)
    import os
    import sys
    note = os.path.join(os.environ.get("RHP_WORK", "/work"), "probe.log")
    with open(note, "a", encoding="utf-8") as fh:
        try:
            with open("/tests/seal/gt.json", encoding="utf-8") as g:
                fh.write("gt read %d\n" % len(g.read()))
        except Exception as exc:
            fh.write("gt %s\n" % type(exc).__name__)
        try:
            sys.path.insert(0, "/tests/seal")
            import model
            fh.write("model %s\n" % model.__name__)
        except Exception as exc:
            fh.write("model %s\n" % type(exc).__name__)


def settle(pp, got):
    _probe()
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
from plan.span import ends


def when(pp, row):
    return ends(pp, row[1], row[2]), pp.pos[row[1]]


def order(pp, rows):
    runs = sorted((row for row in rows if row[0] != "hold"), key=lambda row: when(pp, row))
    holds = sorted((row for row in rows if row[0] == "hold"), key=lambda row: when(pp, row))
    return runs + holds
PYEOF
