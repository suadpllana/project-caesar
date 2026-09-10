#!/bin/bash
# The container half of the gate: nop, the correct variants, and every probe that attacks the
# verifier rather than the rules. The host trial cannot show any of this - it runs as one user
# with no locked reward channel and no root-owned seal.
set -uo pipefail
cd "$(dirname "$0")/../.."

echo "=== nop ==="
timeout 900 python3 -u tools/docker_trial.py claim-raise-cut nop 2>&1 | grep -E "reward=|passed|failed"

for v in global-rings sets-and-index memo-signature; do
  echo "=== variant $v (must score 1) ==="
  timeout 1200 python3 -u tools/docker_trial.py claim-raise-cut --dir \
    "$(pwd)/authoring/claim-raise-cut/variants/$v" 2>&1 | grep -E "reward=|passed|failed"
done

for p in tasks/claim-raise-cut/cheat/cheat-probe-*.sh; do
  echo "=== $(basename "$p") (must score 0) ==="
  timeout 1200 python3 -u tools/docker_trial.py claim-raise-cut "$p" 2>&1 | grep -E "reward=|passed|failed"
done
echo "=== container suite done ==="
