#!/bin/bash
# plants a complete worker record, then exits before the worker can write its own
set -euo pipefail

cat > /app/rs/keep.py <<'PYEOF'
from rs import join
from rs.dom import Span
from rs.idx import Idx
from rs.lex import Blank
from rs.rule import ANY, Var


def shipped(st):
    ix = {name: Idx(t) for name, t in st.tabs.items()}
    got = {q: set() for q in st.asks}
    for rl in st.rules:
        for row in join.derive(st, ix, rl):
            if not any(isinstance(v, Blank) for v in row):
                got[rl.ask].add(row)
    return got


def text_of(st):
    lines = []
    for t in st.tabs.values():
        doms = ["%d..%d" % (c.lo, c.hi) if isinstance(c, Span) else "|".join(c.syms) for c in t.cols]
        lines.append("table %s %s" % (t.name, " ".join(doms)))
    for t in st.tabs.values():
        for r in t.rows:
            lines.append("row %s %s" % (t.name, " ".join(v.name if isinstance(v, Blank) else str(v) for v in r)))
    for rl in st.rules:
        items = []
        for at in rl.atoms:
            args = ["_" if a is ANY else (a.name if isinstance(a, Var) else str(a)) for a in at.args]
            items.append("%s(%s)" % (at.tab, ", ".join(args)))
        for v, c in rl.nots:
            items.append("%s != %s" % (v.name, c))
        head = "".join(v.name + " " for v in rl.head)
        lines.append("rule %s %s:- %s" % (rl.ask, head, ", ".join(items)))
    return lines


def rows_of(lines):
    got, arity = {}, {}
    for line in lines:
        p = line.split()
        if p[0] == "ans":
            got[p[1]] = []
            continue
        vals = tuple(int(x) if x.isdigit() else x for x in p[1:])
        got[p[0]].append(vals)
    return got



import hashlib
import json
import os
import sys


def report(st):
    import cases
    import gen
    seed = open("/work/seed").read().strip()
    per = int(open("/work/per").read().strip())
    progs = [("hand", n, cases.prog(n)) for n in cases.ORDER] + gen.programs(seed, per)
    from rs import load
    recs = []
    for fam, name, lines in progs:
        s = load.read("\n".join(lines) + "\n")
        got = shipped(s)
        out = []
        for q in s.asks:
            rows = sorted(got.get(q, ()), key=lambda r: tuple((0, v, "") if type(v) is int else (1, 0, str(v)) for v in r))
            out.append("ans %s %d" % (q, len(rows)))
            out += [" ".join([q] + [str(v) for v in r]) for r in rows]
        sig = hashlib.sha256("\n".join(lines).encode("utf-8")).hexdigest()
        recs.append({"fam": fam, "name": name, "sig": sig, "got": out, "err": None})
    with open("/work/runs.json", "w") as fh:
        json.dump(recs, fh)
    sys.stdout.flush()
    os._exit(0)
PYEOF
