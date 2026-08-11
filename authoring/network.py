"""Ground-truth reaction network: stoichiometry, heavy-atom maps, kinetics, thermodynamics.

Every true reaction is written here in its CANONICAL direction (the direction it will be
written in the candidate file the agent receives). `flux` is the true net flux along that
canonical direction, so a negative flux means the reaction actually runs backwards
relative to how the candidate file states it.

Atom maps are given as {("<sid>", <instance>, "<atom>"): ("<sid>", <instance>, "<atom>")}
from a reactant-side atom to a product-side atom. Instances are 1-based and only matter
where a stoichiometric coefficient exceeds 1.
"""

from __future__ import annotations

# name -> dict(reactants, products, cls, dg298, dh, flux, amap)
TRUE = {
    # Reversible carbonyl hydration. Sits at equilibrium and still carries net flux,
    # because downstream chemistry drains the diol.
    "hydration": {
        "reactants": {"S02": 1, "S09": 1},
        "products": {"S05": 1},
        "cls": "carbonyl_hydration",
        "dg298": -1.20,
        "dh": -22.0,
        "flux": 4.0,
        "amap": {
            ("S02", 1, "C1"): ("S05", 1, "C1"),
            ("S02", 1, "C2"): ("S05", 1, "C2"),
            ("S02", 1, "O1"): ("S05", 1, "O1"),
            ("S09", 1, "O1"): ("S05", 1, "O2"),
        },
    },
    # Keto-enol tautomerisation. True net flux is zero: the pair is equilibrated and
    # nothing downstream consumes the enol.
    "tautomerisation": {
        "reactants": {"S01": 1},
        "products": {"S13": 1},
        "cls": "tautomerisation",
        "dg298": 12.60,
        "dh": 5.0,
        "flux": 0.0,
        "amap": {
            ("S01", 1, "C1"): ("S13", 1, "C1"),
            ("S01", 1, "C2"): ("S13", 1, "C2"),
            ("S01", 1, "O1"): ("S13", 1, "O1"),
            ("S01", 1, "C3"): ("S13", 1, "C3"),
            ("S01", 1, "O2"): ("S13", 1, "O2"),
            ("S01", 1, "O3"): ("S13", 1, "O3"),
        },
    },
    # Cofactor-dependent decarboxylation. The carboxylate carbon leaves as CO2; the
    # methyl carbon is retained in the aldehyde, which is what the 13C feed reports on.
    "decarboxylation": {
        "reactants": {"S01": 1, "S10": 1},
        "products": {"S02": 1, "S03": 1},
        "cls": "cofactor_decarboxylation",
        "dg298": -19.40,
        "dh": 30.0,
        "flux": 20.0,
        "amap": {
            ("S01", 1, "C1"): ("S02", 1, "C1"),
            ("S01", 1, "C2"): ("S02", 1, "C2"),
            ("S01", 1, "O1"): ("S02", 1, "O1"),
            ("S01", 1, "C3"): ("S03", 1, "C1"),
            ("S01", 1, "O2"): ("S03", 1, "O1"),
            ("S01", 1, "O3"): ("S03", 1, "O2"),
        },
    },
    # Carboligation: the aldehyde is the two-carbon donor and becomes the acetyl arm.
    "carboligation": {
        "reactants": {"S01": 1, "S02": 1},
        "products": {"P2": 1},
        "cls": "carboligation",
        "dg298": -8.30,
        "dh": -41.0,
        "flux": 6.0,
        "amap": {
            ("S02", 1, "C1"): ("P2", 1, "C1"),
            ("S02", 1, "C2"): ("P2", 1, "C2"),
            ("S02", 1, "O1"): ("P2", 1, "O1"),
            ("S01", 1, "C1"): ("P2", 1, "C4"),
            ("S01", 1, "C2"): ("P2", 1, "C3"),
            ("S01", 1, "O1"): ("P2", 1, "O2"),
            ("S01", 1, "C3"): ("P2", 1, "C5"),
            ("S01", 1, "O2"): ("P2", 1, "O3"),
            ("S01", 1, "O3"): ("P2", 1, "O4"),
        },
    },
    # Second decarboxylation, of the tertiary alcohol acid. Again the carboxylate leaves.
    "acetolactate_decarboxylation": {
        "reactants": {"P2": 1, "S10": 1},
        "products": {"S06": 1, "S03": 1},
        "cls": "cofactor_decarboxylation",
        "dg298": -26.10,
        "dh": 18.0,
        "flux": 6.0,
        "amap": {
            ("P2", 1, "C1"): ("S06", 1, "C1"),
            ("P2", 1, "C2"): ("S06", 1, "C2"),
            ("P2", 1, "O1"): ("S06", 1, "O1"),
            ("P2", 1, "C3"): ("S06", 1, "C3"),
            ("P2", 1, "O2"): ("S06", 1, "O2"),
            ("P2", 1, "C4"): ("S06", 1, "C4"),
            ("P2", 1, "C5"): ("S03", 1, "C1"),
            ("P2", 1, "O3"): ("S03", 1, "O1"),
            ("P2", 1, "O4"): ("S03", 1, "O2"),
        },
    },
    # Hydride transfer. Written in the candidate file the other way round, so the true
    # net flux along the written direction is negative.
    "hydride_transfer": {
        "reactants": {"S12": 1, "S07": 1},
        "products": {"S06": 1, "S01": 1},
        "cls": "hydride_transfer",
        "dg298": 6.90,
        "dh": 3.0,
        "flux": -2.5,
        "amap": {
            ("S12", 1, "C1"): ("S06", 1, "C1"),
            ("S12", 1, "C2"): ("S06", 1, "C2"),
            ("S12", 1, "O1"): ("S06", 1, "O1"),
            ("S12", 1, "C3"): ("S06", 1, "C3"),
            ("S12", 1, "O2"): ("S06", 1, "O2"),
            ("S12", 1, "C4"): ("S06", 1, "C4"),
            ("S07", 1, "C1"): ("S01", 1, "C1"),
            ("S07", 1, "C2"): ("S01", 1, "C2"),
            ("S07", 1, "O1"): ("S01", 1, "O1"),
            ("S07", 1, "C3"): ("S01", 1, "C3"),
            ("S07", 1, "O2"): ("S01", 1, "O2"),
            ("S07", 1, "O3"): ("S01", 1, "O3"),
        },
    },
    # Base-mediated oxidative cleavage between the two carbonyl carbons. The incoming
    # hydroxide oxygen ends up in the acetate, which the 18O experiment reports on.
    "alkaline_cleavage": {
        "reactants": {"S01": 1, "S15": 1},
        "products": {"S08": 1, "S14": 1},
        "cls": "base_cleavage",
        "dg298": -31.50,
        "dh": -12.0,
        "flux": 3.0,
        "amap": {
            ("S01", 1, "C1"): ("S08", 1, "C1"),
            ("S01", 1, "C2"): ("S08", 1, "C2"),
            ("S01", 1, "O1"): ("S08", 1, "O1"),
            ("S15", 1, "O1"): ("S08", 1, "O2"),
            ("S01", 1, "C3"): ("S14", 1, "C1"),
            ("S01", 1, "O2"): ("S14", 1, "O1"),
            ("S01", 1, "O3"): ("S14", 1, "O2"),
        },
    },
    # Aldol self-condensation of the aldehyde. The only true reaction with a coefficient
    # above one, so its map is instance-qualified: one molecule supplies the enol carbon,
    # the other the carbonyl that is attacked.
    "aldol_condensation": {
        "reactants": {"S02": 2},
        "products": {"S16": 1},
        "cls": "aldol_addition",
        "dg298": -14.80,
        "dh": -52.0,
        "flux": 1.5,
        "amap": {
            ("S02", 1, "C1"): ("S16", 1, "C3"),
            ("S02", 1, "C2"): ("S16", 1, "C4"),
            ("S02", 1, "O1"): ("S16", 1, "O2"),
            ("S02", 2, "C1"): ("S16", 1, "C1"),
            ("S02", 2, "C2"): ("S16", 1, "C2"),
            ("S02", 2, "O1"): ("S16", 1, "O1"),
        },
    },
    # CO2 hydration. Equilibrated and net-productive.
    "co2_hydration": {
        "reactants": {"S03": 1, "S09": 1},
        "products": {"S04": 1, "S10": 1},
        "cls": "carbonyl_hydration",
        "dg298": 2.10,
        "dh": -9.0,
        "flux": 5.0,
        "amap": {
            ("S03", 1, "C1"): ("S04", 1, "C1"),
            ("S03", 1, "O1"): ("S04", 1, "O1"),
            ("S03", 1, "O2"): ("S04", 1, "O2"),
            ("S09", 1, "O1"): ("S04", 1, "O3"),
        },
    },
}
