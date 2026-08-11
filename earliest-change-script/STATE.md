# Task state

Working memory for this task. Assume the next session starts with no memory of this one.

## Current stage

`Stage 7 - Pre-flight and packaging`, second pass. The task was built, packaged and sent
through the difficulty probe once. It came back **solved 3 of 3 by Opus 5** and was rejected as
too easy. This pass is the re-attack: the correctness half is untouched, the cost half is
rebuilt.

## Why the first version was too easy

The probe transcript is the evidence and it is worth reading before changing anything. The
agent got the tie-break rule right almost immediately - the instruction states it and works two
examples, so the correctness half was never the wall - and then spent the session on
performance. It never found the intended frontier at all. It built the other thing entirely:
whole rows of the LCS table packed into single integers, restricted to a diagonal band, with
checkpointed row storage for the backward walk. That is a legitimate solution and it passed.

The measurement that explains it: the eight timed pairs in v1 were 100k-200k lines with an edit
distance of only **200-700**, and the reference answered them in **0.04-0.20 seconds against a
4 second budget** - a 20-40x margin. Anything within an order of magnitude of the right idea
fitted. The band the agent needed was ~2*D = a few hundred bits wide, which is nothing.

The failed repair, recorded so nobody tries it again: **squeezing the clock does not work.** A
banded row engine and the frontier are within ~2x of each other across the whole feasible
parameter space (measured, both directions), because both are dominated by the same O(n) Python
walk when D is small. Any budget tight enough to exclude one endangers the reference itself,
which is the unverifiable-side rejection.

## What changed in this pass

The timed block is now **twelve pairs in two families that cost the opposite way round**, and
each family is hopeless for the technique that answers the other. This is `docs/DIFFICULTY.md`
Prong A3 (requirements no single known technique satisfies) and Prong C3 (a resource gate the
straightforward implementation fails even when its answers are right).

| Family | Shape | Frontier `O(D^2)` | Row engine `O(n*m/64)` |
|---|---|---|---|
| long, 6 cases | 400k-1M lines a side, D a few hundred | **0.22-0.57s** | 252s |
| crossed, 6 cases | 40k-58k lines a side, D 15k-67k | 94s to ~1850s | **1.0-1.9s** |

Budget: 6 seconds a case. Both single-engine implementations were run through the whole
verifier as submissions: each **passes all 53258 correctness cases and scores zero on the timed
block**, one dying on the crossed family and the other on the long one. That is the Prong C
shape - a plan that is semantically perfect, and fatal, and only shown to be fatal late.

Supporting changes:

- Enumerated block 2500 -> **40804** pairs (shapes now include `ab` strings to length 5 and
  `abc` strings to length 4). Fixed block 46 -> **54**, the new ones aimed at the shared-head
  trap.
- Medium block: a quarter of the 400 pairs are now crossed rather than near-identical, so a
  frontier-only implementation starts bleeding time before the timed block.
- Reference and solution are now a **hybrid**: run the frontier, abandon it if the pair needs
  more moves than the row engine would have cost from the start. The crossover is computed from
  measured constants rather than guessed.
- New test `test_both_engines_of_the_fast_model_are_checked`. The grading-side reference now has
  two engines, the short cases only ever exercise one of them, and the other is what produces
  the expected answers for the crossed pairs. It is forced on and checked against the
  definitional model. Without this the crossed cases would be graded against untested code.
- Two pre-existing preflight errors fixed: em dashes in `instruction.md`, and `test.sh` not
  containing the literal `/logs/verifier/reward.txt`.

## Calibration

Reference worst case over 8 seeds: **32% of budget** (1.93s of 6s), so a grading box twice as
slow as the authoring box still lands at 64%. Deliberately not tighter: the discrimination here
is categorical (15-300x), so budget slack costs nothing and protects against the
never-solved rejection, which `docs/DIFFICULTY.md` warns is the bigger risk when aiming low.

Estimate: **2 of 8**, down from the 8 of 8 the first version measured. The honest uncertainty is
that a strong agent may build a banded row engine plus a full-width fallback and cover both
families with one mechanism. That path is open, it is real work, and it is not the plan anyone
starts with - v1's probe agent built the band and would still have died on the crossed family,
where the band is the width of the file and the row storage it needs is measured in gigabytes.

## Validation status

Run locally without the container (no docker daemon in the authoring session), harness and
pytest driven directly:

- reference solution: **12 tests pass** on seeds 424242, 99887, 20260811
- nop: 7 failed
- `cheat/forge_the_result.py`: 7 failed (and this ran as root locally, with *more* power than
  the sandbox account it faces in the real image)
- `cheat/delegate_to_difflib.py`: 6 failed; wrong on 11019 of 12000 random and 26271 of 40804
  enumerated pairs
- `table_only`, `frontier_only`, `row_engine_only` ablations: all score zero

**Open item for the next session:** re-run under `harbor run -e docker` for the oracle and nop
agents, which needs a working docker daemon. Nothing about the container, the account
separation or the reward wiring was changed in this pass, so the risk is low, but it has not
been re-run end to end in the real image.

**Open item for the contributor:** `relevant_experience` in `task.toml` is unchanged from v1 and
is yours. The performance half of the story it tells is now a two-regime story - worth a
sentence in your own words about the regenerated-file case, since that is what the crossed
family is drawn from.
