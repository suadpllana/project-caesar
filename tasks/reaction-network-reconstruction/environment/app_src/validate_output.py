import json
import sys
from pathlib import Path

DATA = Path("/app/data")
REASONS = {"unbalanceable", "ambiguous_balance", "intermediate_mismatch",
           "condition_gated", "isotope_inconsistent", "no_net_flux"}
DIRECTIONS = {"forward", "reverse", "balanced"}
SECTIONS = {"intermediate_id": str, "formula_conflicts": list, "reactions": list,
            "excluded": list, "intermediates": list, "label_predictions": dict}
FIELDS = {"id", "coefficients", "delta_r_g", "equilibrium", "direction",
          "net_flux", "atom_map"}


def load(name):
    return json.loads((DATA / name).read_text())


def structures():
    rec = {}
    for entry in load("species.json")["species"]:
        rec[entry["id"]] = entry
    for entry in load("candidate_intermediates.json")["candidates"]:
        rec[entry["id"]] = entry
    return rec


def counts(rec, sid):
    out = {}
    for atom in rec[sid]["atoms"]:
        out[atom["element"]] = out.get(atom["element"], 0) + 1
        if atom["hydrogens"]:
            out["H"] = out.get("H", 0) + atom["hydrogens"]
    if not rec[sid]["atoms"] and rec[sid]["charge"] == 1:
        out["H"] = out.get("H", 0) + 1
    return out


def heavy_refs(rec, coefs):
    out = []
    for sid in sorted(coefs):
        for inst in range(1, coefs[sid] + 1):
            for atom in rec[sid]["atoms"]:
                out.append(f"{sid}#{inst}:{atom['id']}")
    return out


def main(path):
    problems = []
    try:
        data = json.loads(Path(path).read_text())
    except (OSError, json.JSONDecodeError) as exc:
        print(f"cannot read {path}: {exc}")
        return 1
    if not isinstance(data, dict):
        print("top level must be a JSON object")
        return 1

    for key, kind in SECTIONS.items():
        if key not in data:
            problems.append(f"missing section: {key}")
        elif not isinstance(data[key], kind):
            problems.append(f"{key} must be a {kind.__name__}")
    if problems:
        print("\n".join(problems))
        return 1

    rec = structures()
    known = {entry["id"] for entry in load("candidate_reactions.json")["reactions"]}
    seen = set()

    for entry in data["reactions"]:
        rid = entry.get("id", "?")
        missing = FIELDS - set(entry)
        if missing:
            problems.append(f"{rid}: missing fields {sorted(missing)}")
            continue
        if rid not in known:
            problems.append(f"{rid}: not a candidate id")
        if rid in seen:
            problems.append(f"{rid}: reported twice")
        seen.add(rid)
        if entry["direction"] not in DIRECTIONS:
            problems.append(f"{rid}: direction must be one of {sorted(DIRECTIONS)}")
        coefs = entry["coefficients"]
        if set(coefs) != {"reactants", "products"}:
            problems.append(f"{rid}: coefficients need 'reactants' and 'products'")
            continue
        delta = {}
        for side, sign in (("reactants", -1), ("products", 1)):
            for sid, n in coefs[side].items():
                if sid not in rec:
                    problems.append(f"{rid}: unknown species {sid}")
                    continue
                if not isinstance(n, int) or n < 1:
                    problems.append(f"{rid}: coefficient for {sid} must be a positive integer")
                    continue
                for el, k in counts(rec, sid).items():
                    delta[el] = delta.get(el, 0) + sign * n * k
                delta["charge"] = delta.get("charge", 0) + sign * n * rec[sid]["charge"]
        off = {k: v for k, v in delta.items() if v}
        if off:
            problems.append(f"{rid}: does not balance, off by {off}")
        want = sorted(heavy_refs(rec, coefs["reactants"]))
        made = sorted(heavy_refs(rec, coefs["products"]))
        pairs = entry["atom_map"]
        if not all(isinstance(p, (list, tuple)) and len(p) == 2 for p in pairs):
            problems.append(f"{rid}: atom_map must be a list of two-element pairs")
            continue
        if sorted(p[0] for p in pairs) != want:
            problems.append(f"{rid}: atom_map does not cover every reactant heavy atom once")
        if sorted(p[1] for p in pairs) != made:
            problems.append(f"{rid}: atom_map does not cover every product heavy atom once")

    for entry in data["excluded"]:
        rid = entry.get("id", "?")
        if rid not in known:
            problems.append(f"{rid}: excluded id is not a candidate")
        if entry.get("reason") not in REASONS:
            problems.append(f"{rid}: reason must be one of {sorted(REASONS)}")
        if rid in seen:
            problems.append(f"{rid}: both in the network and excluded")

    if len(seen) + len(data["excluded"]) != len(known):
        problems.append(f"every candidate must appear exactly once: "
                        f"{len(seen)} + {len(data['excluded'])} != {len(known)}")

    for eid, block in data["label_predictions"].items():
        for sid, positions in block.items():
            if sid not in rec:
                problems.append(f"{eid}: unknown species {sid}")
                continue
            valid = {atom["id"] for atom in rec[sid]["atoms"]}
            for pos in positions:
                if pos not in valid:
                    problems.append(f"{eid}/{sid}: {pos} is not an atom of {sid}")

    if problems:
        print("\n".join(problems))
        return 1
    print("structurally valid")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1] if len(sys.argv) > 1 else "/app/network.json"))
