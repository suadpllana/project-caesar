#!/bin/bash
# Uses the tabulated 298.15 K free energies directly instead of correcting them to the
# reactor temperature. This is the single most likely shortcut: it leaves every other
# step intact and still gets the equilibrium flags and one membership decision wrong.
set -euo pipefail

cat > /app/cheat_solver.py <<'CHEAT_EOF'
"""Reference reconstruction of the partially observed network.

The work follows the order a kineticist would actually take it in: fix the bookkeeping
first (structures beat the typed formulas), settle what the unassigned intermediate is,
throw out chemistry the reactor cannot do, let the tracers veto connectivity, and only
then let the rate data decide how much flux each surviving step carries.
"""

from __future__ import annotations

import json
import math
from fractions import Fraction
from itertools import permutations
from math import gcd
from pathlib import Path

DATA = Path("/app/data")
OUT = Path("/app/network.json")

R_GAS = 8.314462618e-3          # kJ/(mol K)
EQUILIBRIUM_BAND = 0.5          # kJ/mol
FLUX_ZERO = 1e-9


def load(name):
    return json.loads((DATA / name).read_text())


# ------------------------------------------------------------------ structure basics


class Structures:
    """Every species the task knows about, keyed by id, with derived formulas."""

    def __init__(self):
        self.rec = {}
        for entry in load("species.json")["species"]:
            self.rec[entry["id"]] = entry
        for entry in load("candidate_intermediates.json")["candidates"]:
            self.rec[entry["id"]] = entry

    def counts(self, sid):
        """Element counts read off the structure, not off the typed formula."""
        rec = self.rec[sid]
        out = {}
        for atom in rec["atoms"]:
            out[atom["element"]] = out.get(atom["element"], 0) + 1
            if atom["hydrogens"]:
                out["H"] = out.get("H", 0) + atom["hydrogens"]
        if not rec["atoms"] and rec["charge"] == 1:
            out["H"] = out.get("H", 0) + 1          # the bare hydron
        return out

    def charge(self, sid):
        return self.rec[sid]["charge"]

    def derived_formula(self, sid):
        counts = self.counts(sid)
        text = ""
        for el in ("C", "H", "O"):
            n = counts.get(el, 0)
            text += el if n == 1 else (f"{el}{n}" if n > 1 else "")
        q = self.charge(sid)
        if q == 1:
            text += "+"
        elif q == -1:
            text += "-"
        elif q:
            text += f"{abs(q)}{'+' if q > 0 else '-'}"
        return text

    def atoms(self, sid):
        return [a["id"] for a in self.rec[sid]["atoms"]]

    def element(self, sid, aid):
        return next(a["element"] for a in self.rec[sid]["atoms"] if a["id"] == aid)

    def hydrogens(self, sid, aid):
        return next(a["hydrogens"] for a in self.rec[sid]["atoms"] if a["id"] == aid)

    def bonds(self, sid):
        return [(b["a"], b["b"], b["order"]) for b in self.rec[sid]["bonds"]]


# ------------------------------------------------------------------ exact linear algebra


def nullspace(rows, ncols):
    """Exact rational nullspace basis."""
    mat = [row[:] for row in rows]
    pivots, r = [], 0
    for c in range(ncols):
        piv = next((i for i in range(r, len(mat)) if mat[i][c] != 0), None)
        if piv is None:
            continue
        mat[r], mat[piv] = mat[piv], mat[r]
        lead = mat[r][c]
        mat[r] = [v / lead for v in mat[r]]
        for i in range(len(mat)):
            if i != r and mat[i][c] != 0:
                f = mat[i][c]
                mat[i] = [a - f * b for a, b in zip(mat[i], mat[r])]
        pivots.append(c)
        r += 1
        if r == len(mat):
            break
    basis = []
    for f in [c for c in range(ncols) if c not in pivots]:
        vec = [Fraction(0)] * ncols
        vec[f] = Fraction(1)
        for i, pc in enumerate(pivots):
            vec[pc] = -mat[i][f]
        basis.append(vec)
    return basis


def solve_exact(rows, rhs, ncols):
    """One exact solution of an overdetermined consistent system, or None."""
    mat = [row[:] + [rhs[i]] for i, row in enumerate(rows)]
    pivots, r = [], 0
    for c in range(ncols):
        piv = next((i for i in range(r, len(mat)) if mat[i][c] != 0), None)
        if piv is None:
            continue
        mat[r], mat[piv] = mat[piv], mat[r]
        lead = mat[r][c]
        mat[r] = [v / lead for v in mat[r]]
        for i in range(len(mat)):
            if i != r and mat[i][c] != 0:
                f = mat[i][c]
                mat[i] = [a - f * b for a, b in zip(mat[i], mat[r])]
        pivots.append(c)
        r += 1
        if r == len(mat):
            break
    for row in mat[len(pivots):]:
        if all(v == 0 for v in row[:ncols]) and row[ncols] != 0:
            return None                       # inconsistent
    sol = [Fraction(0)] * ncols
    for i, pc in enumerate(pivots):
        sol[pc] = mat[i][ncols]
    return sol


# ------------------------------------------------------------------ stage 1: balancing


def balance(struct, reactants, products):
    order = list(reactants) + list(products)
    signs = [1] * len(reactants) + [-1] * len(products)
    elements = sorted({el for s in order for el in struct.counts(s)})
    rows = [[Fraction(signs[i] * struct.counts(s).get(el, 0)) for i, s in enumerate(order)]
            for el in elements]
    rows.append([Fraction(signs[i] * struct.charge(s)) for i, s in enumerate(order)])

    basis = nullspace(rows, len(order))
    if not basis:
        return "none", {}, {}
    if len(basis) > 1:
        return "ambiguous", {}, {}
    vec = basis[0]
    if all(v <= 0 for v in vec):
        vec = [-v for v in vec]
    if any(v <= 0 for v in vec):
        return "none", {}, {}

    denom = 1
    for v in vec:
        denom = denom * v.denominator // gcd(denom, v.denominator)
    ints = [int(v * denom) for v in vec]
    g = 0
    for v in ints:
        g = gcd(g, v)
    ints = [v // g for v in ints]
    rc, pc = {}, {}
    for i, s in enumerate(order):
        (rc if i < len(reactants) else pc)[s] = ints[i]
    return "unique", rc, pc


# ------------------------------------------- stage 2: which isomer the C5 channel is


def equivalence_classes(struct, sid):
    """Colour refinement: atoms that no walk can tell apart share a class."""
    ids = struct.atoms(sid)
    adj = {a: [] for a in ids}
    for x, y, order in struct.bonds(sid):
        adj[x].append((y, order))
        adj[y].append((x, order))
    colour = {a: (struct.element(sid, a), struct.hydrogens(sid, a)) for a in ids}
    labels = {a: 0 for a in ids}
    for _ in range(len(ids) + 1):
        sig = {a: (colour[a], tuple(sorted((o, labels[n]) for n, o in adj[a]))) for a in ids}
        index = {s: i for i, s in enumerate(sorted(set(sig.values()), key=repr))}
        nxt = {a: index[sig[a]] for a in ids}
        if nxt == labels:
            break
        labels = nxt
    return labels


def carbon_signature(struct, sid):
    cls = equivalence_classes(struct, sid)
    per_class = {}
    for aid in struct.atoms(sid):
        if struct.element(sid, aid) == "C":
            per_class.setdefault(cls[aid], struct.hydrogens(sid, aid))
    return len(per_class), sorted(per_class.values())


def identify_intermediate(struct):
    spec = load("spectroscopy.json")
    want = (spec["carbon_signal_count"], sorted(spec["attached_hydrogens_per_signal"]))
    hits = [c["id"] for c in load("candidate_intermediates.json")["candidates"]
            if carbon_signature(struct, c["id"]) == want]
    if len(hits) != 1:
        raise SystemExit(f"spectroscopy does not single out one isomer: {hits}")
    return hits[0]


# ------------------------------------------------------------------ atom mapping


def side_atoms(struct, coefs):
    out = []
    for sid in sorted(coefs):
        for inst in range(1, coefs[sid] + 1):
            for aid in struct.atoms(sid):
                out.append(((sid, inst, aid), struct.element(sid, aid)))
    return out


def side_bonds(struct, coefs):
    bonds = set()
    for sid in sorted(coefs):
        for inst in range(1, coefs[sid] + 1):
            for x, y, order in struct.bonds(sid):
                a, b = (sid, inst, x), (sid, inst, y)
                bonds.add((min(a, b), max(a, b), order))
    return bonds


def ref(node):
    sid, inst, aid = node
    return f"{sid}#{inst}:{aid}"


def canonical_map(struct, reactants, products):
    """Keep as much bonding as possible; break ties lexicographically."""
    left, right = side_atoms(struct, reactants), side_atoms(struct, products)
    lb, rb = side_bonds(struct, reactants), side_bonds(struct, products)
    by_left, by_right = {}, {}
    for node, el in left:
        by_left.setdefault(el, []).append(node)
    for node, el in right:
        by_right.setdefault(el, []).append(node)

    elements = sorted(by_left)
    best = [-1, None]

    def walk(i, mapping):
        if i == len(elements):
            score = sum(1 for a, b, o in lb
                        if (min(mapping[a], mapping[b]), max(mapping[a], mapping[b]), o) in rb)
            pairs = sorted([ref(k), ref(v)] for k, v in mapping.items())
            if score > best[0] or (score == best[0] and pairs < best[1]):
                best[0], best[1] = score, pairs
            return
        el = elements[i]
        for perm in permutations(by_right[el]):
            nxt = dict(mapping)
            nxt.update(dict(zip(by_left[el], perm)))
            walk(i + 1, nxt)

    walk(0, {})
    return best[1]


def split_ref(text):
    sid, rest = text.split("#", 1)
    inst, atom = rest.split(":", 1)
    return sid, int(inst), atom


# ------------------------------------------------------------------ thermodynamics


def ln_q(struct, rc, pc, conc, solvent):
    total = 0.0
    for s, c in pc.items():
        if s != solvent:
            total += c * math.log(conc[s])
    for s, c in rc.items():
        if s != solvent:
            total -= c * math.log(conc[s])
    return total


def delta_r_g(dg_ref, dh, t_ref, t_run, lnq):
    return dg_ref + R_GAS * t_run * lnq


# ------------------------------------------------------------------ the pipeline


def main():
    struct = Structures()
    conditions = load("conditions.json")
    solvent = conditions["solvent_species"]
    t_run = conditions["temperature_k"]
    feed = set(conditions["feed_species"])
    available = conditions["available"]

    cand_file = load("candidate_reactions.json")
    t_ref = cand_file["reference_temperature_k"]
    requirement = {c["class"]: c["requires"] for c in load("reaction_classes.json")["classes"]}

    concentration = {sid: rec["concentration"] for sid, rec in struct.rec.items()
                     if rec.get("concentration") is not None}

    # --- consistency annotation: typed formulas that disagree with the structures ---
    conflicts = sorted(sid for sid, rec in struct.rec.items()
                       if rec["formula"] != struct.derived_formula(sid))

    # --- stage 2 needs deciding before any candidate that names an isomer is judged ---
    intermediate = identify_intermediate(struct)
    rejected_isomers = {c["id"] for c in load("candidate_intermediates.json")["candidates"]
                        if c["id"] != intermediate}

    # --- tracer observations -------------------------------------------------------
    experiments = load("tracer_experiments.json")["experiments"]
    observed = {e["id"]: {s: set(v) for s, v in e["observed_enriched_positions"].items()}
                for e in experiments}
    watched = {e["id"]: set(e["observed_enriched_positions"]) for e in experiments}
    feed_label = {e["id"]: {s: set(v) for s, v in e["feed_enrichment"].items()}
                  for e in experiments}

    verdict, info = {}, {}
    for entry in cand_file["reactions"]:
        rid = entry["id"]
        status, rc, pc = balance(struct, entry["reactants"], entry["products"])
        info[rid] = {"entry": entry, "rc": rc, "pc": pc}

        if status == "none":
            verdict[rid] = "unbalanceable"
            continue
        if status == "ambiguous":
            verdict[rid] = "ambiguous_balance"
            continue
        if rejected_isomers & (set(rc) | set(pc)):
            verdict[rid] = "intermediate_mismatch"
            continue
        need = requirement.get(entry["class"])
        if need is not None and not available.get(need, False):
            verdict[rid] = "condition_gated"
            continue

        lnq = ln_q(struct, rc, pc, concentration, solvent)
        dg = delta_r_g(entry["delta_r_g_ref"], entry["delta_r_h"], t_ref, t_run, lnq)
        equilibrated = abs(dg) <= EQUILIBRIUM_BAND
        info[rid].update(dg=dg, equilibrated=equilibrated,
                         amap=canonical_map(struct, rc, pc))

        # --- stage 4: does its own connectivity put label where none was seen? ------
        directions = ["f", "r"] if equilibrated else (["f"] if dg < 0 else ["r"])
        clash = False
        for eid in observed:
            for src, dst in info[rid]["amap"]:
                for d in directions:
                    a, b = (src, dst) if d == "f" else (dst, src)
                    asid, _ai, aatom = split_ref(a)
                    bsid, _bi, batom = split_ref(b)
                    if aatom in observed[eid].get(asid, set()) \
                            and bsid in watched[eid] \
                            and batom not in observed[eid].get(bsid, set()):
                        clash = True
        if clash:
            verdict[rid] = "isotope_inconsistent"

    # --- stage 5: let the rate data size every surviving step ----------------------
    survivors = [e["id"] for e in cand_file["reactions"] if e["id"] not in verdict]
    channels = load("net_rates.json")["channels"]
    measured, rhs = [], []
    for ch in channels:
        sid = ch["species"]
        if sid is None:
            matches = [s for s in (intermediate,) if struct.derived_formula(s) == ch["formula"]]
            if not matches:
                raise SystemExit(f"channel {ch['channel']} matches no identified species")
            sid = matches[0]
        measured.append(sid)
        rhs.append(Fraction(str(ch["net_rate"])))

    def column(rid):
        v = {}
        for s, c in info[rid]["rc"].items():
            v[s] = v.get(s, 0) - c
        for s, c in info[rid]["pc"].items():
            v[s] = v.get(s, 0) + c
        return v

    rows = [[Fraction(column(rid).get(s, 0)) for rid in survivors] for s in measured]
    solution = solve_exact(rows, rhs, len(survivors))
    if solution is None:
        raise SystemExit("no flux vector reproduces the measured rates")
    if nullspace(rows, len(survivors)):
        raise SystemExit("the measured rates do not pin a single flux vector")

    flux = {rid: float(solution[i]) for i, rid in enumerate(survivors)}
    for rid in survivors:
        if abs(flux[rid]) <= FLUX_ZERO and not info[rid]["equilibrated"]:
            verdict[rid] = "no_net_flux"
        elif (flux[rid] > FLUX_ZERO and not info[rid]["equilibrated"]
              and info[rid]["dg"] > EQUILIBRIUM_BAND) or \
             (flux[rid] < -FLUX_ZERO and not info[rid]["equilibrated"]
              and info[rid]["dg"] < -EQUILIBRIUM_BAND):
            raise SystemExit(f"{rid}: flux runs against its free energy")

    network = [rid for rid in survivors if rid not in verdict]

    # --- label propagation over the network, along the way each step really runs ----
    edges = []
    for rid in network:
        pairs = [(split_ref(a), split_ref(b)) for a, b in info[rid]["amap"]]
        if info[rid]["equilibrated"]:
            chosen = pairs + [(b, a) for a, b in pairs]
        elif flux[rid] > 0:
            chosen = pairs
        else:
            chosen = [(b, a) for a, b in pairs]
        edges += [(a[0], a[2], b[0], b[2]) for a, b in chosen]

    predictions = {}
    for eid in observed:
        labels = {s: set(v) for s, v in feed_label[eid].items()}
        changed = True
        while changed:
            changed = False
            for fs, fa, ts, ta in edges:
                if fa in labels.get(fs, set()) and ta not in labels.get(ts, set()):
                    labels.setdefault(ts, set()).add(ta)
                    changed = True
        predictions[eid] = {s: sorted(v) for s, v in sorted(labels.items()) if v}

    # --- species the network makes and then eats, and that the feed does not supply --
    produced, consumed = set(), set()
    for rid in network:
        if abs(flux[rid]) <= FLUX_ZERO:
            continue
        for s, c in column(rid).items():
            (produced if c * flux[rid] > 0 else consumed).add(s)
    intermediates = sorted((produced & consumed) - feed)

    reactions = []
    for rid in sorted(network):
        v = flux[rid]
        reactions.append({
            "id": rid,
            "coefficients": {"reactants": info[rid]["rc"], "products": info[rid]["pc"]},
            "delta_r_g": round(info[rid]["dg"], 2),
            "equilibrium": bool(info[rid]["equilibrated"]),
            "direction": "forward" if v > FLUX_ZERO else "reverse" if v < -FLUX_ZERO else "balanced",
            "net_flux": round(v, 3),
            "atom_map": info[rid]["amap"],
        })

    OUT.write_text(json.dumps({
        "intermediate_id": intermediate,
        "formula_conflicts": conflicts,
        "reactions": reactions,
        "excluded": sorted(({"id": rid, "reason": reason} for rid, reason in verdict.items()),
                           key=lambda e: e["id"]),
        "intermediates": intermediates,
        "label_predictions": predictions,
    }, indent=2) + "\n")


if __name__ == "__main__":
    main()
CHEAT_EOF

python3 /app/cheat_solver.py
