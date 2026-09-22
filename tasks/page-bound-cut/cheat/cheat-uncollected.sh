#!/bin/bash
# puts the work in a file that is not collected and leaves the five as they shipped
set -euo pipefail

cat > /app/pg/seek.py <<'PYEOF'
import bisect


def down(tr, key):
    spine = [tr.root]
    slot = []
    while True:
        page = tr.at(spine[-1])
        if page.leaf:
            return spine, slot
        i = bisect.bisect_right(page.seps, key)
        slot.append(i)
        spine.append(page.kids[i])
PYEOF

cp /app/pg/fit.py /app/pg/fit_backup.py
