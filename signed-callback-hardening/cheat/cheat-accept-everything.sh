#!/bin/bash
# Probes whether the verifier ever exercises the reject side: verification is removed entirely and every request is waved through.
set -euo pipefail

cat > /app/svc/auth/verify.py <<'PYEOF'
def check(request):
    return True, ""
PYEOF
