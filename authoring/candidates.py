"""The full candidate list handed to the agent, and the reason each decoy is out.

`kind` is authoring bookkeeping only: it records which rule is expected to remove the
candidate, so the uniqueness check can assert that the rules really do that.
"""

from __future__ import annotations

# (candidate key, reactant species, product species, class, kind)
CANDIDATES = [
    # --- the nine reactions that are really running -------------------------------
    ("hydration", ["S02", "S09"], ["S05"], "carbonyl_hydration", "true"),
    ("tautomerisation", ["S01"], ["S13"], "tautomerisation", "true"),
    ("decarboxylation", ["S01", "S10"], ["S02", "S03"], "cofactor_decarboxylation", "true"),
    ("carboligation", ["S01", "S02"], ["P2"], "carboligation", "true"),
    ("acetolactate_decarboxylation", ["P2", "S10"], ["S06", "S03"], "cofactor_decarboxylation", "true"),
    ("hydride_transfer", ["S12", "S07"], ["S06", "S01"], "hydride_transfer", "true"),
    ("alkaline_cleavage", ["S01", "S15"], ["S08", "S14"], "base_cleavage", "true"),
    ("aldol_condensation", ["S02"], ["S16"], "aldol_addition", "true"),
    ("co2_hydration", ["S03", "S09"], ["S04", "S10"], "carbonyl_hydration", "true"),

    # --- same chemistry written on the wrong C5H7O4- isomer ------------------------
    ("carboligation_p1", ["S01", "S02"], ["P1"], "carboligation", "spectroscopy"),
    ("carboligation_p3", ["S01", "S02"], ["P3"], "carboligation", "spectroscopy"),
    ("decarb_p1", ["P1", "S10"], ["S06", "S03"], "cofactor_decarboxylation", "spectroscopy"),
    ("decarb_p3", ["P3", "S10"], ["S06", "S03"], "cofactor_decarboxylation", "spectroscopy"),

    # --- no positive integer balance exists ---------------------------------------
    ("acetate_decarboxylation", ["S08", "S10"], ["S02", "S03"], "cofactor_decarboxylation", "unbalanceable"),
    ("diol_carboxylation", ["S05", "S03"], ["S07", "S10"], "carbonyl_hydration", "unbalanceable"),
    ("formate_reduction", ["S14", "S12"], ["S03", "S06"], "hydride_transfer", "unbalanceable"),
    ("lactate_cleavage", ["S07", "S15"], ["S08", "S14", "S09"], "base_cleavage", "unbalanceable"),

    # --- the species lists admit more than one independent balance ------------------
    ("lumped_ketol_route", ["S01", "S02", "S10"], ["S06", "S03"], "carboligation", "ambiguous"),
    ("ketol_hydrolysis", ["S06", "S09"], ["S05", "S02"], "carbonyl_hydration", "ambiguous"),
    ("aldehyde_carbonate_oxidation", ["S02", "S15", "S03"], ["S08", "S14", "S10"], "base_cleavage", "ambiguous"),

    # --- balanced, but their class needs something the reactor does not have --------
    ("ketol_metal_oxidation", ["S05", "S12"], ["S06", "S08", "S10"], "metal_oxidation", "gated"),
    ("diol_carbonate_oxidation", ["S05", "S03"], ["S08", "S04", "S10"], "metal_oxidation", "gated"),
    ("photolytic_decarboxylation", ["S01", "S09"], ["S02", "S04"], "photolysis", "gated"),
    ("lactate_carbonate_photolysis", ["S07", "S03"], ["S01", "S04", "S10"], "photolysis", "gated"),

    # --- balanced and allowed, but it would label a carbon the tracer shows clean ---
    ("acyloin_condensation", ["S02"], ["S06"], "carboligation", "isotope"),

    # --- balanced and allowed, but they would carry label backwards into the feed ---
    ("oxidative_coupling", ["S01", "S02"], ["S12", "S14"], "hydride_transfer", "isotope"),
    ("lactate_coupling", ["S01", "S07"], ["S12", "S14"], "hydride_transfer", "isotope"),
    ("diol_coupling", ["S01", "S05"], ["S09", "S12", "S14"], "hydride_transfer", "isotope"),

    # --- balanced, allowed, tracer-clean, but the rate data give it no room ---------
    ("dione_cleavage", ["S12", "S15"], ["S08", "S02"], "base_cleavage", "flux"),
]

# Candidate id assignment: fixed, deliberately not grouped by kind.
ORDER = [
    "diol_carboxylation", "carboligation", "diol_coupling", "co2_hydration",
    "acetate_decarboxylation", "hydride_transfer", "carboligation_p1", "hydration",
    "lumped_ketol_route", "acetolactate_decarboxylation", "ketol_metal_oxidation",
    "decarboxylation", "oxidative_coupling", "decarb_p3", "alkaline_cleavage",
    "formate_reduction", "aldol_condensation", "ketol_hydrolysis", "decarb_p1",
    "photolytic_decarboxylation", "tautomerisation", "dione_cleavage",
    "lactate_cleavage", "carboligation_p3", "lactate_coupling",
    "aldehyde_carbonate_oxidation", "diol_carbonate_oxidation",
    "lactate_carbonate_photolysis", "acyloin_condensation",
]

CANDIDATE_ID = {key: f"R{i:02d}" for i, key in enumerate(ORDER, start=1)}

# Which condition key each reaction class needs. Shipped to the agent as data.
CLASS_REQUIREMENT = {
    "carbonyl_hydration": None,
    "tautomerisation": None,
    "aldol_addition": None,
    "cofactor_decarboxylation": "thiamine_analogue_cofactor",
    "carboligation": "thiamine_analogue_cofactor",
    "hydride_transfer": None,
    "base_cleavage": "hydroxide_activity",
    "metal_oxidation": "transition_metal_oxidant",
    "photolysis": "actinic_irradiation",
}

CONDITIONS = {
    "temperature_k": 318.15,
    "ph": 7.2,
    "thiamine_analogue_cofactor": True,
    "hydroxide_activity": True,
    "transition_metal_oxidant": False,
    "actinic_irradiation": False,
}
