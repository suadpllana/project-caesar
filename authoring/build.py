"""Build the task data files and the verifier ground truth, then prove the answer unique.

Run:  python3 build.py <repo-root>

Everything the agent receives is derived here from the ground-truth network, so the data
cannot drift out of agreement with the answer.
"""

from __future__ import annotations

import json
import math
import sys
from fractions import Fraction
from pathlib import Path

import candidates as cd
import network as nw
import species as sp
import symmetry as sy
from atommap import canonical_map
from balancer import balance, _nullspace

R_GAS = 8.314462618e-3          # kJ / (mol K)
T_REF = 298.15                  # K, the temperature the tabulated values refer to
T_RUN = cd.CONDITIONS["temperature_k"]
EQUILIBRIUM_BAND = 0.5          # kJ / mol

MEASURED = ["S01", "S02", "S03", "S04", "S05", "S06", "S07", "S08",
            "P2", "S12", "S13", "S14", "S16"]

# Steady-state concentrations in mol/L. Water is the solvent and carries unit activity.
CONC = {
    "S01": 2.00e-3, "S02": 4.00e-4, "S03": 1.20e-3, "S04": 3.00e-3,
    "S05": 1.60e-4, "S06": 2.50e-4, "S07": 5.00e-4, "S08": 8.00e-4,
    "P1": 2.00e-6, "P2": 2.00e-6, "P3": 2.00e-6,
    "S10": 6.31e-8, "S12": 1.00e-4, "S13": 1.40e-7, "S14": 6.00e-4,
    "S15": 3.20e-6, "S16": 1.10e-4,
}
SOLVENT = "S09"

# Target Delta_r G at reactor conditions (kJ/mol) and the reaction enthalpy used for the
# temperature correction. The targets encode the intended verdicts:
#   |dG| <= 0.5  the pair is equilibrated, its flux sign is not fixed by thermodynamics
#   dG < -0.5    net flux may only be positive along the written direction
#   dG > +0.5    net flux may only be negative along the written direction
# Candidates that reach the rate stage: (Delta_r G wanted in the reactor, wanted Delta_r S
# in J/mol/K). The reaction enthalpy is then derived, so the tabulated numbers the agent
# receives carry a plausible entropy instead of whatever the algebra happened to need.
#   |dG| <= 0.5  the pair is equilibrated, its flux sign is not fixed by thermodynamics
#   dG < -0.5    net flux may only be positive along the written direction
#   dG > +0.5    net flux may only be negative along the written direction
FLUX_STAGE_TARGET = {
    "hydration": (-0.20, -76.0),
    "tautomerisation": (0.10, -64.0),
    "decarboxylation": (-34.00, 145.0),
    "carboligation": (-12.50, -82.0),
    "acetolactate_decarboxylation": (-29.00, 152.0),
    "hydride_transfer": (3.80, 17.0),
    "alkaline_cleavage": (-22.00, 67.0),
    "aldol_condensation": (-15.00, -62.0),
    "co2_hydration": (-0.35, -157.0),
    # the sign pattern below is what makes the flux solution a single point
    "dione_cleavage": (-0.85, 123.0),
    "oxidative_coupling": (4.20, -129.0),
    "lactate_coupling": (5.60, -96.0),
    "diol_coupling": (3.10, -102.0),
}

# Everything removed before the thermodynamic stage. No rule consumes these numbers, so
# they are published as tabulated estimates: (Delta_r G at 298.15 K, Delta_r H).
TABULATED = {
    "carboligation_p1": (-13.47, -38.12),
    "carboligation_p3": (-11.09, -34.86),
    "decarb_p1": (-58.23, -12.44),
    "decarb_p3": (-56.78, -11.05),
    "acyloin_condensation": (-32.31, -47.29),
    "acetate_decarboxylation": (18.44, 41.13),
    "diol_carboxylation": (9.72, -8.36),
    "formate_reduction": (14.18, 12.07),
    "lactate_cleavage": (7.31, -4.62),
    "lumped_ketol_route": (-38.57, -23.41),
    "ketol_hydrolysis": (11.52, 9.28),
    "aldehyde_carbonate_oxidation": (-6.84, -19.17),
    "ketol_metal_oxidation": (17.76, -22.35),
    "diol_carbonate_oxidation": (44.19, 6.42),
    "photolytic_decarboxylation": (-9.23, 26.08),
    "lactate_carbonate_photolysis": (31.44, -9.31),
}


# --------------------------------------------------------------------- stoichiometry


def coefficients(key):
    for k, r, p, _c, _kind in cd.CANDIDATES:
        if k == key:
            return balance(r, p)
    raise KeyError(key)


def stoich_vector(key) -> dict[str, int]:
    st, rc, pc = coefficients(key)
    assert st == "unique", key
    v: dict[str, int] = {}
    for s, c in rc.items():
        v[s] = v.get(s, 0) - c
    for s, c in pc.items():
        v[s] = v.get(s, 0) + c
    return v


def net_rates() -> dict[str, Fraction]:
    rates = {s: Fraction(0) for s in MEASURED}
    for key, spec in nw.TRUE.items():
        v = Fraction(str(spec["flux"]))
        for s, c in stoich_vector(key).items():
            if s in rates:
                rates[s] += c * v
    return rates


# --------------------------------------------------------------------- thermodynamics


def ln_q(key) -> float:
    """ln of the mass-action ratio, solvent excluded (unit activity)."""
    st, rc, pc = coefficients(key)
    assert st == "unique", key
    total = 0.0
    for s, c in pc.items():
        if s != SOLVENT:
            total += c * math.log(CONC[s])
    for s, c in rc.items():
        if s != SOLVENT:
            total -= c * math.log(CONC[s])
    return total


def dg_standard_at(dg_ref: float, dh: float, temperature: float) -> float:
    """Gibbs-Helmholtz, holding the reaction enthalpy and entropy constant."""
    return dh - temperature * (dh - dg_ref) / T_REF


def solve_dg_ref(key, target: float, dh: float) -> float:
    """Tabulated Delta_r G at 298.15 K that lands Delta_r G on `target` in the reactor."""
    rt = R_GAS * T_RUN
    # target = dh - T_RUN*(dh - dg_ref)/T_REF + rt*lnQ  ->  linear in dg_ref
    lhs = target - rt * ln_q(key) - dh
    return dh + lhs * T_REF / T_RUN


def enthalpy_for(key, target: float, ds_j: float) -> float:
    """Reaction enthalpy that lands both Delta_r G in the reactor and Delta_r S on target."""
    k = target - R_GAS * T_RUN * ln_q(key)
    return k + ds_j * T_REF / (T_REF / T_RUN * 1000.0)


def dg_reaction(key, dg_ref: float, dh: float, temperature: float, use_correction: bool) -> float:
    std = dg_standard_at(dg_ref, dh, temperature) if use_correction else dg_ref
    return std + R_GAS * temperature * ln_q(key)


# --------------------------------------------------------------------- isotope labels

# (experiment id, description, initial enrichment)
EXPERIMENTS = [
    ("E1", "carbon-13 on the methyl carbon of the fed 2-oxo acid", {"S01": {"C1"}}),
    ("E2", "carbon-13 on the carbonyl carbon of co-fed aldehyde", {"S02": {"C2"}}),
    ("E3", "oxygen-18 in the solvent and in the hydroxide it equilibrates with",
     {"S09": {"O1"}, "S15": {"O1"}}),
]


def network_reactions() -> list[str]:
    """Keys of the reactions that are actually in the network."""
    return list(nw.TRUE.keys())


def parsed_map(key):
    """Canonical map as (species, instance, atom) pairs."""
    st, rc, pc = coefficients(key)
    _score, pairs = canonical_map(rc, pc)
    out = []
    for src, dst in pairs:
        def split(x):
            sid, rest = x.split("#", 1)
            inst, atom = rest.split(":", 1)
            return (sid, int(inst), atom)
        out.append((split(src), split(dst)))
    return out


def propagate(initial: dict[str, set[str]], extra_keys: tuple[str, ...] = ()) -> dict[str, set[str]]:
    """Fixed-point spread of enrichment along the network's real flow directions.

    A reaction that is equilibrated carries label in both directions whatever its net
    flux; every other reaction carries it only the way its net flux runs.
    """
    labels = {s: set(v) for s, v in initial.items()}
    edges: list[tuple[str, str, str, str]] = []   # (from_species, from_atom, to_species, to_atom)
    for key in list(nw.TRUE.keys()) + list(extra_keys):
        spec = nw.TRUE[key] if key in nw.TRUE else EXTRA_REACTIONS[key]
        pairs = parsed_map(key)
        forward = [(a[0], a[2], b[0], b[2]) for a, b in pairs]
        backward = [(b[0], b[2], a[0], a[2]) for a, b in pairs]
        equilibrated = abs(spec["dg_run"]) <= EQUILIBRIUM_BAND
        if equilibrated:
            edges += forward + backward
        elif spec["flux"] > 0:
            edges += forward
        elif spec["flux"] < 0:
            edges += backward

    changed = True
    while changed:
        changed = False
        for fs, fa, ts, ta in edges:
            if fa in labels.get(fs, set()) and ta not in labels.get(ts, set()):
                labels.setdefault(ts, set()).add(ta)
                changed = True
    return labels


# The acyloin route is not in the network; it is carried here only so the builder can
# show that including it would predict enrichment the experiment does not see.
EXTRA_REACTIONS = {
    "acyloin_condensation": {"reactants": {"S02": 2}, "products": {"S06": 1},
                             "flux": 1.0, "dg_run": -11.86},
}


# --------------------------------------------------------------------- uniqueness


def check_flux_uniqueness(flux_keys, sign_of):
    """The true flux vector must be the ONLY point satisfying rates + sign constraints.

    The feasible set is convex, so it is enough to show no nonzero direction stays
    feasible: any move must keep the measured rates and must not push a candidate that
    sits at zero flux into the sign its Delta_r G forbids.
    """
    rows = [[Fraction(stoich_vector(k).get(s, 0)) for k in flux_keys] for s in MEASURED]
    basis = _nullspace(rows, len(flux_keys))
    if not basis:
        return True, "stoichiometric matrix has full column rank"

    idx = {k: i for i, k in enumerate(flux_keys)}
    tight = [k for k in flux_keys
             if Fraction(str(nw.TRUE[k]["flux"] if k in nw.TRUE else 0)) == 0
             and sign_of[k] != "unconstrained"]
    # A direction is a1*b1 + ... ; feasibility needs sign_of[k]-compatible movement on
    # every candidate pinned at zero. Enumerate the sign pattern exhaustively over the
    # small basis by checking the cone {x : M x >= 0} is trivial, where each row is
    # oriented so that "feasible" means >= 0.
    rows_cone = []
    for k in tight:
        coeffs = [vec[idx[k]] for vec in basis]
        if sign_of[k] == "forward":       # v_k must stay >= 0, so direction >= 0
            rows_cone.append(coeffs)
        else:                             # reverse-only: v_k must stay <= 0
            rows_cone.append([-c for c in coeffs])
    trivial = cone_is_trivial(rows_cone, len(basis))
    return trivial, f"nullspace dim {len(basis)}, cone trivial={trivial}"


def cone_is_trivial(rows, n):
    """True when {x in R^n : rows . x >= 0} contains only the origin.

    Solved exactly by vertex enumeration on the small systems this task produces: the
    cone is trivial exactly when the only solution of the homogeneous system is zero,
    which we test by looking for a nonzero solution among the candidate directions
    generated by all n-1 subsets of the constraint rows plus the coordinate directions.
    """
    from itertools import combinations
    if not rows:
        return n == 0
    cands = []
    for a in range(n):
        e = [Fraction(0)] * n
        e[a] = Fraction(1)
        cands.append(e)
        cands.append([-x for x in e])
    for combo in combinations(range(len(rows)), min(n - 1, len(rows))):
        sub = [rows[i] for i in combo]
        for vec in _nullspace(sub, n) if sub else []:
            cands.append(vec)
            cands.append([-x for x in vec])
    for vec in cands:
        if all(v == 0 for v in vec):
            continue
        if all(sum(r[i] * vec[i] for i in range(n)) >= 0 for r in rows):
            return False
    return True


# --------------------------------------------------------------------- emit


def species_record(sid, declared_formula=None):
    """Ships id, formula, charge and the connection table - never the compound name.

    A name would let the network be recognised instead of derived, which is exactly the
    inference the spectroscopy and tracer data are there to force.
    """
    _name, atoms, bonds, charge = sp.SPECIES[sid]
    return {
        "id": sid,
        "formula": declared_formula or sp.formula(sid),
        "charge": charge,
        "atoms": [{"id": a, "element": e, "hydrogens": h} for a, e, h in atoms],
        "bonds": [{"a": x, "b": y, "order": o} for x, y, o in bonds],
    }


def main(root: Path):
    # 1. thermodynamics: pick tabulated values that realise the intended verdicts
    thermo = {}
    for key, (dg_ref, dh) in TABULATED.items():
        thermo[key] = {"dg_ref": dg_ref, "dh": dh}
    for key, (target, ds_j) in FLUX_STAGE_TARGET.items():
        dh = round(enthalpy_for(key, target, ds_j), 2)
        dg_ref = round(solve_dg_ref(key, target, dh), 2)
        thermo[key] = {"dg_ref": dg_ref, "dh": dh}
        run = dg_reaction(key, dg_ref, dh, T_RUN, use_correction=True)
        assert abs(run - target) < 0.02, (key, run, target)
        ds = (dh - dg_ref) / T_REF * 1000
        assert abs(ds - ds_j) < 1.0, (key, ds, ds_j)

    for key, spec in nw.TRUE.items():
        spec["dg_run"] = FLUX_STAGE_TARGET[key][0]

    # 2. flux uniqueness over everything that survives to the rate stage
    flux_keys = [k for k, _r, _p, _c, kind in cd.CANDIDATES if kind in ("true", "flux")]
    sign_of = {}
    for k in flux_keys:
        dg = FLUX_STAGE_TARGET[k][0]
        sign_of[k] = ("unconstrained" if abs(dg) <= EQUILIBRIUM_BAND
                      else "forward" if dg < 0 else "reverse")
    unique, detail = check_flux_uniqueness(flux_keys, sign_of)
    print(f"flux solution unique: {unique}  ({detail})")
    assert unique, "the rate data do not pin a single flux vector"

    # 3. isotope predictions, and proof that the acyloin route contradicts them
    labels = {}
    for eid, _desc, initial in EXPERIMENTS:
        labels[eid] = propagate(initial)
    with_acyloin = {eid: propagate(init, ("acyloin_condensation",))
                    for eid, _d, init in EXPERIMENTS}
    contradiction = [(eid, s, sorted(with_acyloin[eid].get(s, set()) - labels[eid].get(s, set())))
                     for eid, _d, _i in EXPERIMENTS
                     for s in sorted(set(with_acyloin[eid]) | set(labels[eid]))
                     if with_acyloin[eid].get(s, set()) - labels[eid].get(s, set())]
    print("acyloin route would add enrichment at:", contradiction)
    assert contradiction, "the acyloin decoy is not excluded by the tracer data"

    print("\nnet rates:")
    rates = net_rates()
    for s in MEASURED:
        print(f"   {s}: {float(rates[s]):+7.3f}")
    truth = build_ground_truth(thermo, rates, labels)
    write_data(root, thermo, rates, labels, truth)
    print("\nintermediates:", truth["intermediates"])
    print("network reactions:", [r["id"] for r in truth["reactions"]])
    print("wrote data files and ground truth")
    return thermo, rates, labels




# --------------------------------------------------------------------- output schema

# Species whose tabulated formula string was entered wrongly in the inventory. The
# structures are right; the strings are not, and the network has to say so.
DECLARED_FORMULA_OVERRIDE = {"S06": "C4H8O3", "S13": "C3H4O3-"}

INVENTORY = ["S01", "S02", "S03", "S04", "S05", "S06", "S07", "S08", "S09",
             "S10", "S12", "S13", "S14", "S15", "S16"]
INTERMEDIATE_POOL = ["P1", "P2", "P3"]
FEED = ["S01", "S09", "S10", "S15"]


def atom_ref(sid, instance, atom):
    return f"{sid}#{instance}:{atom}"


def direction_of(v):
    return "forward" if v > 1e-9 else "reverse" if v < -1e-9 else "balanced"


def build_ground_truth(thermo, rates, labels):
    fluxes = {k: nw.TRUE[k]["flux"] for k in nw.TRUE}
    reactions = []
    for key, spec in nw.TRUE.items():
        rid = cd.CANDIDATE_ID[key]
        st, rc, pc = coefficients(key)
        dg = dg_reaction(key, thermo[key]["dg_ref"], thermo[key]["dh"], T_RUN, True)
        reactions.append({
            "id": rid,
            "coefficients": {"reactants": rc, "products": pc},
            "delta_r_g": round(dg, 2),
            "equilibrium": abs(dg) <= EQUILIBRIUM_BAND,
            "direction": direction_of(spec["flux"]),
            "net_flux": round(spec["flux"], 3),
            "atom_map": canonical_map(rc, pc)[1],
        })
    reactions.sort(key=lambda r: r["id"])

    reason_of = {"unbalanceable": "unbalanceable", "ambiguous": "ambiguous_balance",
                 "spectroscopy": "intermediate_mismatch", "gated": "condition_gated",
                 "isotope": "isotope_inconsistent", "flux": "no_net_flux"}
    excluded = sorted(
        ({"id": cd.CANDIDATE_ID[k], "reason": reason_of[kind]}
         for k, _r, _p, _c, kind in cd.CANDIDATES if kind != "true"),
        key=lambda e: e["id"])

    produced, consumed = set(), set()
    for key, spec in nw.TRUE.items():
        v = spec["flux"]
        if v == 0:
            continue
        for s, c in stoich_vector(key).items():
            (produced if c * v > 0 else consumed).add(s)
    intermediates = sorted((produced & consumed) - set(FEED))

    return {
        "intermediate_id": "P2",
        "formula_conflicts": sorted(DECLARED_FORMULA_OVERRIDE),
        "reactions": reactions,
        "excluded": excluded,
        "intermediates": intermediates,
        "label_predictions": {
            eid: {s: sorted(v) for s, v in sorted(labels[eid].items()) if v}
            for eid, _d, _i in EXPERIMENTS
        },
    }


def write_data(root: Path, thermo, rates, labels, truth):
    data = root / "tasks" / "reaction-network-reconstruction" / "environment" / "app_src" / "data"
    data.mkdir(parents=True, exist_ok=True)

    def dump(name, obj):
        (data / name).write_text(json.dumps(obj, indent=2, sort_keys=False) + "\n")

    dump("species.json", {
        "units": {"concentration": "mol/L"},
        "species": [dict(species_record(s, DECLARED_FORMULA_OVERRIDE.get(s)),
                         concentration=CONC.get(s))
                    for s in INVENTORY],
    })

    dump("candidate_intermediates.json", {
        "note": "one of these accounts for the unassigned C5H7O4- channel",
        "candidates": [dict(species_record(s), concentration=CONC[s]) for s in INTERMEDIATE_POOL],
    })

    dump("candidate_reactions.json", {
        "units": {"delta_r_g_ref": "kJ/mol", "delta_r_h": "kJ/mol"},
        "reference_temperature_k": T_REF,
        "reactions": sorted(
            [{"id": cd.CANDIDATE_ID[k], "reactants": r, "products": p, "class": c,
              "delta_r_g_ref": round(thermo[k]["dg_ref"], 2),
              "delta_r_h": round(thermo[k]["dh"], 2)}
             for k, r, p, c, _kind in cd.CANDIDATES],
            key=lambda x: x["id"]),
    })

    dump("reaction_classes.json", {
        "classes": [{"class": c, "requires": cd.CLASS_REQUIREMENT[c]}
                    for c in sorted(cd.CLASS_REQUIREMENT)],
    })

    dump("conditions.json", {
        "temperature_k": T_RUN,
        "ph": cd.CONDITIONS["ph"],
        "solvent_species": SOLVENT,
        "feed_species": FEED,
        "available": {k: v for k, v in cd.CONDITIONS.items()
                      if isinstance(v, bool)},
    })

    dump("net_rates.json", {
        "units": {"net_rate": "umol/(L s)"},
        "channels": [
            {"channel": f"CH{i:02d}",
             "species": (s if s != "P2" else None),
             "formula": ("C5H7O4-" if s == "P2" else None),
             "net_rate": round(float(rates[s]), 3)}
            for i, s in enumerate(MEASURED, start=1)
        ],
    })

    dump("tracer_experiments.json", {
        "experiments": [
            {"id": eid, "description": desc,
             "feed_enrichment": {s: sorted(v) for s, v in initial.items()},
             "observed_enriched_positions": {
                 s: sorted(labels[eid].get(s, set()))
                 for s in INVENTORY if s in labels[eid] or s in MEASURED}}
            for eid, desc, initial in EXPERIMENTS
        ],
    })

    dump("spectroscopy.json", {
        "target": "unassigned C5H7O4- channel",
        "carbon_signal_count": 5,
        "attached_hydrogens_per_signal": [0, 0, 0, 3, 3],
    })

    tests = root / "tasks" / "reaction-network-reconstruction" / "tests"
    tests.mkdir(parents=True, exist_ok=True)
    (tests / "ground_truth.json").write_text(json.dumps(truth, indent=2) + "\n")


if __name__ == "__main__":
    main(Path(sys.argv[1] if len(sys.argv) > 1 else "."))
