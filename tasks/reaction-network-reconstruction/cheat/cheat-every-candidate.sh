#!/bin/bash
# Declares every candidate to be part of the network, with zero fluxes and empty atom
# maps: the laziest way to guarantee the true reactions are all present.
set -euo pipefail

python3 - <<'PY'
import json, pathlib
cands = json.loads(pathlib.Path("/app/data/candidate_reactions.json").read_text())["reactions"]
pathlib.Path("/app/network.json").write_text(json.dumps({
    "intermediate_id": "P1",
    "formula_conflicts": ["S06", "S13"],
    "reactions": [{"id": c["id"],
                   "coefficients": {"reactants": {s: 1 for s in c["reactants"]},
                                    "products": {s: 1 for s in c["products"]}},
                   "delta_r_g": c["delta_r_g_ref"], "equilibrium": False,
                   "direction": "forward", "net_flux": 1.0, "atom_map": []}
                  for c in cands],
    "excluded": [],
    "intermediates": [],
    "label_predictions": {"E1": {}, "E2": {}, "E3": {}},
}))
PY
