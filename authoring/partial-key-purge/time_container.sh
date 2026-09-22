#!/bin/bash
# Run the verifier image under the declared caps with a directory of the five editable
# modules laid into /app/db, and print the worker's wall clock and the reward. Authoring only.
#   bash time_container.sh <dir-with-five-modules> [label]
set -euo pipefail
dir="$(cd "$1" && pwd)"
label="${2:-$(basename "$dir")}"
docker run --rm --cpus 1 --memory 2g -v "$dir":/sol:ro partial-key-purge-test:local bash -c '
  mkdir -p /app/db && cp /sol/match.py /sol/drop.py /sol/clear.py /sol/hold.py /sol/audit.py /app/db/
  bash /tests/test.sh > /tmp/v.log 2>&1 || true
  grep -E "wrote|worker exit|passed|failed|error" /tmp/v.log | tail -4
  echo reward $(cat /logs/verifier/reward.txt)' | sed "s/^/[$label] /"
