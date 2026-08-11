"""Verifier for the reaction-network reconstruction.

The agent writes /app/network.json. Ground truth lives beside this file in
ground_truth.json and is baked into the verifier image only.

The assertions are grouped by the piece of chemistry each one is defending:

  1. the file is a well-formed network at all
  2. the bookkeeping annotation (typed formulas that disagree with the structures)
  3. which C5H7O4- isomer the unassigned channel is
  4. the exact membership of the network
  5. per-reaction stoichiometry, free energy, equilibrium flag, direction and flux
  6. atom maps, which is where a guessed connectivity dies
  7. why every rejected candidate was rejected - the reason, not just the rejection
  8. inferred intermediates
  9. tracer predictions, which only come out right if maps AND directions are right
 10. degenerate-output guards

A network that is right about the reaction list but wrong about any of the rest is not
a reconstruction, so every group is required.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

OUTPUT = Path("/app/network.json")
TRUTH = json.loads((Path(__file__).with_name("ground_truth.json")).read_text())

# The free energies are recomputed by the agent from the published tabulated values, so
# a small numerical spread is expected; the flux solve is exact rational arithmetic in
# the reference, so its tolerance is tighter than the reported precision.
DG_TOLERANCE = 0.05          # kJ/mol
FLUX_TOLERANCE = 0.005       # umol/(L s)

REASONS = {"unbalanceable", "ambiguous_balance", "intermediate_mismatch",
           "condition_gated", "isotope_inconsistent", "no_net_flux"}


@pytest.fixture(scope="module")
def result():
    """Parse the agent's output once; a missing or unparseable file fails everything."""
    assert OUTPUT.is_file(), f"{OUTPUT} was not produced"
    try:
        data = json.loads(OUTPUT.read_text())
    except json.JSONDecodeError as exc:
        pytest.fail(f"{OUTPUT} is not valid JSON: {exc}")
    assert isinstance(data, dict), "the top level of network.json must be a JSON object"
    return data


def reactions_by_id(data):
    return {r["id"]: r for r in data.get("reactions", [])}


# ------------------------------------------------------------------ 1. shape


def test_top_level_keys_present(result):
    """Every section of the deliverable exists, with the right container type."""
    expected = {
        "intermediate_id": str,
        "formula_conflicts": list,
        "reactions": list,
        "excluded": list,
        "intermediates": list,
        "label_predictions": dict,
    }
    for key, kind in expected.items():
        assert key in result, f"network.json is missing the '{key}' section"
        assert isinstance(result[key], kind), \
            f"'{key}' must be a {kind.__name__}, got {type(result[key]).__name__}"


def test_reaction_records_are_complete(result):
    """Each reported reaction carries all the fields the network is scored on."""
    fields = {"id", "coefficients", "delta_r_g", "equilibrium", "direction",
              "net_flux", "atom_map"}
    for entry in result["reactions"]:
        missing = fields - set(entry)
        assert not missing, f"reaction {entry.get('id', '?')} is missing fields: {sorted(missing)}"
        coefs = entry["coefficients"]
        assert set(coefs) == {"reactants", "products"}, \
            f"{entry['id']}: coefficients must have exactly 'reactants' and 'products'"


# ------------------------------------------------------------------ 2. bookkeeping


def test_formula_conflicts_reported(result):
    """The species whose typed formula contradicts its own structure, and only those.

    Reporting extra species here means the agent's formula derivation is wrong;
    reporting none means it trusted the typed strings, which mis-balances three of the
    reactions that are actually running.
    """
    assert sorted(result["formula_conflicts"]) == TRUTH["formula_conflicts"], (
        "formula_conflicts must list exactly the species whose declared formula "
        f"disagrees with the structure; expected {TRUTH['formula_conflicts']}, "
        f"got {sorted(result['formula_conflicts'])}")


# ------------------------------------------------------------------ 3. the intermediate


def test_intermediate_identified(result):
    """The unassigned C5H7O4- channel is one specific isomer.

    Signal count alone leaves two isomers standing; the attached-proton pattern is what
    settles it.
    """
    assert result["intermediate_id"] == TRUTH["intermediate_id"], (
        f"the unassigned C5H7O4- channel is {TRUTH['intermediate_id']}, "
        f"not {result['intermediate_id']}")


# ------------------------------------------------------------------ 4. membership


def test_network_membership_is_exact(result):
    """Exactly the reactions that are running, no more and no fewer.

    The two traps here are dropping the equilibrated pair that carries no net flux, and
    keeping the cleavage whose free energy only clears the equilibrium band once the
    tabulated values are corrected to the reactor temperature.
    """
    got = sorted(reactions_by_id(result))
    want = sorted(r["id"] for r in TRUTH["reactions"])
    assert got == want, (
        f"network membership is wrong: missing {sorted(set(want) - set(got))}, "
        f"unexpected {sorted(set(got) - set(want))}")


# ------------------------------------------------------------------ 5. per reaction


@pytest.mark.parametrize("expected", TRUTH["reactions"], ids=[r["id"] for r in TRUTH["reactions"]])
def test_reaction_stoichiometry(result, expected):
    """Balanced coefficients, derived from the structures rather than the typed formulas."""
    got = reactions_by_id(result).get(expected["id"])
    assert got is not None, f"{expected['id']} is missing from the network"
    assert got["coefficients"] == expected["coefficients"], (
        f"{expected['id']}: coefficients {got['coefficients']} do not balance the "
        f"reaction; expected {expected['coefficients']}")


@pytest.mark.parametrize("expected", TRUTH["reactions"], ids=[r["id"] for r in TRUTH["reactions"]])
def test_reaction_free_energy(result, expected):
    """Delta_r G at reactor conditions, which needs the temperature correction.

    Using the tabulated 298.15 K value directly moves several of these by more than the
    tolerance and flips two equilibrium verdicts.
    """
    got = reactions_by_id(result).get(expected["id"])
    assert got is not None, f"{expected['id']} is missing from the network"
    assert isinstance(got["delta_r_g"], (int, float)), \
        f"{expected['id']}: delta_r_g must be a number"
    assert abs(got["delta_r_g"] - expected["delta_r_g"]) <= DG_TOLERANCE, (
        f"{expected['id']}: delta_r_g is {got['delta_r_g']}, expected "
        f"{expected['delta_r_g']} +- {DG_TOLERANCE} kJ/mol")


@pytest.mark.parametrize("expected", TRUTH["reactions"], ids=[r["id"] for r in TRUTH["reactions"]])
def test_reaction_equilibrium_flag(result, expected):
    """Being equilibrated and carrying net flux are different things.

    Two of the equilibrated reactions carry substantial net flux, and one carries none;
    conflating the two collapses this flag.
    """
    got = reactions_by_id(result).get(expected["id"])
    assert got is not None, f"{expected['id']} is missing from the network"
    assert bool(got["equilibrium"]) == expected["equilibrium"], (
        f"{expected['id']}: equilibrium flag is {got['equilibrium']}, "
        f"expected {expected['equilibrium']}")


@pytest.mark.parametrize("expected", TRUTH["reactions"], ids=[r["id"] for r in TRUTH["reactions"]])
def test_reaction_direction(result, expected):
    """Direction of net flow relative to how the candidate was written.

    One reaction runs backwards relative to the candidate file and one carries no net
    flow at all, so a solver that reports the written direction everywhere fails here.
    """
    got = reactions_by_id(result).get(expected["id"])
    assert got is not None, f"{expected['id']} is missing from the network"
    assert got["direction"] == expected["direction"], (
        f"{expected['id']}: direction is {got['direction']}, expected {expected['direction']}")


@pytest.mark.parametrize("expected", TRUTH["reactions"], ids=[r["id"] for r in TRUTH["reactions"]])
def test_reaction_net_flux(result, expected):
    """The flux the measured net rates force on this step, signed by the written direction."""
    got = reactions_by_id(result).get(expected["id"])
    assert got is not None, f"{expected['id']} is missing from the network"
    assert isinstance(got["net_flux"], (int, float)), \
        f"{expected['id']}: net_flux must be a number"
    assert abs(got["net_flux"] - expected["net_flux"]) <= FLUX_TOLERANCE, (
        f"{expected['id']}: net_flux is {got['net_flux']}, expected "
        f"{expected['net_flux']} +- {FLUX_TOLERANCE}")


# ------------------------------------------------------------------ 6. atom maps


@pytest.mark.parametrize("expected", TRUTH["reactions"], ids=[r["id"] for r in TRUTH["reactions"]])
def test_atom_map(result, expected):
    """The canonical heavy-atom map: maximum bond conservation, lexicographic tie-break.

    This is where a network that is right about which reactions run can still be wrong
    about what actually happens in them - which carbon leaves as CO2, which oxygen the
    hydroxide contributes, which of two identical aldehyde molecules becomes which end
    of the aldol product.
    """
    got = reactions_by_id(result).get(expected["id"])
    assert got is not None, f"{expected['id']} is missing from the network"
    normalised = sorted([list(pair) for pair in got["atom_map"]])
    assert normalised == sorted(expected["atom_map"]), (
        f"{expected['id']}: atom map is wrong.\n"
        f"  missing pairs: {[p for p in expected['atom_map'] if p not in normalised]}\n"
        f"  spurious pairs: {[p for p in normalised if p not in expected['atom_map']]}")


# ------------------------------------------------------------------ 7. rejections


def test_every_rejected_candidate_is_accounted_for(result):
    """Each candidate that is not in the network appears once in `excluded`."""
    got = {e["id"] for e in result["excluded"]}
    want = {e["id"] for e in TRUTH["excluded"]}
    assert len(got) == len(result["excluded"]), "a candidate is listed twice in `excluded`"
    assert got == want, (
        f"`excluded` is wrong: missing {sorted(want - got)}, unexpected {sorted(got - want)}")


def test_rejection_reasons_use_the_agreed_vocabulary(result):
    """Reasons come from the fixed vocabulary, not free text."""
    for entry in result["excluded"]:
        assert entry.get("reason") in REASONS, (
            f"{entry.get('id', '?')}: reason {entry.get('reason')!r} is not one of "
            f"{sorted(REASONS)}")


@pytest.mark.parametrize("expected", TRUTH["excluded"], ids=[e["id"] for e in TRUTH["excluded"]])
def test_rejection_reason(result, expected):
    """The FIRST rule that removes the candidate, applied in the order the brief fixes.

    Getting the set of rejected candidates right while getting the reasons wrong means
    the pipeline was not actually run: several candidates would be caught by more than
    one rule, and only the earliest one is the answer.
    """
    got = {e["id"]: e.get("reason") for e in result["excluded"]}
    assert got.get(expected["id"]) == expected["reason"], (
        f"{expected['id']} was excluded for {got.get(expected['id'])!r}, "
        f"expected {expected['reason']!r}")


# ------------------------------------------------------------------ 8. intermediates


def test_inferred_intermediates(result):
    """Species the network both makes and eats, that the feed does not supply.

    Includes the C5H7O4- species that is never observed directly, and excludes the
    products that only accumulate.
    """
    assert sorted(result["intermediates"]) == TRUTH["intermediates"], (
        f"intermediates should be {TRUTH['intermediates']}, "
        f"got {sorted(result['intermediates'])}")


# ------------------------------------------------------------------ 9. tracer predictions


@pytest.mark.parametrize("experiment", sorted(TRUTH["label_predictions"]))
def test_label_predictions(result, experiment):
    """Enriched positions predicted by propagating the label through the network.

    Correct here requires all three of: the right reactions, the right atom maps, and
    the right flow direction for each of them - including that an equilibrated pair
    carries label both ways even when its net flux is zero.
    """
    got = result["label_predictions"].get(experiment)
    assert got is not None, f"no label predictions for experiment {experiment}"
    want = TRUTH["label_predictions"][experiment]
    normalised = {s: sorted(v) for s, v in got.items() if v}
    assert normalised == want, (
        f"{experiment}: predicted enrichment does not match.\n"
        f"  expected {want}\n"
        f"  got      {normalised}")


# ------------------------------------------------------------------ 10. degenerate output


def test_output_is_not_degenerate(result):
    """Guards against shapes that could pass a careless assertion without doing the work."""
    assert result["reactions"], "no reactions reported"
    fluxes = [r.get("net_flux", 0) for r in result["reactions"]]
    assert any(abs(v) > 0 for v in fluxes), "every reported net flux is zero"
    assert len({r["id"] for r in result["reactions"]}) == len(result["reactions"]), \
        "the same reaction is reported twice"
    overlap = {r["id"] for r in result["reactions"]} & {e["id"] for e in result["excluded"]}
    assert not overlap, f"these candidates are both in the network and excluded: {sorted(overlap)}"
    for entry in result["reactions"]:
        pairs = [tuple(p) for p in entry["atom_map"]]
        sources = [p[0] for p in pairs]
        targets = [p[1] for p in pairs]
        assert len(set(sources)) == len(sources), \
            f"{entry['id']}: an atom appears twice on the reactant side of the map"
        assert len(set(targets)) == len(targets), \
            f"{entry['id']}: two atoms map onto the same product atom"
