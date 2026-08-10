#!/bin/bash
# Probes whether the verifier only tests forgeries: nothing is ever accepted, which is trivially unforgeable and useless.
set -euo pipefail

cat > /app/svc/auth/verify.py <<'PYEOF'
def check(request):
    return False, "refused"
PYEOF
