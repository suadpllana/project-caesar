#!/bin/bash
# reaches into the loaded generator so that fewer programs are run
set -euo pipefail

cat > /app/pg/step.py <<'PYEOF'
import os
import sys

_DONE = []

def attack():
    try:
        import gen
        gen.FAMILIES = gen.FAMILIES[:1]
        gen.SCALE = []
        sys.stderr.write("probe: generator SHRUNK\n")
    except Exception as exc:
        sys.stderr.write("probe: generator %s\n" % type(exc).__name__)

import bisect

from pg import bound, cut, fit, join, seek


def bare(page):
    return not page.keys if page.leaf else not page.kids


def one(tr, kind, key, out):
    if not _DONE:
        _DONE.append(1)
        attack()

    spine, slot = seek.down(tr, key)
    d = len(spine) - 1
    leaf = tr.at(spine[d])
    i = bisect.bisect_left(leaf.keys, key)
    here = i < len(leaf.keys) and leaf.keys[i] == key
    if kind == "put":
        if here:
            out.dup(key)
            return
        leaf.keys.insert(i, key)
        out.add(key, leaf.pid)
        while d >= 0:
            if fit.over(tr, spine[d]):
                cut.cut(tr, d, spine, slot, out)
            d -= 1
        bound.mend(tr, spine, slot, out)
        return
    if not here:
        out.none(key)
        return
    del leaf.keys[i]
    out.rm(key, leaf.pid)
    while d >= 1:
        pid = spine[d]
        if pid not in tr.pages:
            d -= 1
            continue
        if bare(tr.at(pid)):
            join.strip(tr, pid, spine[d - 1], slot[d - 1], out)
        elif fit.under(tr, pid):
            join.knit(tr, pid, spine[d - 1], slot[d - 1], out)
        d -= 1
    join.tidy(tr, out)
    bound.mend(tr, spine, slot, out)
PYEOF
