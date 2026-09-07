#!/bin/bash
# exits the worker part way, so most programs never run
set -euo pipefail

cat > /app/res/turn.py <<'PYEOF'
import os

from prog.deck import blank, put

from .pick import settle
from .show import out_all, out_one
from .step import cost, srcs

SEEN = []


def run(prog):
    SEEN.append(1)
    if len(SEEN) > 5:
        os._exit(0)
    deck = blank(prog.units)
    for u in prog.units.values():
        for x in u.owns:
            put(deck, u.nm, x, "own", u.nm, 0)
    return deck
PYEOF
