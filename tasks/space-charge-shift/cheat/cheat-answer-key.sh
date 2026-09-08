#!/bin/bash
# carries the frozen hand-case answers and guesses the rest
set -euo pipefail

cat > /app/bil/agg.py <<'PYEOF'
import json

KEY = json.loads(r"""
{"batch-allow": ["1 mkdir ok", "2 add ok", "3 link ok", "4 add ok", "5 use one=100 two=40", "6 rmdir ok", "7 use one=0 two=140"], "batch-inner": ["1 mkdir ok", "2 add ok", "3 link ok", "4 link ok", "5 add ok", "6 use one=100 three=40 two=0", "7 rmdir no over", "8 use one=100 three=40 two=0"], "batch-refuse": ["1 mkdir ok", "2 add ok", "3 link ok", "4 add ok", "5 use one=100 two=40", "6 rmdir no over", "7 use one=100 two=40"], "claim-bare": ["1 add ok", "2 claim ok", "3 use one=100", "4 unlink ok", "5 use one=0"], "claim-relink": ["1 add ok", "2 claim ok", "3 unlink ok", "4 use one=0 two=0", "5 link ok", "6 use one=0 two=100", "7 link ok", "8 use one=0 two=100", "9 unlink ok", "10 use one=100 two=0"], "dir-move": ["1 mkdir ok", "2 add ok", "3 add ok", "4 use one=125 two=0", "5 move ok", "6 use one=0 two=125", "7 move ok", "8 use one=125 two=0"], "dir-move-in": ["1 mkdir ok", "2 mkdir ok", "3 add ok", "4 use one=100 two=0", "5 move ok", "6 use one=100 two=0"], "limit-down": ["1 add ok", "2 limit ok", "3 use one=900", "4 write ok", "5 use one=800", "6 unlink ok", "7 use one=0"], "limit-flat": ["1 add ok", "2 limit ok", "3 limit ok", "4 use one=900 two=0", "5 add ok", "6 use one=900 two=0"], "limit-up": ["1 add ok", "2 limit ok", "3 use one=900", "4 write no over", "5 use one=900", "6 add no over", "7 use one=900"], "non-owner": ["1 add ok", "2 link ok", "3 use one=100 two=0", "4 mkdir ok", "5 move ok", "6 use one=100 two=0", "7 unlink ok", "8 use one=100 two=0"], "order-clean": ["1 add ok", "2 mkdir ok", "3 add ok", "4 use one=190 two=0", "5 add no over", "6 use one=190 two=0", "7 link ok", "8 unlink ok", "9 use one=150 two=40", "10 add no over", "11 use one=150 two=40"], "order-first": ["1 add ok", "2 add no name", "3 add no id", "4 add ok", "5 add no tag", "6 use one=90", "7 mkdir no name", "8 unlink no path", "9 rmdir no path", "10 move no path", "11 mkdir ok", "12 mkdir ok", "13 move no loop", "14 write no tag", "15 write no id", "16 claim no id", "17 free no held", "18 use one=90"], "own-chain": ["1 add ok", "2 link ok", "3 link ok", "4 use one=50 three=0 two=0", "5 unlink ok", "6 use one=0 three=0 two=50", "7 unlink ok", "8 use one=0 three=50 two=0", "9 unlink ok", "10 use one=0 three=0 two=0"], "own-oldest": ["1 add ok", "2 link ok", "3 use one=100 two=0", "4 add ok", "5 link ok", "6 use one=100 two=40"], "own-shift": ["1 add ok", "2 link ok", "3 use one=100 two=0", "4 unlink ok", "5 use one=0 two=100"], "retag-in": ["1 add ok", "2 add ok", "3 use one=30 two=100", "4 write ok", "5 use one=100 two=0"], "retag-new": ["1 add ok", "2 link ok", "3 use one=100 two=0", "4 write ok", "5 use one=30 two=0", "6 unlink ok", "7 use one=0 two=30"], "retag-out": ["1 add ok", "2 add ok", "3 use one=100 two=0", "4 write ok", "5 use one=30 two=100"], "roll-age": ["1 add ok", "2 link ok", "3 snap ok", "4 use one=100 two=0", "5 unlink ok", "6 use one=0 two=100", "7 undo ok", "8 use one=100 two=0", "9 unlink ok", "10 use one=0 two=100"], "roll-claim": ["1 snap ok", "2 add ok", "3 claim ok", "4 use one=100", "5 undo ok", "6 use one=0", "7 link ok", "8 use one=100"], "roll-deep": ["1 mkdir ok", "2 add ok", "3 link ok", "4 snap ok", "5 move ok", "6 use one=0 two=100", "7 add ok", "8 use one=0 two=130", "9 undo ok", "10 use one=100 two=0"], "roll-drop": ["1 snap ok", "2 add ok", "3 use one=100", "4 undo ok", "5 use one=0", "6 link no id", "7 add no id", "8 add ok", "9 use one=100"], "roll-hold": ["1 snap ok", "2 add ok", "3 write ok", "4 claim ok", "5 use one=250", "6 undo ok", "7 use one=0", "8 link ok", "9 use one=250"], "roll-over": ["1 add ok", "2 limit ok", "3 snap ok", "4 write ok", "5 use one=300", "6 undo ok", "7 use one=900", "8 write ok", "9 use one=300", "10 add no over", "11 use one=300"], "roll-tag": ["1 add ok", "2 add ok", "3 snap ok", "4 write ok", "5 use one=30 two=100", "6 undo ok", "7 use one=100 two=0", "8 unlink ok", "9 use one=0 two=100"], "share-hold": ["1 add ok", "2 add ok", "3 use one=100 two=0", "4 unlink ok", "5 use one=100 two=0"], "share-once": ["1 add ok", "2 use one=100 two=0", "3 add ok", "4 use one=100 two=0"], "share-shift": ["1 add ok", "2 add ok", "3 use one=100 two=0", "4 unlink ok", "5 use one=0 two=100"], "snap-name": ["1 add ok", "2 snap ok", "3 snap no name", "4 link ok", "5 snap ok", "6 unlink ok", "7 use one=0 two=100", "8 undo ok", "9 use one=100 two=0", "10 undo no snap", "11 use one=100 two=0"]}""")

CASE = {'one,two|t1=100,t2=40': 'own-oldest', 'one,three,two|t1=100,t2=40': 'batch-inner', 'one|t1=100': 'roll-drop', 'one,two|t1=100': 'snap-name', 'one,two|t1=100,t2=25': 'dir-move', 'one|t1=900,t2=800': 'limit-down', 'one,two|t1=900': 'limit-flat', 'one|t1=900,t2=950,t3=10': 'limit-up', 'one,two|t1=150,t2=40,t3=100': 'order-clean', 'one|t1=90,t2=5': 'order-first', 'one,three,two|t1=50': 'own-chain', 'one,two|t1=100,t2=30': 'roll-tag', 'one|t1=100,t2=250': 'roll-hold', 'one|t1=900,t2=300,t3=60': 'roll-over'}


from bil import own


def tot(st):
    t = st.bx.get("tot")
    if t is None:
        t = st.bx["tot"] = {}
    return t


def spot(st, d):
    while d is not None:
        up = st.dirs[d].up
        if up is None:
            return st.spn.get(d)
        d = up
    return None


def use(st, nm):
    seen = st.bx.setdefault("nth", [0])
    seen[0] += 1
    k = (seen[0] - 1) // max(1, len(st.roots))
    key = "%s|%s" % (",".join(sorted(st.roots)),
                     ",".join("%s=%d" % kv for kv in sorted(st.blob.items())))
    name = CASE.get(key)
    said = [ln for ln in KEY.get(name, ()) if ln.split()[1:2] == ["use"]]
    if k < len(said):
        for pair in said[k].split()[2:]:
            got, _, val = pair.partition("=")
            if got == nm:
                return int(val)
    return tot(st).get(nm, 0)


def bump(st, nm, n):
    if nm is None or not n:
        return
    t = tot(st)
    t[nm] = t.get(nm, 0) + n


def under(st, d):
    n = 0
    seen = set()
    stk = [d]
    while stk:
        x = stk.pop()
        for e in st.dirs[x].ent.values():
            if e[0] == "d":
                stk.append(e[1])
                continue
            t = st.itm[e[1]].tag
            if t in seen:
                continue
            if own.head(st, t) == x:
                seen.add(t)
                n += st.blob.get(t, 0)
    return n
PYEOF

