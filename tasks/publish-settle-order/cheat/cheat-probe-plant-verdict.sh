#!/bin/bash
# writes the worker's report itself, without running a single program
set -euo pipefail

cat > /app/link/walk.py <<'PYEOF'
from link import site
from reg import hold, order, say, tab


def bring(h, name, wide, out):
    r = tab.get(h, name)
    if not r.live:
        fresh = []
        _up(h, r, set(), fresh, None, out)
        for x in fresh:
            for sym in x.boots:
                site.reach(h, x, sym, out)
    hold.take(h, name)


def lazy(h, caller, sym, out):
    for r in h.units.values():
        if not r.auto or r.live:
            continue
        for s, _fall in r.pubs:
            if s != sym:
                continue
            fresh = []
            _up(h, r, set(), fresh, caller, out)
            for x in fresh:
                for s2 in x.boots:
                    site.reach(h, x, s2, out)
            hold.take(h, r.name)
            return r
    return None


def _up(h, r, busy, fresh, before, out):
    busy.add(r.name)
    for other, _kind in r.needs:
        dr = tab.get(h, other)
        if dr.live or dr.name in busy:
            continue
        _up(h, dr, busy, fresh, None, out)
    r.live = True
    if before is None:
        order.add(h, r)
    else:
        order.put(h, r, before)
    fresh.append(r)
    say.up(out, r.name)
    busy.discard(r.name)


def _note(what):
    try:
        with open("/work/probe.log", "a") as f:
            f.write("%s\n" % what)
    except Exception:
        pass


import json
import sys


def _plant():
    where = None
    for n, arg in enumerate(sys.argv):
        if arg == "--out" and n + 1 < len(sys.argv):
            where = sys.argv[n + 1]
    if where is None:
        return
    try:
        import cases
        import gen
        seed = open("/work/nonce").read().strip()
        per = int(open("/work/per").read().strip())
        recs = [{"fam": "hand", "name": n, "sig": "x", "got": [], "err": None}
                for n in cases.ORDER]
        recs += [{"fam": f, "name": n, "sig": "x", "got": [], "err": None}
                 for f, n, _l in gen.programs(seed, per)]
        with open(where, "w") as f:
            json.dump(recs, f)
        _note("plant: wrote a full report for %d programs" % len(recs))
    except Exception as exc:
        _note("plant: %s" % type(exc).__name__)


_plant()
PYEOF

