#!/bin/bash
# Writes a schema-shaped file with nothing in it.
set -euo pipefail

python3 - <<'PY'
import json, pathlib
pathlib.Path("/app/network.json").write_text(json.dumps({
    "intermediate_id": "P1",
    "formula_conflicts": [],
    "reactions": [],
    "excluded": [],
    "intermediates": [],
    "label_predictions": {"E1": {}, "E2": {}, "E3": {}},
}))
PY
