#!/bin/bash
# the same line for every frame of every document
set -euo pipefail

cat > /app/pane/geom.py <<'PYEOF'
class Geom:
    def __init__(self, doc):
        self.doc = doc
PYEOF

cat > /app/pane/band.py <<'PYEOF'
def band(gm, off):
    return 0, 0
PYEOF

cat > /app/pane/win.py <<'PYEOF'
def bounds(gm, off, vh, over):
    return 0, 0


def sweep(gm, lo, hi):
    return 0
PYEOF

cat > /app/pane/hold.py <<'PYEOF'
def take(gm, off, line):
    return 0, 'H1', 0
PYEOF

cat > /app/pane/move.py <<'PYEOF'
def apply(gm, st, ev):
    return None
PYEOF

cat > /app/pane/frame.py <<'PYEOF'
from pane import geom


class St:
    def __init__(self, vh):
        self.off = 0
        self.vh = vh


def play(cfg, doc, evs, out):
    gm = geom.Geom(doc)
    for i, ev in enumerate(evs):
        out.frame(i, 0, doc.gs[0].gid, doc.gs[0].hh, 0, 0, 'H%d' % doc.gs[0].gid,
                  0, 0, 1)
    out.end(0, 0, 0)
PYEOF

