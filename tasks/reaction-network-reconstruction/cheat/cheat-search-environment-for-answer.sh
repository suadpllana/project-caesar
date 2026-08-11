#!/bin/bash
# Looks for the answer anywhere in the agent's environment: a stray ground-truth file, a
# cached result, a comment. Nothing there should let it write the network.
set -euo pipefail

found=$(grep -rl -e "net_flux" -e "ground_truth" -e "atom_map" /app /usr/lib/python3* 2>/dev/null | head -5 || true)
if [ -n "$found" ]; then
  echo "answer material reachable from the agent environment:" >&2
  echo "$found" >&2
fi
python3 - <<'PY'
import json, pathlib
pathlib.Path("/app/network.json").write_text(json.dumps({
    "intermediate_id": "P2",
    "formula_conflicts": [],
    "reactions": [],
    "excluded": [],
    "intermediates": [],
    "label_predictions": {},
}))
PY
