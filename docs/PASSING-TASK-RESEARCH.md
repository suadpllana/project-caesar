# What the retained passing tasks teach us

Updated 2026-09-06. This note is the compact research record for the only projects this
repository is meant to reference.

## Evidence boundary

The contributor supplied the pass classification:

- Project Caesar AI passed: `concurrent-commit-rules`, `delta-view-retraction`,
  `guard-mark-unwind`, `share-register-screen`, `alias-settle-report`,
  `note-carry-forward`, and `focus-return-point`.
- Human passed: `heap-file-replacement` and `late-dimension-updates`.

Six complete bundles are present under `tasks/`. Probe trajectories are retained for
`alias-settle-report`, `share-register-screen`, and `note-carry-forward`; the other local
bundles have design and validation records in `STATE.md`. The final external probe outputs are
not present for every task, so this note distinguishes three evidence levels:

- observed: a trajectory, measured mutant, or local/container result exists here;
- contributor reported: the pass is supplied by the contributor, without the final raw result;
- unavailable: no bundle, trajectory, or Git object exists in this checkout.

`concurrent-commit-rules`, `heap-file-replacement`, and `late-dimension-updates` are unavailable.
They do not occur in the working tree, any local or remote Git ref, or exact-name public search
results checked on 2026-09-06. Their pass status belongs in the inventory, but their mechanism
must not be reverse-engineered from the slug. Add a task-specific analysis only when its bundle
or trajectory is supplied.

## Comparative result

| Task | Evidence here | Default plan that loses | What made the final plan harder |
|---|---|---|---|
| `alias-settle-report` | bundle, state, three earlier trajectories; final pass contributor reported | enumerate every legal future group and solve the fixed point directly | a measured scale family where exhaustive legal-group search is exact but infeasible, plus a graph invariant that applies only when differences are absent |
| `delta-view-retraction` | bundle and detailed state; final pass contributor reported | invert sum/count and rebuild min/max/top on retraction | a selective rebuild changes the meaning of the dependency set, so the first repair predicate has to be re-derived from the row store |
| `guard-mark-unwind` | bundle, state, container gate history, easiness pass recorded | stamp one chosen guard on a travelling cancellation and match it at the boundary | a second mark can land during unwind, so the resting decision must be recomputed at each closing guard while band liveness rules still hold |
| `share-register-screen` | bundle, state, earlier 3/3 trajectory; final pass contributor reported | transitive ownership closure followed by per-holder seat counting | coalition voting changes the allocation itself, and nominee/treasury behavior changes which holdings join the coalition |
| `note-carry-forward` | bundle, state, nine trajectories across later rounds; final pass contributor reported | replay revisions, cache the chosen script, and update each note independently | the shipped edit script disagrees with standard LCS, note state is historical, and wide cases force change groups to be settled once per revision rather than once per thread |
| `focus-return-point` | final bundle and state; final pass contributor reported | either process all events immediately or defer the entire render | mutations are immediate but focus effects are deferred; requests bind to object instances; nested abort restores both objects and deletion history |
| `concurrent-commit-rules` | pass status only | unknown | unavailable - do not infer from name |
| `heap-file-replacement` | pass status only | unknown | unavailable - do not infer from name |
| `late-dimension-updates` | pass status only | unknown | unavailable - do not infer from name |

## Task findings

### alias-settle-report

The early task was already semantically dense: future aliases, declared differences, pending
posts, departures on the current tick, and a smallest self-consistent departure set. It was still
too easy. Two of three agents chose the same group enumerator immediately, copied the fixed-point
shape into the policy, and built a brute-force checker. Hidden small cases improved coverage but
did not change the plan. This is direct evidence that a fully specified finite-state predicate can
remain easy even when its implementation has many rules.

The successful repair did not add another arbitrary exception. It found a real input family in
which the agents' exact method becomes exponential. With no declared differences, every subgroup
inside the open-tag component is legal, so the union of all reachable groups is just the ordinary
connected component. Difference-bearing states still need exact group search. Locally, the
optimized reference completed the wide case in about 0.07 seconds while the exhaustive reading
was still running after 70 seconds. Reference and independent model agreed over 900 generated
sets, including the wide family.

Why this worked:

- The first plan stayed semantically correct, so ordinary correctness testing did not expose its
  failure early.
- The faster plan came from a domain invariant, not a magic timeout or undisclosed case.
- The optimization had a boundary. Applying component closure to difference-bearing states is
  wrong, so the solver still had to preserve the exact path on the other side.
- The verifier fenced both directions: eager filing and unnecessary holding both fail.
- The task denied a stable local oracle by generating graded sets after the agent finished.

Quality lesson: state the execution limit and the input scale, but do not name the optimization.
The metadata explains the intrinsic planning failure, the practitioner, and the synthetic input
distribution. The category was corrected to Software / Algorithms because the graded work is
graph and state-machine software; the evaluation setting is only narrative.

Primary local evidence: [`tasks/alias-settle-report/STATE.md`](../tasks/alias-settle-report/STATE.md),
[`tasks/alias-settle-report/task.toml`](../tasks/alias-settle-report/task.toml), and
[`probes/alias-settle-report/`](../probes/alias-settle-report/).

### delta-view-retraction

The obvious plan is the textbook aggregate split: inverse deltas for sum and count, rebuild
non-invertible min, max, and top cells on retraction. It publishes correct values and loses the
work budget. The next plan checks whether the bounded candidate accumulator is complete. Earlier
versions leaked completeness through derived quantities: first a spill field, then the difference
between retained multiplicity and retained counts, then retained multiplicity versus dependency
count. Agents wrote those comparisons before experimenting.

Removing the named leak was not enough. The final design required two linked findings:

1. An incomplete cell can still absorb a retraction if its retained candidate slots remain
   standing; only a retraction that empties a retained slot forces rereading.
2. A reread need not fold the whole live group. The bounded accumulator can only retain rows
   carrying its surviving candidate values, so the rebuild folds those rows and their
   multiplicities.

The second optimization breaks the first implementation. After a narrowed rebuild, the dependency
set names rows that were folded, not every row the group contains. A completeness test using that
set becomes wrong and must move to the row-store listing. This is the strongest reusable feature
in the task: progress on one requirement invalidates a previously correct-looking decision, so a
solver has to revise the plan rather than append another case.

The verifier couples exact published values to fold/scan ceilings, a replayable work journal,
runtime instrumentation, and lifecycle traces. A conservative full rebuild cannot pass on values
alone, and a forged low counter cannot pass without consistent evidence. The state records 22
cheats scoring zero, four alternative correct implementations scoring one, and the two-image
oracle/nop/isolation results.

Quality lesson: never publish the target budget as a stopping oracle, and grade a ceiling rather
than exact work so a better correct implementation can pass. Search every pair of exposed numeric
fields for a derived witness; deleting a field name does not delete the information.

Primary local evidence: [`tasks/delta-view-retraction/STATE.md`](../tasks/delta-view-retraction/STATE.md)
and [`tasks/delta-view-retraction/task.toml`](../tasks/delta-view-retraction/task.toml).

### guard-mark-unwind

This task wins without a scale gate. Its leverage is a strong prior that is correct almost
everywhere: single-delivery cancellation chooses a target, stamps it on the travelling exception,
and recognizes that target at a boundary. The shipped runtime behaves coherently under that model,
which makes the first repair easy to believe.

The counter-rule appears only when another guard is marked while the cut is already travelling.
The marked guard that should receive or stop the cut can change during unwind. The decision must
therefore be settled again as guards close, while the outermost-visible mark, child liveness, band
handover, errors, and unmarked pass-through rules remain consistent. A wrong reading differs by a
small number of tokens in an otherwise plausible trace, so ordinary smoke tests provide little
feedback.

The state records a useful fairness correction. One zero-solve run was caused partly by an
unstated error rule and dead fields that looked like deliberate clues. The hard unwind discovery
was found; peripheral ambiguity caused the miss. The repair stated the missing observable rule and
deleted the false affordances without revealing where the cut rests. This is the right response to
a task that is unfairly hard: repair alignment and dead scenery, not the central mechanism.

The verifier uses 28 enumerated programs and 300 nonce-generated programs, exact event traces and
fiber token lists, 24 cheats, and six correct variants. The reference is stored once beside
`solve.sh`, avoiding the quality-review failure caused by duplicate inlined source.

Primary local evidence: [`tasks/guard-mark-unwind/STATE.md`](../tasks/guard-mark-unwind/STATE.md)
and [`tasks/guard-mark-unwind/task.toml`](../tasks/guard-mark-unwind/task.toml).

### share-register-screen

The first plan is almost correct and strongly supported by public material: build an ownership
graph, seed named parties, take a transitive closure, and decide control from seats allocated to
holders already on the list. The earlier brief made the coalition correction too explicit, and
all three agents solved it in a few minutes.

The repaired task removes the algorithmic reveal and relies on interacting business rules. Listed
holders arrive at a meeting as one voting hand. Combining them changes the seat allocation, so
adding up seats they would take separately is not a conservative approximation; it is a different
board. Nominee and treasury behavior then changes what joins that hand. The closure, coalition,
and holding rules cannot be solved independently because each changes the next iteration's input.

This task shows why "more hidden cases" is not a repair by itself. The useful change was a third
decision that breaks the natural coalition implementation and the removal of prose that announced
the collapse. The final verifier has 23 enumerated registers and 320 generated registers, exact
integer outcomes, 21 cheats, and six correct variants including the earlier probe solution where
it remains semantically valid.

Quality lesson: use the category of the work, not the story. Explain the synthetic concentration
of coalition and nominee cases as adversarial but realistic. Keep paths formatted consistently
and remove padded prose; the instruction must specify outcomes without narrating the strategy.

Primary local evidence: [`tasks/share-register-screen/STATE.md`](../tasks/share-register-screen/STATE.md),
[`tasks/share-register-screen/task.toml`](../tasks/share-register-screen/task.toml), and
[`probes/share-register-screen/`](../probes/share-register-screen/).

### note-carry-forward

This task was repeatedly improved by reading agent trajectories rather than guessing. Twelve
decisions are graded: a nonstandard chosen edit script, span shrinkage, outdated retention,
first-contact raising, answered reopening, resolved behavior, event order, absorbed-thread routing,
and fixed-point overlap merging. Yet two of three agents still solved it in four to nine tool calls.
They read the compact project at once, cached the script per revision pair without prompting, and
wrote the two artifacts in one pass. File count was not Prong B; the full system fit in attention.

The successful direction had two parts:

- Remove plan delivery. An annotated sample, a sentence explicitly refuting one sweep, and a
  helper that restated standard LCS behavior all told agents what to repair.
- Add a measured semantic scale boundary. Change groups belong to a revision pair, but the wrong
  policy recomputed them once per thread. Profiling showed the edit table was 91 percent of the
  run. On a wide stream, settling once per revision took about 1.4 seconds and settling per thread
  took about 58 seconds, a 40x difference; 36 wide streams sit behind a 600-second run limit.

This is a good C3 because the rule is unchanged. The wide family makes an unnecessary recomputation
fatal, while the correct cache follows directly from ownership of the derived value. A proposed
quadratic merge gate was rejected after measurement because 61,020 merge calls took only 0.012
seconds. The lesson is to profile before inventing a budget.

Quality lesson: adding decisions does not create difficulty when each remains visible and locally
checkable. Remove commentary and development files from the shipped bundle, keep test comments on
the verifier side, and make every stated corner map to a real hand case and a wrong-reading cheat.

Primary local evidence: [`tasks/note-carry-forward/STATE.md`](../tasks/note-carry-forward/STATE.md),
[`tasks/note-carry-forward/task.toml`](../tasks/note-carry-forward/task.toml), and
[`probes/note-carry-forward/`](../probes/note-carry-forward/).

### focus-return-point

Two smaller versions failed at two solves out of three. Nested navigation and object-lifetime
identity sounded difficult, but agents included both in their first plan after two reads. The
final change altered the timing model rather than adding more random histories.

Nested render transactions apply tree edits immediately but delay focus effects. A focus request
binds to the object instance present when issued, then resolves against the final tree at the outer
commit. Inner commit retains work that an outer abort can still discard. Abort restores the
original objects and the deletion records that belonged to that frame. Current id lookup is still
used for new events, so a reused id can refer to a replacement while an older modal return refers
to the retired instance.

Neither familiar plan works. Immediate processing loses focus and changes memory during transient
renders. Deferring everything binds to the wrong lifetime and repeats mutations. The correct plan
has to separate structural state, instance-bound intents, settled focus, and rollbackable deletion
history, then compose them with different Tab/arrow scopes and group memory. The late discriminator
requires an aborted widget to be restored, moved, and later lose another ancestor.

The final verifier compares 89 literal trails and 1050 generated histories (300 general, 300
nested, 150 id-reuse, 300 render). The reference and independent model agreed on all 1139 graded
histories plus 2000 additional render histories; the earlier reference fails 18 of the 21 render
examples. The task is compact and does not claim B1. Its difficulty is A1/A3 plus interacting B2,
with exact C1/C4 grading.

Quality lesson: compact is acceptable when the semantic conjunction is real. The metadata must
say that the environment is small and that terse naming is deliberate, then explain the actual
timing and identity collision instead of claiming difficulty from file count.

Primary local evidence: [`tasks/focus-return-point/STATE.md`](../tasks/focus-return-point/STATE.md)
and [`tasks/focus-return-point/task.toml`](../tasks/focus-return-point/task.toml).

## Cross-task conclusions

### What repeatedly moved an easiness rejection into a pass

1. Change the plan, not the amount of work. Added random cases did not help when every agent began
   with the correct plan. A new interaction or a semantic scale boundary did.
2. Require at least two discoveries, with the later one invalidating the earlier implementation.
   `delta-view-retraction` is the clearest example; `focus-return-point` does the same across event
   binding and rollback.
3. Make the default prior coherent and specifically wrong. Cancellation tokens, ownership
   closure, ordinary LCS, aggregate invertibility, and immediate/deferred UI processing all gave
   agents a strong plan that survived ordinary examples.
4. Remove derived leaks, not just labels. Compare exposed counts, lengths, dependency sets,
   cached flags, and public helper outputs. If a short expression reconstructs the hidden
   distinction, the task has no planning depth there.
5. Deny incremental confirmation. Visible examples may demonstrate the interface, but they must
   not form an oracle for each load-bearing decision. Exact independent verification belongs on
   the sealed side.
6. Use a measured C3 only where the naive method remains correct. State the time and scale fairly;
   make the fast path follow from an invariant; prove both sides with differential tests and
   alternative correct implementations.
7. Treat trajectories as data. Identify whether the winning plan came from the brief, the tree, a
   self-built checker, or confirming data. Repair that source. Do not blindly add rules or rewrite
   prose.

### What repeatedly helped quality review

1. Describe intrinsic difficulty in `task.toml`: the practitioner, realistic or intentionally
   concentrated data, the natural wrong plan, and the exact interaction that breaks it. Do not put
   revision history, probe counts, or future work in shipped metadata.
2. Keep the contributor's instruction concrete and complete without describing the method. Every
   tested rule needs one sentence; every sentence needs a test. State paths, limits, input bounds,
   output order, and both sides of each fence.
3. Categorize the skill exercised by the graded work, not the narrative setting. Tags name the
   actual mechanisms.
4. Keep the agent tree lean. No comments, docs, answer material, dead fields, unused helpers, or
   development artifacts. A compact honest project is better than scenery.
5. Keep the reference in one place beside `solve.sh`. Do not inline long files or ship duplicate
   copies that can drift.
6. Prove behavior rather than trust submitted reports. Use an independent oracle, exact
   all-or-nothing comparison, pristine overlays, unprivileged execution, root-owned reward,
   survivor cleanup, output attestation, and answer-key/reward-tamper cheats when submitted code
   runs inside the verifier.
7. Test alternative correct implementations. If a variant that follows the contract scores zero,
   the verifier is grading an implementation choice.

## Required intake for a future task

Before environment work begins, write these answers in its `STATE.md`:

1. What is the frontier agent's first plan?
2. Which exact requirement makes that plan wrong?
3. What second discovery forces a replan instead of a patch?
4. What shipped field, helper, sample, or pair of quantities could reveal either discovery?
5. What ordinary case prevents an overconservative solution?
6. What adversarial case makes the wrong plan fail late?
7. If using a resource gate, what measured invariant gives the correct fast path, and what input
   scale is stated in the instruction?
8. Which wrong-plan implementation will be kept as a cheat, and which hand case separates it?
9. Which independent correct variant proves the verifier is implementation-neutral?
10. Why would a real expert solve this in a clear sequence even though the first plan is likely
    wrong?

A candidate with weak answers to questions 2 or 3 is still easy. A candidate with no clear answer
to question 10 is not hard; it is unverifiable.

## Do not overlearn the examples

- A large repository is not required. `focus-return-point` is compact, and its interaction is the
  difficulty. Claim B1 only when the project genuinely exceeds one attention window.
- A timeout is not difficulty. It matters only when a naive correct family is measured to fail and
  a principled expert path is measured to pass.
- Random generation is not difficulty. It prevents fitting; it does not repair a correct first
  plan.
- Missing information is not difficulty. Every behavior remains fully specified. The hard part is
  forming the plan that satisfies all of it.
- A pass label without artifacts is not mechanism evidence. Keep the three unavailable tasks in
  the inventory, but do not use their names to justify a new design.
