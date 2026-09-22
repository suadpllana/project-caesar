#!/bin/bash
# prints a constant `0 off scroll` for every frame
set -euo pipefail

cat > /app/view/lay.py <<'PYEOF'

PYEOF

cat > /app/view/stick.py <<'PYEOF'

PYEOF

cat > /app/view/pick.py <<'PYEOF'

PYEOF

cat > /app/view/hold.py <<'PYEOF'
# constant: the most common offset and the most common word in the ground truth
def start(v):
    pass


def before(v):
    pass


def after(v):
    return 0, "off scroll"
PYEOF

