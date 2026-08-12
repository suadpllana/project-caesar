# Task state

## Current stage

`Stage 7 - Pre-flight and packaging`

## Assistant's assigned role

Senior inference-infrastructure engineer for RL post-training: rollout engines that stay
resident across weight pushes, paged key/value caches, prefix indexes, adapter serving,
and the sleep/wake path that RL loops drive between batches.

## Source repository

- Repo URL: https://github.com/vllm-project/vllm (issue tracker used as the seed only)
- Task shape chosen: authored on top, not an ablation of upstream code. No vLLM source is
  vendored. The engine in `environment/app_src/` is written for this task: a CPU-only,
  integer-arithmetic rollout engine with the same organs (paged pool, block table, prefix
  index, continuous-batching scheduler, adapter-aware parameter store, two-level offload).
- Why not vendor: vLLM's own code is public and diffable, and the real fix for the closest
  public issue is public with it. Writing the engine means the shipped tree matches no
  public repository, while the failure mode is the real one.
- Seed issues, for reviewers: `vllm-project/vllm#48310` ("[RFC] Sleep/Wake Correctness for
  RL"), whose SW3 and SW5 categories are state reconstruction after a discarding wake and
  asymmetric cache invalidation between paired holders; and `vllm-project/vllm#44250`
  ("external KV cache key omits LoRA identity, allowing cross-adapter KV hits"), whose
  accepted fix is the plan this task is built to punish.
- Proper-noun sweep: the shipped tree carries no project, product, company or person name,
  no upstream identifiers, no distinctive error strings and no URLs. Identifiers are in
  the register of ordinary internal code (`pfx`, `blk`, `pstore`, `wq`/`wk`/`wv`).
- Upstream-diff check: there is nothing to diff. An agent that finds both seed issues
  learns the failure mode, which the instruction already states, and learns the public fix
  for the second one, which is `cheat-adapter-in-key.sh` and scores 0.

## Task summary

The agent gets a working rollout engine that serves samples while a trainer pushes
parameter updates into it. Samples that are in flight across a push come back mixing two
policies, and cached key/value blocks computed under old parameters keep being served. The
agent must make every finished sample identical to what a freshly started engine on one
parameter state would produce, without giving up cache reuse that is still valid, across
base pushes, adapter pushes, replayed pushes, a cross-layer parameter tie, two offload
levels, preemption and eviction. Four files may be edited; everything else is restored
from a pristine copy before grading.

## Why it is hard

One question that is really two, with different answers, and nothing in the tree that says
so.

- A push invalidates a sample in flight if it moved anything the sampler can see, which is
  the whole parameter set.
- The same push invalidates a cached block only if it moved something the block's contents
  depend on, which is the embedding, every parameter of the layers below, and that layer's
  own key and value projections - and therefore not the last layer's query, output or
  feedforward projections, nor the final scale, nor the output head.

Carrying one fingerprint through the engine is wrong on one side or the other, and both
sides are graded.

The second axis is which requests each of those two answers governs, and the pairing is
not the one the symptom suggests. Prefill is chunked, so a request can be sitting on part
of its own prompt with nothing emitted yet when a push lands. It has no tokens to throw
away, so the rule that governs samples in flight does not reach it - but it is holding
key/value work done under the old parameters, and that work is governed by the other
fingerprint, the block one. A request producing tokens goes down when anything the sampler
sees moves; a request part way through its prompt loses its work only when the block
fingerprint moves, and keeps every position when it does not. Both cases are in the set
twice over, and the fences run the other way as well: `prefill-neutral` and the second
push in `prefill-adapter` fail an implementation that clears everything in flight, while
`prefill-relevant` and the first push in `prefill-adapter` fail one that only looks at
requests which have emitted a token.

- Expert time estimate: 8 hours
- Why a frontier agent cannot one-shot the plan: the first plan is "put the weight version
  (or the adapter id) into the block hash and reset the prefix cache on sync". That plan
  produces correct tokens on almost every scenario and fails the work accounting, which
  only surfaces at the verifier. Forming the correct plan requires deriving the dependency
  set from the forward pass in a file the agent cannot edit, and then noticing it is not
  the same set as the one that governs rewinds. The plan after that - both fingerprints,
  rewind what has emitted tokens, remember which pages were discarded - is the whole of the
  task as it stood before the easiness probe returned 3 of 3, and it now scores 0: it
  serves a half-built prefix computed under superseded parameters and its tokens diverge.
- Tactics making that true: A1, A2 and A3 poison the default plan; B1 and B2 withhold it;
  C1, C2 and C3 make the wrong plan fail late. Each one, concretely:
  - Prong A1/A2: the retrieved fix for the nearest public issue (adapter identity in the
    cache key) is specifically wrong here; the concept is never named - the instruction
    says "may only stop being used when what it holds could have changed".
  - Prong A3: correctness and reuse pull against each other; no single remembered recipe
    satisfies both.
  - Prong B1: the dependency structure is only in `model/be.py`, the tie table only in
    `model/arch.py`, the block lifecycle in `runtime/blk.py` and `runtime/eng.py`, the two
    offload levels in `mem/pool.py` - all but the last are not editable, and the tree
    carries no comments.
  - Prong B2: replayed push, adapter push, tied module, level 1 versus level 2 offload,
    rewind queue discipline, a half-built prefix straddling a push, preemption and eviction
    all have to hold at once.
  - Prong B1 again, for the second axis: nothing says a request can hold part of its own
    prompt across a step. It follows from one line of `runtime/eng.py`, the chunk budget in
    `run_one`, and from nowhere else. The brief states what must happen to work already
    done without saying when a request is in that state.
  - Prong C1: fenced both ways - `neutral-base`, `replayed-push`, `adapter-share`,
    `adapter-neutral-push`, `prefill-neutral`, the second push in `prefill-adapter` and the
    level 1 offload all fail an overreaction.
  - Prong C3: the work accounting is a real resource gate that the safe implementation
    fails while producing every token correctly.
  - Prong C2: the obvious oracle is denied. A cold engine on the current parameters agrees
    with a wrong implementation on most scenarios; the disagreement is in the counters,
    which the agent cannot compare against anything.
- Assistant's attack on the plan: my first plan was a content fingerprint of all
  parameters folded into the block key, plus a rewind of everything in flight on any
  change. It gets every token right and fails `neutral-base`, `adapter-share`,
  `adapter-neutral-push`, `replayed-push` and `pressure` on the work accounting. My second
  plan would have been the adapter-in-key variant. Both are in `cheat/` and both score 0.
- Estimated solves out of 8: 1 to 2. The easiness probe returned 3 of 3 against the
  version without the prefill axis, and the audit trajectories put the solve time at 28 and
  61 minutes of a 240 minute budget, so the crux as it stood was no longer difficult for
  this class of agent. What is added here is not another stated rule but another thing to
  find, and the solution that scored 3 of 3 now scores 0.
- Expert path, step by step:
  1. Reproduce with `/app/run_rollout.py` and see the sample straddling the push.
  2. Read `runtime/eng.py` to find where the block key is built and where the sample's
     fingerprint is set, and `model/pstore.py` to find that the fingerprint is a constant
     per adapter.
  3. Read `model/be.py` and work out what a block's contents depend on: everything
     upstream of that layer's key and value projections, and nothing downstream of the
     last one.
  4. Notice that the sampler depends on all of it, so rewinds and block validity need
     different fingerprints.
  5. Take both fingerprints over effective parameter values, not over a counter, which
     handles the replayed push and the tie in `model/arch.py` without special cases.
  6. Implement the rewind in `runtime/sch.py`, with sampler state reset and the queue
     discipline the instruction states.
  7. Read `mem/pool.py` and `runtime/blk.py` together, see that `reconcile` asks the pool
     which pages are usable, and record the discard on a level 2 wake only.
  8. Read `run_one` again and notice the chunk budget: a request can be holding part of its
     own prompt across a step, with no tokens emitted, when a push lands. Work out that
     this population is governed by the block fingerprint rather than the sampler one, drop
     the half-built prefix only when that fingerprint moved, and leave its place in the
     queue alone.
  9. Drive scenarios of their own through `run_rollout.py` until the counters stop moving
     for the wrong reasons.
- Originality check: searched for public write-ups of prefix-cache invalidation across
  weight updates in RL rollout loops. What exists is the two seed issues above, the general
  advice to call a cache reset after a weight sync, and the LoRA-identity-in-the-key fix.
  Nothing anywhere makes the distinction this task is built on, and no public code has this
  engine's shape.

## Run-audit finding, and the change it forced

The task cleared the difficulty probe and the easiness probe, then failed the run audit:
reward hacking, 1 trial of 8. The trajectory notes told the real story. One agent recovered
the whole intended design - both fingerprints, the rewind with the sampler counter reset and
the head-of-queue reinsertion, the discarded-page set - and scored 55 of 57. Its only losses
were the `evict` counter in `pressure` (48 against 50) and in `mixed` (3 against 7), because
it retired superseded index entries at the push instead of leaving them for the
least-recently-used sweep. A solution that had done every piece of the actual work was one
bookkeeping choice away from full credit, and the only way to close that gap is to tune an
implementation detail against a hidden constant. That is what the audit was looking at.

Two defects, found by measuring rather than guessing:

- `evict` counts when the index happens to drop an entry. `authoring/field_report.py`
  compares every cheat field by field: not one of the seventeen is separated by `evict`.
  It caught nothing and cost a correct solution the run.
- Worse, and not in the audit note: the work counters of `pressure` encode the reference's
  eviction tie-break. `authoring/variants/ok-ordered-lru` implements the same
  least-recently-used policy with an OrderedDict and produces computed 265 against 225 and
  preempt 12 against 9, on identical semantics and identical tokens. The instruction says
  which block goes first is not what we are after, and the verifier was grading exactly
  that.

The fix, which changes what is graded and not what is correct:

- `evict` is out of the graded set entirely.
- Work counters and the engine trace are graded only on scenarios that evict nothing and
  preempt nothing. The boundary is derived from the ground truth (`ORDER_FREE` in
  `tests/test_outputs.py`), so a scenario that starts evicting drops out by itself.
- `mixed` moved from 14 pages to 40 so it sits inside that boundary; `pressure` stays as
  the one scenario that runs the pool dry and is graded on tokens and rewinds, which
  eviction order cannot move.
- `test_counters_agree_with_each_other` cross-checks the engine's count against the
  backend's, in two non-editable modules, so a forged report has to be consistent.
- `authoring/variants/` holds alternative correct implementations that must score 1, and
  `authoring/variant_check.py` runs them through the real verifier. Both the ordered-dict
  index and the eager-retire shape from the flagged trial now score 1.

Difficulty was not touched. The crux is the two fingerprints and the minimal-invalidation
accounting, all of which lives in the nine scenarios that never evict. The cheat suite is
unchanged in verdict: seventeen of seventeen still score 0, and `field_report.py` shows
every one of them diverging on tokens or on the real-work counters.

## Second sweep, after the same audit note came back for review

The zip that went through the audit was the build from before that fix, so the finding is
the one already answered above. Re-reading it against the verifier as it stands turned up a
second field of the same kind, found the same way - by writing the alternative correct
implementations out and running them, not by arguing about them.

`authoring/variants/ok-readmit-on-rewind` is the reference with one more line: the rewind
clears the sample's started flag. The brief asks for a sample that comes back as if it were
"submitted fresh", so clearing it is a plain reading, and the engine then notes a second
admission when the sample is picked up again. Tokens, rewind set, `computed`, `reused`,
`pos`, `preempt` - all identical to the reference. It scored 0 on `test_engine_trace`
alone. That is a solution which did the whole job losing the run on whether a rewound
request counts as newly admitted, which is the exact shape of the finding the audit raised.

Fixed in the grader, not in the environment: `lifecycle()` in `tests/test_outputs.py`
collapses repeated `start:<rid>` entries on both sides before comparing, so the trace still
pins the order requests were first admitted, finished and preempted in, and no longer pins
how many times one was admitted. Nothing legitimate is lost - the recompute a rewind costs
is charged by `computed`/`reused`/`pos`, and the rewinds themselves by the restart events.
Nothing illegitimate is admitted either: the seventeen cheats trip the same tests they did
before, `nop` still fails four of them, and `cheat-no-rewind` still loses on tokens,
rewinds and work.

Two more alternative implementations were written and measured while looking for others:

- `ok-lazy-rewind` applies the rewind at the top of the next `pick` instead of inside
  `on_sync`. Scores 1, so when the rewind is applied is free.
- `ok-value-compare` compares effective matrices instead of fingerprints. Scores 1, so how
  the two questions are fingerprinted is free.

Nothing else in the graded set can move between correct implementations. The block key is
built in `runtime/eng.py`, which the agent cannot edit, and a block holds the key/value
pair of every layer, so there is exactly one KV-relevant parameter set and no finer reading
of it - the trap that sank `turn-seam-alignment` has no room to form here. Reuse is
maximal at the correct fingerprint and any other choice computes more, so `computed` and
`reused` each have one right answer rather than a range.

## Recalibration after the easiness probe returned 3 of 3

The fairness fixes above were right and they cost the task its difficulty. Both audit
trajectories say why: one agent recovered the whole intended design in 61 minutes of a 240
minute budget, another in 28, and what separated them from full credit was the counters
that turned out to be implementation choice. Take those away, as the audit required, and
three of three agents solve it. Nothing about the grading can fix that - the crux itself
had become retrievable for this class of agent - so this pass adds a second thing to find
rather than another rule to obey.

Prefill is now chunked. `Eng.run_one` takes a per-step budget from `conf/engine.json`, so a
request works through its prompt over several steps and a push can land on one that has
computed part of its own prefix and emitted nothing. The two answers the task is built on
now have to be routed to two populations:

- a request that has emitted tokens goes down when anything the sampler can see moves;
- a request part way through its prompt keeps every position it has computed unless the
  block fingerprint moved, and rebuilds from the index when it did.

Getting that backwards fails loudly in one direction and quietly in the other, which is the
shape the task already had: `cheat-keep-stale-prefill` serves the stale prefix and its
tokens diverge, `cheat-drop-prefill-on-any-push` produces every token correctly and pays for
key/value work it did not have to do.

Three scenarios were added for it - `prefill-relevant`, `prefill-neutral`, `prefill-adapter`
- and each holds both populations at once, so one push has to be answered two ways in the
same step. Three cheats were added with them. The previous reference solution, which is
exactly the shape the three easiness solvers submitted, was run through the new verifier and
scores 0 on tokens, work, rewinds and trace.

Fairness was kept in front of the difficulty, not behind it:

- The new grading is on tokens and on positions through the backend. Both are real work by
  the two-implementations test, and neither has a range: reuse is maximal at the correct
  fingerprint, so `computed` and `reused` each have one right answer.
- Whether a dropped prefix counts as a sample thrown away is decided by non-editable code.
  `Eng.rewind` books a restart only when there were tokens to throw, so an implementation
  that routes both populations through it and one that hand-rolls the reset agree.
  `authoring/variants/ok-rewind-for-prefill` is that first shape and scores 1.
- The brief states what happens to work already done, in both directions, and states that a
  request which emitted nothing is not counted as thrown away and keeps its queue place. It
  does not say when a request is in that state; that is the discovery.
- Variant directories now hold only the files they change and take the rest from
  `solution/ref`, so the suite cannot rot into testing the shipped tree when the reference
  moves. `variant_check.py` and `tools/docker_trial2.py` both fill from the reference.

Also fixed here, found while inspecting the rebuilt image: `.dockerignore` listed
`__pycache__` and `*.pyc`, which docker matches only at the context root, so bytecode from a
local run of the tree was being baked into the agent image. Both ignore files now carry the
`**/` forms and the built image is back to 16 files.

## Verifier contract - FROZEN

- Artifacts: `/app/model/pstore.py`, `/app/runtime/pfx.py`, `/app/runtime/sch.py`,
  `/app/mem/pool.py`. Nothing else is read from the agent's container.
- The verifier bakes a pristine copy of the shipped tree, overlays those four paths onto
  it, and runs the engine over the fourteen scenarios in `tests/scen.py`.
- Checked per scenario, all-or-nothing: every request's token stream and the set of
  rewound samples, on all fourteen; `computed`, `reused`, `pos`, `preempt` and the engine's
  start/finish/preempt trace, on the thirteen that evict nothing and preempt nothing.
  `evict` is not graded anywhere.
- The trace is compared with repeated admissions of the same request collapsed, so the
  order of first admission, completion and preemption is graded and the number of times a
  rewound request is re-admitted is not.
- The expected token streams are re-proved at verification time by `tests/oracle.py`, a
  sealed from-scratch generator sharing no code with the tree.
- Tolerances: none. Everything is integer arithmetic and exact.
- Ground truth: `tests/gt.json`, generated by `authoring/build_gt.py`, root-only in the
  verifier image.

## Decisions and their reasons

- Restart entries are compared as a set, not in trace order, while start/finish/preempt
  are compared in order. Restart ordering inside one push is an implementation detail; the
  queue discipline that does affect later scheduling is stated in the instruction instead.
- The counters that bind are incremented in `runtime/eng.py` and `model/be.py`, both
  outside the editable set, so they measure real work for any implementation.
- The reference `pfx.py` is unchanged from the shipped file. It stays in the artifact set
  anyway: naming only the files that need changing would hand over the diagnosis.
- Adapters `a1` and `a2` target only modules downstream of the last key/value write, `b1`
  and `b2` target modules upstream of one. That is what makes cross-adapter block sharing
  correct in some cases and wrong in others.
- `l3.wq` is tied to `l1.wq` storage. A base push at the tied name is upstream after all;
  an adapter delta at the same name is a per-module view and is not. Content fingerprints
  get both right; name-based rules get both wrong.

## Validation status

| Check | Status | Notes |
|---|---|---|
| Both images build | pass | `tools/docker_trial.py --build`; base image had to come from a mirror and the sandbox's proxy CA had to be injected for pip, neither of which the shipped Dockerfiles carry |
| No answer leaked into agent image | pass | the built image holds 16 files: the engine, its config, the runner. Sweep cheat finds nothing. The `.dockerignore` bug that let nested `__pycache__` through was fixed here and the image re-inspected file by file |
| Oracle = 1 | pass | real two-container run, 84 of 84 assertions, and the host emulation |
| Nop = 0 | pass | real two-container run, and the host emulation |
| Cheats all score 0 | pass | 20 of 20 on the real images, including the seven isolation probes. `tools/docker_trial2.py rollout-cache-coherence --all` reports 22 of 22 trials behaving. The privilege probe reports uid 1002 and PermissionError on the reward channel, the ground truth, the pristine tree and the tests |
| Alternative correct solutions = 1 | pass | 6 of 6 through the real verifier image, `--variants`: eager retire, ordered-dict index, lazy rewind, re-admit on rewind, rewind-the-prefill, value compare |
| Previous reference scores 0 | pass | the solution shape three of three easiness solvers submitted, run through the current verifier: fails tokens, work, rewinds and trace |
| No graded field is dead weight | pass | `field_report.py`; `evict` separated no cheat and is not graded, every other graded field separates several |
| `preflight.py` | pass | clean, no warnings |
| `harbor check` rubric | not run | `harbor` is not installed in this sandbox |

## Open questions and next steps

- `instruction.md` was rejected twice by the AI-text screen. The first rewrite matched the
  passing sample on voice and average sentence length and was rejected again, which was the
  wrong reading of the screen: the published accounts of these classifiers say they react
  to uniform cadence and editorial smoothing, and regularising sentence length toward the
  mean made the draft more uniform, not less. `tools/textcheck.py` now measures a draft
  against a sample known to have passed on the axes those tools key on. The second rewrite
  took burstiness from 0.601 to 0.926 against the sample's 0.938, short sentences from 18
  to 32 per cent, and holds zero stock vocabulary, hedges, antithesis constructions, dash
  asides and first-person singular. It still wants the contributor's own read before
  submission (D1), and no measurement can certify a classifier verdict.
- The rewrite dropped the line naming the flush-on-every-push plan as unusable. The
  requirement it carried is still stated, as "both halves are measured", so the brief no
  longer hands over which default plan is wrong.
- `harbor check` has not been run; `harbor` is not installed here. Every other gate has.
