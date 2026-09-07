# Raise difficulty after an easiness failure

This is the mandatory recovery procedure for a task that does not pass the easiness probe. Read
this file completely before changing the task. The goal is not to make the task longer or more
obscure. The goal is to make a frontier agent's first reasonable plan fail for a fair, specified
reason while preserving a reliable expert path.

This procedure cannot make a stochastic probe infallible. It does make every retry evidence-based,
and it forbids declaring the recovery complete until a real easiness probe passes.

## Trigger

Use this procedure immediately when any of these happens:

- the easiness probe rejects the task;
- all sampled frontier agents solve it;
- a successful trajectory forms the correct complete plan before meaningful exploration;
- a new helper, example, field, document, or instruction edit exposes a load-bearing decision;
- the finished task's honest self-attack estimates eight solves out of eight.

Stop packaging or presenting the task as ready while this procedure is active. Keep the failed
probe evidence. Do not delete, rewrite, or summarize away a successful trajectory.

## Non-negotiable rules

1. Never weaken the verifier, widen a tolerance, delete an assertion, or accept partial credit to
   make a run pass.
2. Never create difficulty through ambiguity, missing requirements, artificial naming, random
   busywork, gratuitous repository size, or an arbitrarily short timeout.
3. More hidden cases do not repair a correct first plan. Random cases prevent hardcoding; they do
   not create planning depth.
4. Every new behavior must be stated accurately in the agent-authored instruction and checked by
   the verifier. The agent owns the rewrite and prose review. A changed verifier contract requires
   the contributor's explicit approval when it changes what "correct" means.
5. Preserve a concrete expert solution. The reference must remain reliable, implementation-neutral,
   and comfortably inside the stated resource limit.
6. Do not reuse a public issue, patch, benchmark, write-up, or prior task answer as the new twist.
7. Do not resubmit merely because local checks pass. Recovery ends only at the exit gate below.

## 1. Capture the failure before editing

Create a dated `Easiness recovery` entry in the task's `STATE.md` containing:

- the probe result and number of successful attempts;
- the path to every available trajectory under `probes/<slug>/`;
- each successful agent's first plan, decisive discovery, and final method;
- the earliest point at which the agent had enough information to commit to the winning plan;
- whether the plan came from the instruction, project tree, examples, a public helper, generated
  experiments, internet retrieval, or a verifier loophole;
- the existing A/B/C tactics and the tactic that failed in practice;
- the current estimated solves out of eight.

If detailed trajectories are unavailable, record that limitation and reproduce the strongest
one-shot plan yourself. Lack of probe logs is not permission to guess why the task was easy.

## 2. Classify the winning route

Choose every applicable failure mode. Point to concrete files and lines.

| Failure mode | Evidence | Required direction |
|---|---|---|
| The default plan was correct | The agent named the right algorithm or state model immediately | Add a specified interaction that makes that coherent prior wrong |
| The instruction delivered the plan | Method names, staged hints, repeated constraints, or examples exposed the decomposition | Rewrite it to state behavior without naming or teaching the method |
| The environment delivered the plan | A helper, derived field, count, flag, data pair, comment, or name reconstructed the hidden distinction | Remove the derived leak while keeping all necessary facts observable |
| The agent confirmed each step independently | Visible examples or an exposed oracle answered every load-bearing question | Deny incremental confirmation; keep only interface examples and sealed exact grading |
| A route-around bypassed the hard part | The output could be produced without satisfying the intended invariant | Fence both sides and add an ordinary case that rejects overconservative shortcuts |
| The naive method was fast enough | A correct exhaustive or quadratic approach fit the real limits | Use C3 only after measuring a principled fast path and a failing naive path at the stated scale |
| The verifier accepted a false solution | A successful attempt exploited grading rather than solving the task | Treat this as a verifier defect, obtain approval for the contract change, and return to Stage 2 |

Do not move on with a diagnosis such as "the task needs more edge cases." Name the winning plan and
the exact reason it remained valid.

## 3. Design a semantic replan

Draft two or three candidate changes in `STATE.md`. Attack each, select the strongest, and proceed.
A usable change normally has all of these properties:

- the original first plan remains reasonable, not foolish;
- a later discovery invalidates that plan rather than merely adding one local condition;
- at least two load-bearing decisions interact;
- ordinary cases punish a blanket or overconservative workaround;
- adversarial cases make the wrong plan fail late;
- the required behavior is complete and unambiguous;
- a real expert still has a step-by-step route to a solution.

Prefer a new interaction at a semantic boundary: ownership versus local state, partial rebuild
versus global completeness, nested operations versus deferred effects, identity versus value,
rollback versus committed history, or a measured scale boundary with a derivable fast invariant.
These are directions, not recipes. The new interaction must come from the contributor's domain and
must be novel for this task.

Use the retained pass research in `docs/PASSING-TASK-RESEARCH.md` to compare failure shapes. Do not
copy another task's mechanism or claim evidence from a pass label whose artifacts are unavailable.

The selected repair must use several tactics across at least two prongs from
`docs/DIFFICULTY.md`:

- Prong A: poison the default plan without making the instruction vague;
- Prong B: withhold the complete plan through genuine coupled facts or simultaneous rules;
- Prong C: make the wrong plan fail conclusively and, where natural, late;
- block the route-around.

Reject the candidate if the honest plan is still a one-shot sequence. Also reject it if no expert
path can be described; that produces zero solves, not valid difficulty.

## 4. Rebuild from the earliest affected stage

Once the strongest semantic change is selected, return to the normal workflow at the earliest
affected stage:

1. Stage 2: freeze the revised verifier contract before environment code changes.
2. Stage 3: update the environment and remove any newly exposed derived leaks.
3. Stage 4: update the single canonical reference solution and measure it.
4. Stage 5: rewrite and self-review the instruction, then gap-check every tested rule.
5. Stage 6: turn the old winning implementation into a named cheat and add a small hand case that
   proves why it is wrong. Re-run every existing cheat and alternative correct variant.
6. Stage 7: re-attack the finished task cold, run preflight, oracle, nop, isolation checks where
   applicable, the manual quality review, and rebuild the archive.

Record every changed assumption and its evidence in `STATE.md`. Do not put probe history, pass
claims, or difficulty tactics in the shipped instruction or agent-facing tree.

## 5. Measure the repair

Before spending another external probe run, require all of the following:

- the reference scores 1 reliably;
- nop and every cheat score 0;
- alternative correct implementations score 1;
- the old probe-winning plan now fails a specific hand case and the sealed suite;
- no short expression over exposed fields reconstructs the new distinction;
- any resource gate has recorded timings for both the correct and naive families;
- preflight and the full manual quality review pass;
- the cold self-attack says: "I can see where to start, but I cannot commit to the full plan without
  exploration, and my first plan is likely wrong somewhere that matters."

Then run the real easiness probe with its normal frontier model, internet access, time budget, and
environment. A reduced local simulation is preparation, not a substitute.

## 6. Exit gate

Recovery is complete only when:

1. the external easiness probe reports a pass;
2. at least one independent solve still demonstrates verifiability when the pipeline requires it;
3. the reference, nop, cheat, isolation, alternative-solution, preflight, archive, and manual
   quality gates still pass after the final change; and
4. `STATE.md` records the before-and-after trajectory analysis, the final tactics, and the realized
   result.

If the probe fails again, append the new evidence and repeat from section 1. Do not stack another
rule onto the previous repair without diagnosing the new winning route. If required infrastructure,
probe access, or contributor judgment is unavailable, mark the recovery as pending and report the
exact blocker. Never label the task ready on predicted difficulty alone.
