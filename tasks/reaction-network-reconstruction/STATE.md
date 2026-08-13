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

## Hardening, after a self-attack found the isomer stage was a lookup

An Opus-class self-attack (the calibration instrument `docs/DIFFICULTY.md` asks for) read
the bundle cold and reported that its first plan was the correct plan. Three leaks, all of
them from the "What not to ship" list, and one of them fatal on its own.

1. **The isomer stage was a sorted-list comparison, not chemistry.** `species.json` and
   `candidate_intermediates.json` stored `hydrogens` as an explicit per-atom integer, and
   `spectroscopy.json` published `attached_hydrogens_per_signal`. Identifying the channel
   was then

       sorted(a["hydrogens"] for a in atoms if element == "C") == sorted(profile)

   with no valence reasoning anywhere. Leak-audit class 3 (self-labelling data) and class 5
   (a free join key: the H counts were the join). Confirmed by running it - it eliminates
   P1 and leaves P2/P3 tied, so the remaining step was a coin flip a retry resolves.
2. **`candidate_intermediates.json` carried `"note": "one of these accounts for the
   unassigned C5H7O4- channel"`, and `spectroscopy.json` carried `"target": "unassigned
   C5H7O4- channel"`.** Prose in JSON clothing, telling the agent what the files are for -
   leak-audit class 2, and the documentation ban in Stage 3 by intent if not by extension.
3. **The instruction pre-announced every trap.** It stated the rule precedence outright
   ("balance, then the isomer identity, then the class gate, then the tracers, then the
   flux"), said the reactor "is not at that temperature" (handing over the Gibbs-Helmholtz
   correction), and gave the *count* of equilibrated-but-flux-carrying reactions ("two of
   ours"). Prong A2 is "describe the concept, never name it"; this named all of them.

What changed:

1. **Hydrogens are no longer stored.** Both structure files ship heavy atoms and bonds
   only. A hydrogen count is now derived: neutral valence minus the bond orders an atom
   carries, then the ion's charge spent on an oxygen. Verified recoverable for 86/86 atoms.
   The one arbitrary case is `S04` (bicarbonate, two equivalent singly-bonded oxygens where
   the proton could sit on either); swapping it produces a byte-identical answer, so it is
   implementation choice and nothing grades it. That check matters - grading an arbitrary
   labelling is exactly what failed the run audit on `rollout-cache-coherence`.
2. **`spectroscopy.json` now publishes `methyl_correlations`**, the shift region of the
   carbon each methyl hangs off (carbonyl / oxygenated / aliphatic), replacing the H-count
   profile. This separates all three isomers where the old profile tied P2 and P3, and it
   is a real HMBC-style reading: it requires deriving bond orders and symmetry-distinct
   carbons first. P2 alone shows one methyl on a carbonyl and one on an oxygenated carbon;
   P3 has both methyls on the same oxygenated carbon.
3. **The `note` and `target` strings are deleted.**
4. **`validate_output.py` no longer counts hydrogens.** It checks heavy atoms and charge
   only. Leaving the H derivation in the shipped validator would have handed the agent an
   oracle for the balance stage - it could brute-force coefficients until the validator
   stopped complaining, which is class 4 (an artifact that is a function of the correct
   trajectory). Its message now says "heavy atoms and charge do not balance" so it does not
   claim more than it checks.
5. **The instruction states the observations, not the method.** The precedence sentence is
   gone (the rules are still in order, and it says to take the first that catches); the
   temperature paragraph names the tabulated temperature and the conditions file without
   announcing that they differ; the "two of ours" count is gone. Because the H shortcut is
   gone, the brief now has to say what the spectroscopy contains - stated as observations
   and the definition of the three regions, which is the contract an analytical chemist
   would be handed, not the plan.

Not changed: the balance algebra, the atom-map convention, the tracer veto, the flux
solve, the precedence itself, the ground truth, and the verifier contract. `ground_truth.json`
is untouched and the reference solution still reproduces it field for field, which is the
point - the chemistry was always sound, and only the ways to skip it were removed.

### Verification of the hardening

| Check | Result |
|---|---|
| Reference solver == `tests/ground_truth.json` after all changes | exact match, all six keys |
| `validate_output.py` on the correct output | `structurally valid` |
| H counts recoverable from valence + charge | 86/86 atoms |
| `S04` proton placement affects the answer | no - byte-identical output when swapped |
| `hydrogens` anywhere in the agent tree | none |
| self-labelling strings in the agent tree | none |
| `tools/textcheck.py` vs `rollout-cache-coherence` | no findings |

## Easiness probe, run locally after the hardening: 3 of 3. Still too easy.

Three Opus-class agents were given the hardened bundle in isolated directories, no access to
`tests/`, `solution/` or anything outside their own copy. All three produced output identical
to `ground_truth.json` on all six keys. Under the pipeline's rule (fail at 2 or 3 of 3) this
is a rejection, and it says the leak fixes above were necessary but not sufficient.

The three reports agree on why, and none of it is the chemistry. **The task confirms its own
answer at every stage**, so an agent never has to commit to a reading - it guesses, checks
global consistency, and revises. Their own words:

- The dG treatment: "that produced zero equilibrated reactions, which contradicted the
  brief's insistence that equilibrated reactions exist and belong to the network. That was
  the signal to revise." The instruction asserts the equilibrated set is non-empty, so a
  wrong free-energy treatment announces itself.
- Two of the three independently: the corrected values "land on suspiciously round numbers
  (-29.004, -34.004, -21.999, -14.998), which is what convinced me the treatment was the
  intended one." The generator built the free energies backwards from round targets, so
  arriving at round numbers *is* the confirmation. Leak class 4, in the data itself.
- The hydrogen rule I introduced above: it "reproduced every stated formula except the two I
  flagged as conflicts, which is the self-check that told me the reading was right." With
  only 2 conflicts in 18 species, the derivation is validated for free by the data it runs on.
- The flux solve: "an exact, unique, over-determined fit is hard to get by accident" - the
  system closing at rank 10 with no free variables retroactively confirms every upstream
  exclusion, including the isomer. One probe noted that picking P1 or P3 makes the system
  fail to close, so even the stage I rebuilt is checkable downstream.
- `label_predictions`: "re-propagating feed enrichment reproduces every measured position in
  all three tracer runs" - a full end-to-end checksum of the finished answer.

So the structural diagnosis is not "a stage was a lookup" (that was the first audit, and it
was real). It is that the task is a constraint-satisfaction puzzle with a unique consistent
solution and **total feedback**, which is leak-audit item 6 - no per-axis confirmation before
commit - at global scale. Prong C is absent in practice: nothing fails late, because
everything fails immediately and visibly. Guess-check-revise is what frontier agents are
best at, so the real chemistry never becomes the bottleneck.

### What fixing it requires

This is a regeneration of the data and ground truth, not an edit, and it is the contributor's
call because it changes what the task is:

1. Break the roundness in the generated free energies, so landing on the right formula
   produces nothing recognisable.
2. Stop the flux system from being a global checksum - it currently closes only for the
   correct upstream exclusion set, which validates the whole chain at once.
3. Cut or blunt `label_predictions` as an end-to-end confirmation of the finished network.
4. Remove the existence assertions from the instruction (that equilibrated reactions exist,
   that the network is non-empty). Those are shape hints the agent tests against.
5. Raise the number of `formula_conflicts`, or otherwise stop 16 of 18 species silently
   validating the hydrogen derivation.

Until that is done the task should not be resubmitted: it will come back 7-8 of 8.

## Open questions and next steps

- The instruction is a draft written by the assistant. Per the authoring rules the
  contributor has to rewrite it in their own words before submission; the facts in it are
  checked against the environment and are correct.
- `task.toml` metadata prose (`difficulty_explanation`, `solution_explanation`,
  `verification_explanation`, `relevant_experience`) is also a draft and belongs to the
  contributor.
- Re-run `harbor run` oracle and nop, and `harbor check`, in an environment with Docker Hub
  access before packaging.
