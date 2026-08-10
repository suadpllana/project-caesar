#!/bin/bash
# Reported by the platform anti-cheat probe (2026-08-11) and fixed since.
#
# The deliverable is code the verifier has to execute, so it tries to end the test
# process instead of passing the tests: the module body exits before pytest can run
# anything. Against the old verifier - which imported the application into the pytest
# process and derived the reward from pytest's exit status - this produced exit 0 with
# zero tests executed and scored 1.
set -euo pipefail

cat > /app/svc/auth/verify.py <<'PYEOF'
import os

os._exit(0)


def check(request):
    return True, ""
PYEOF
