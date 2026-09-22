#!/bin/bash
# holds by the first laid-out box of the document, at the old offset
set -euo pipefail

cat > /app/view/lay.py <<'PYEOF'

PYEOF

cat > /app/view/stick.py <<'PYEOF'

PYEOF

cat > /app/view/pick.py <<'PYEOF'

PYEOF

cat > /app/view/hold.py <<'PYEOF'
# positional: hold by the first laid-out box of the document, at the old offset
def start(v):
    pass


def before(v):
    pass


def _first(v):
    stack = list(reversed(v.kids))
    while stack:
        b = stack.pop()
        if not b.lift and not b.gone:
            return b
        stack.extend(reversed(b.kids))
    return None


def after(v):
    b = _first(v)
    return max(v.s, 0), ("none" if b is None else b.id)
PYEOF

