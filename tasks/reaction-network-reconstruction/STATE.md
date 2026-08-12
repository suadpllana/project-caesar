# Task state

## Current stage

`Stage 7 - Pre-flight and packaging`. Everything is built and validated except the two
gates that need a container registry (`harbor run` oracle/nop in Docker) and `harbor check`,
neither of which can run in the authoring environment used here. See "Validation status".

## Assistant's assigned role

Senior reaction-kinetics engineer for small aqueous organic systems: steady-state flow
reactors, LC-MS and NMR channel assignment, 13C and 18O tracer design, and the
stoichiometric bookkeeping that turns a pile of analytical channels into a mechanism.

## Source repository (repo-based tasks only)

- Repo URL: none - idea-based task.

## Task summary

The agent is dropped into a flow-reactor dataset: fifteen species with drawn structures,
twenty-nine candidate reactions written without coefficients, reactor conditions,
steady-state concentrations, measured net production rates, tabulated free energies, three
tracer runs, and three C5H7O4- isomers only one of which is the unassigned channel. It must
reconstruct the running network and write `/app/network.json`: balanced coefficients, free
energy under reactor conditions, equilibrium flag, direction, net flux and full heavy-atom
map for each reaction in the network; the first rule that removed each of the twenty
candidates that are out; the identified isomer; the species whose typed formula contradicts
its structure; the inferred intermediates; and the enrichment its network predicts for all
three tracer runs.

## Why it is hard

Six coupled inferences, each with a plausible shortcut that is specifically wrong, and all
six must be right at once.

- Expert time estimate: 8 hours
- Why a frontier agent cannot one-shot the plan: the correct plan is not "balance the
  candidates and pick the ones that fit the rates". It is a five-stage classification with a
  fixed precedence, where the stages interact: the thermodynamic stage decides which
  directions the tracer stage is allowed to test, the tracer stage decides which candidates
  reach the flux stage, and the flux stage is only uniquely solvable once the tracer stage
  has removed the three coupling candidates. None of those couplings is visible from the
  instruction alone; they only appear once the data has been read and the stages attempted.
- Tactics making that true: prong A poisons the default plan, prong B withholds it, prong C
  makes the wrong plan fail late. Each one, concretely:
  - Prong A: the tabulated free energies are quoted at 298.15 K and the reactor is at
    318.15 K. Taking tabulated numbers at face value is the memorised default and it is
    wrong. Balancing from a formula string rather than a connection table is the other
    default, and two formula strings are mistyped. "In the network" defaulting to "carries
    flux" is a third, and one equilibrated reaction carries exactly zero.
  - Prong B: the load-bearing facts are spread across eight data files. The reference
    temperature is in `candidate_reactions.json`, the reactor temperature in
    `conditions.json`; the class gate needs `reaction_classes.json` crossed with
    `conditions.json`; the isomer needs `spectroscopy.json` crossed with
    `candidate_intermediates.json`; the unassigned rate channel in `net_rates.json` carries
    a formula and no species id, so it cannot be used until the isomer is settled.
  - Prong C: the temperature error is silent. Every earlier stage still succeeds with it,
    and it surfaces only at the end, as two wrong equilibrium flags and a tenth reaction in
    the network. A wrong isomer is equally late-breaking, since it invalidates the atom maps
    and every tracer prediction downstream.
- Assistant's attack on the plan: my first plan was "parse the data, balance every
  candidate, filter by class, solve the rate system by least squares, report what survives".
  That plan is wrong in four places: it balances from formulas, it never corrects the free
  energies, it has no place for the tracer veto (so its rate system is underdetermined and
  it silently picks one of infinitely many flux vectors), and it drops the zero-flux
  equilibrated reaction. Executing it produces a confident, internally consistent, wrong
  network.
- Estimated solves out of 8: 1 to 2.
- Expert path, step by step:
  1. Derive element counts and charge from the connection tables; note the two species whose
     typed formula disagrees.
  2. Balance each candidate as an exact rational nullspace over the element and charge rows;
     classify as uniquely balanced, unbalanceable, or admitting two independent balances.
     Two candidates balance only at 5:6 to 6:3:4 and 4:4 to 5:2:7.
  3. Compute topological equivalence classes of the carbons of each C5H7O4- isomer by colour
     refinement; match count and attached-proton multiset against the spectroscopy record.
     Count alone leaves two standing; the proton pattern settles it.
  4. Gate classes against the reactor conditions.
  5. Correct the tabulated free energies from 298.15 K to 318.15 K holding enthalpy and
     entropy constant, add RT ln Q from the measured concentrations with solvent at unit
     activity, and classify each within or outside the 0.5 kJ/mol equilibrium band.
  6. Compute each surviving candidate's canonical atom map by maximising conserved bonds
     over element-preserving pairings, breaking ties lexicographically. No reaction exceeds
     nine heavy atoms a side, so brute force is fine.
  7. Push the measured enrichment across each candidate's map in its permitted directions;
     four candidates put label on positions the runs report clean.
  8. Solve the remaining stoichiometric matrix against the measured net rates in exact
     rational arithmetic. Full column rank, so the flux vector is unique; one candidate
     comes out at exactly zero flux without being equilibrated.
  9. Propagate label to a fixed point along the directions the fluxes imply, both ways
     across equilibrated steps.
- Originality check: the components are each textbook (atom mapping, flux balance, isotope
  tracing, Gibbs-Helmholtz, colour refinement). No public write-up combines them over an
  authored dataset with this rule precedence, and the data was generated here.

## Verifier contract - FROZEN

- Artifact: `/app/network.json`.
- Checked: network membership exactly; per reaction the coefficients, `delta_r_g`
  (+-0.05 kJ/mol), `equilibrium`, `direction`, `net_flux` (+-0.005) and the full atom map;
  every excluded candidate's reason under the stated precedence; `intermediate_id`;
  `formula_conflicts`; `intermediates`; `label_predictions` for all three runs; plus
  degenerate-output guards.
- Tolerances: as above. Everything else exact.
- Ground truth: `tests/ground_truth.json`, baked into the verifier image only. Derived twice
  independently - forward from the generating network in `authoring/`, and by running
  `solution/reconstruct.py` on the shipped data files - and the two agree field for field.

## Decisions and their reasons

- Candidates are given without coefficients. This forces exact linear algebra and lets two
  candidates carry non-obvious ratios, and it makes "admits two independent balances" a real
  category rather than a curiosity.
- The atom-map convention (maximum conserved bonds, lexicographic tie-break) is stated in
  the instruction because it is a convention choice, not something derivable. Without the
  tie-break the gem-diol oxygens and the CO2 oxygens make the answer genuinely ambiguous.
- The exclusion reasons are graded, not just the exclusions. A right reaction set with wrong
  reasons means the pipeline was not run; several candidates would be caught by more than
  one rule.
- The acyloin candidate and the three coupling candidates are removed at the tracer stage,
  not the flux stage. This is forced: with any of them present the flux system is rank
  deficient, so the tracer veto has to come first for the answer to be unique.
- Isomer ids were reassigned late. In the first build the true isomer was `P1`, and a solver
  that used only the carbon signal count and then took the first or alphabetically first hit
  landed on it by luck; the `cheat-signal-count-only` probe scored 1. The true isomer is now
  `P2`, so both of those shortcuts land on the wrong one. Do not reorder them back.
- `/app/validate_output.py` ships in the agent environment on purpose. It checks schema and
  internal consistency only, never chemistry, so it removes formatting noise without giving
  away any part of the answer.

## Validation status

| Check | Status | Notes |
|---|---|---|
| Agent image builds | not run | no container registry reachable from the authoring environment |
| No answer leaked into agent image | pass | `environment/` grepped for ground-truth material; the only executable shipped is the schema checker |
| `harbor run -a oracle` = 1 | pass (emulated) | `tools/run_local.py oracle` at the real absolute paths; 86/86 verifier assertions |
| `harbor run -a nop` = 0 | pass (emulated) | `tools/run_local.py nop` |
| Cheats all score 0 | pass | 12 cheats via `tools/run_local.py --all` |
| `preflight.py` | pass | no errors, no warnings |
| `harbor check` rubric | not run | needs a model API key |

## Open questions and next steps

- The instruction is a draft written by the assistant. Per the authoring rules the
  contributor has to rewrite it in their own words before submission; the facts in it are
  checked against the environment and are correct.
- `task.toml` metadata prose (`difficulty_explanation`, `solution_explanation`,
  `verification_explanation`, `relevant_experience`) is also a draft and belongs to the
  contributor.
- Re-run `harbor run` oracle and nop, and `harbor check`, in an environment with Docker Hub
  access before packaging.
