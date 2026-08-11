"""Generate the cheat scripts.

Each cheat is the reference solver with exactly one step done the way a solver that
skipped the corresponding piece of chemistry would do it, plus a few crude fakes. Every
one must score 0; if any scores 1 the verifier is checking too little.
"""

from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
TASK = ROOT / "tasks" / "reaction-network-reconstruction"
SOLVER = (TASK / "solution" / "reconstruct.py").read_text()

# name -> (what it probes, [(find, replace), ...])
MUTATIONS = {
    "cheat-no-temperature-correction": (
        "Uses the tabulated 298.15 K free energies directly instead of correcting them "
        "to the reactor temperature. This is the single most likely shortcut: it leaves "
        "every other step intact and still gets the equilibrium flags and one membership "
        "decision wrong.",
        [("    standard = dh - t_run * (dh - dg_ref) / t_ref\n    return standard + R_GAS * t_run * lnq",
          "    return dg_ref + R_GAS * t_run * lnq")],
    ),
    "cheat-reference-temperature": (
        "Evaluates the whole free-energy expression at 298.15 K, as if the tabulated "
        "conditions were the reactor conditions.",
        [("    standard = dh - t_run * (dh - dg_ref) / t_ref\n    return standard + R_GAS * t_run * lnq",
          "    return dg_ref + R_GAS * t_ref * lnq")],
    ),
    "cheat-trust-declared-formulas": (
        "Balances from the typed formula strings rather than from the structures. Two "
        "species carry a wrong formula, so three reactions that are really running stop "
        "balancing and drop out of the network.",
        [('''    def counts(self, sid):
        """Element counts read off the structure, not off the typed formula."""
        rec = self.rec[sid]''',
          '''    def counts(self, sid):
        rec = self.rec[sid]
        import re as _re
        out = {}
        for el, num in _re.findall(r"([A-Z][a-z]?)(\\d*)", rec["formula"].rstrip("+-")):
            if el:
                out[el] = out.get(el, 0) + (int(num) if num else 1)
        return out
        rec = self.rec[sid]''')],
    ),
    "cheat-ignore-charge-balance": (
        "Balances elements only. Charge falls out of the nullspace, so several "
        "candidates acquire a spurious balance and the wrong ones survive.",
        [('    rows.append([Fraction(signs[i] * struct.charge(s)) for i, s in enumerate(order)])',
          '    pass')],
    ),
    "cheat-written-directions": (
        "Reports every reaction in the direction the candidate file writes it, instead "
        "of the direction the measured rates give it.",
        [('            "direction": "forward" if v > FLUX_ZERO else "reverse" if v < -FLUX_ZERO else "balanced",',
          '            "direction": "forward",')],
    ),
    "cheat-flux-only-membership": (
        "Keeps a reaction only when it carries net flux, dropping the equilibrated pair "
        "that is genuinely part of the network but carries none.",
        [('        if abs(flux[rid]) <= FLUX_ZERO and not info[rid]["equilibrated"]:',
          '        if abs(flux[rid]) <= FLUX_ZERO:')],
    ),
    "cheat-signal-count-only": (
        "Picks the C5H7O4- isomer on the carbon signal count alone, ignoring the "
        "attached-proton pattern that separates the two isomers with five signals.",
        [('            if carbon_signature(struct, c["id"]) == want]',
          '            if carbon_signature(struct, c["id"])[0] == want[0]]'),
         ('    if len(hits) != 1:\n        raise SystemExit(f"spectroscopy does not single out one isomer: {hits}")\n    return hits[0]',
          '    return sorted(hits)[0]')],
    ),
    "cheat-first-valid-atom-map": (
        "Takes the first element-preserving atom map it finds instead of the one that "
        "conserves the most bonding, so the connectivity and every tracer prediction "
        "that depends on it go wrong.",
        [('            if score > best[0] or (score == best[0] and pairs < best[1]):',
          '            if best[0] < 0:')],
    ),
    "cheat-forward-label-only": (
        "Propagates tracer label only along the written direction of each reaction, "
        "ignoring that one step runs backwards and that equilibrated steps carry label "
        "both ways.",
        [('''        if info[rid]["equilibrated"]:
            chosen = pairs + [(b, a) for a, b in pairs]
        elif flux[rid] > 0:
            chosen = pairs
        else:
            chosen = [(b, a) for a, b in pairs]''',
          '        chosen = pairs')],
    ),
}

# Crude fakes that do no chemistry at all.
STANDALONE = {
    "cheat-empty-network": (
        "Writes a schema-shaped file with nothing in it.",
        '''python3 - <<'PY'
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
''',
    ),
    "cheat-every-candidate": (
        "Declares every candidate to be part of the network, with zero fluxes and empty "
        "atom maps: the laziest way to guarantee the true reactions are all present.",
        '''python3 - <<'PY'
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
''',
    ),
    "cheat-search-environment-for-answer": (
        "Looks for the answer anywhere in the agent's environment: a stray ground-truth "
        "file, a cached result, a comment. Nothing there should let it write the network.",
        '''found=$(grep -rl -e "net_flux" -e "ground_truth" -e "atom_map" /app /usr/lib/python3* 2>/dev/null | head -5 || true)
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
''',
    ),
}


def emit():
    out = TASK / "cheat"
    out.mkdir(exist_ok=True)
    for name, (why, edits) in MUTATIONS.items():
        body = SOLVER
        for find, replace in edits:
            assert find in body, f"{name}: anchor not found -> {find[:60]!r}"
            body = body.replace(find, replace, 1)
        assert body != SOLVER, name
        script = ("#!/bin/bash\n"
                  + "".join(f"# {line}\n" for line in wrap(why))
                  + "set -euo pipefail\n\n"
                  "cat > /app/cheat_solver.py <<'CHEAT_EOF'\n"
                  + body +
                  "CHEAT_EOF\n\n"
                  "python3 /app/cheat_solver.py\n")
        path = out / f"{name}.sh"
        path.write_text(script)
        path.chmod(0o755)

    for name, (why, body) in STANDALONE.items():
        script = ("#!/bin/bash\n"
                  + "".join(f"# {line}\n" for line in wrap(why))
                  + "set -euo pipefail\n\n" + body)
        path = out / f"{name}.sh"
        path.write_text(script)
        path.chmod(0o755)
    print(f"wrote {len(MUTATIONS) + len(STANDALONE)} cheat scripts")


def wrap(text, width=86):
    words, line, lines = text.split(), "", []
    for word in words:
        if len(line) + len(word) + 1 > width:
            lines.append(line)
            line = word
        else:
            line = f"{line} {word}".strip()
    if line:
        lines.append(line)
    return lines


if __name__ == "__main__":
    emit()
