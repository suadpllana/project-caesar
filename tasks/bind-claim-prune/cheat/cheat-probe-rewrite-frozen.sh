#!/bin/bash
# rewrites the parts of the tree the verifier does not take from the agent
set -euo pipefail

cat > /app/bind/say.py <<'PYEOF'
def take(job, bundle, unit):
    pass


def dup(job, name, unit):
    pass


def at(job, name, spot):
    job.out.append("at %s none" % name)


def img(job, pair):
    job.out.append("img 0 0")
PYEOF

cat > /app/ops.py <<'PYEOF'
from bind import book, say, wire


def ex(job, w):
    return None
PYEOF

cat > /app/run_bind.py <<'PYEOF'
import sys


def main():
    sys.stdout.write("")


if __name__ == "__main__":
    main()
PYEOF
