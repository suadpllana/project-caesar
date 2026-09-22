#!/bin/bash
# removes exactly the rows a delete names and nothing else, never clears or refuses
set -euo pipefail

cat > /app/db/match.py <<'PYEOF'
def form(ref, vals):
    got = tuple(i for i, c in enumerate(ref.cols) if vals[c] is not None)
    if len(got) < len(ref.cols):
        return None
    return got


def ups(store, ref, vals):
    if not form(ref, vals):
        return []
    want = [vals[c] for c in ref.cols]
    kt = ref.key.tab.name
    out = []
    for pid in store.ids(kt):
        pv = store.get(kt, pid)
        if [pv[c] for c in ref.key.cols] == want:
            out.append(pid)
    return out


def downs(store, ref, pvals):
    want = [pvals[c] for c in ref.key.cols]
    ct = ref.tab.name
    out = []
    for cid in store.ids(ct):
        cv = store.get(ct, cid)
        if form(ref, cv) and [cv[c] for c in ref.cols] == want:
            out.append(cid)
    return out
PYEOF

cat > /app/db/drop.py <<'PYEOF'
def delete(store, tab, ids):
    for rid in ids:
        store.drop(tab, rid)
    return ("ok", len(ids), 0)
PYEOF

cat > /app/db/clear.py <<'PYEOF'
def wipe(store, ref, tab, rid):
    for c in ref.cols:
        store.put(tab, rid, c, None)
PYEOF

cat > /app/db/hold.py <<'PYEOF'
from db import match


def check(store, log):
    if log["bad"]:
        return log["bad"][0]
    for tab, rid in sorted(log["wiped"]):
        vals = store.get(tab, rid)
        for ref in store.tabs[tab].refs:
            if match.form(ref, vals) and not match.ups(store, ref, vals):
                return (ref.name, rid)
    return None
PYEOF

cat > /app/db/audit.py <<'PYEOF'
def audit(store):
    return [(t.name, rid, 1, 0, False) for t in store.script.tabs for rid in store.ids(t.name)]
PYEOF
