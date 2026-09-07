# Task state

## Current stage

`Stage 7 - Pre-flight and packaging`, after the easiness recovery of 2026-09-07. Every local gate
passes. The recovery is **not complete**: `RAISE-DIFFICULTY.md` section 6 closes only on an
external easiness probe pass, and no probe run is available from this machine. See "Open
questions".

## Assistant's assigned role

Not supplied in the contributor's words. Working persona: runtime engineer on a language
implementation, generational collectors, write barriers and weak maps.

## Source repository

- Repo URL: none - idea-based task.

## Task summary

`/app` is a small generational runtime: a nursery and an old space, objects with fields, frames
with named slots, a global table, a handle stack, pins, a weak reference table, a table of weak
key-value pairs, finalizers, and a remembered set fed by a write barrier. A program is a text
file of ops and `/app/run_prog.py` prints a line per event. Five files under `/app/col` decide
roots, reachability, finalizer retention, ageing and clearing; four ship wrong.

## Why it is hard

- Expert time estimate: 8 hours.
- Why a frontier agent cannot one-shot the plan: the rules are stated, but several facts the
  rules depend on are behaviours of the tree. The remembered set stores a value that is never
  refreshed, which is visible only in `mem/rset.py`; whether an object is in the nursery or old
  space depends on the ageing rule the agent is also writing; and the five modules consume each
  other's answers, so no one of them can be settled alone.
- Tactics making that true: A1, A2, A3, B1, B2, C1, C2, C3, C4.
  A1 - identity. Every collector in the training data, the shipped one, and all three probe
  trajectories key the runtime's records on the integer id. Here a released number is handed out
  again and the records are about the object, so the memorized default is specifically wrong at
  two of the nine decisions and silently right-looking everywhere else.
  A2 - the mechanisms are described operationally and never named: no "ephemeron", no
  "tricolor", no "resurrection", no "write barrier", no "generational reference".
  A3 - the pair fixed point, the finalizer reprieve and the generational split have textbook
  answers that do not compose, and the identity rule contradicts the remembered-set rule: one
  says the record is stale so re-read the field, the other says the record is the answer.
  B1 - the load-bearing facts are spread and none of them is in the brief: the barrier's trigger
  in `mem/rset.py`, the serial in `mem/heap.py`, the finished-finalizer record in `ops.py`, the
  stamped pair row in `mem/tables.py`, promotion in the module the agent is writing. The brief
  states that records do not carry over; which records they are is only in the tree.
  B2 - ten stated decisions whose interaction is the work; getting ageing right changes which
  space an object is in, which changes what the next collection traces, which changes which
  numbers come free, which changes what the records mean.
  C1 - both fences: `plain-drop`, `all-live`, `weak-live`, `reuse-live`, `rset-fields` fail an
  over-conservative collector; `old-safe`, `rset-root`, `weak-old`, `reuse-fin`, `reuse-key` fail
  an over-eager one.
  C2 - the shipped collector is wrong in all five modules, so running it confirms nothing, and
  it now dies with a `KeyError` on `progs/churn.txt` rather than printing a wrong answer.
  C3 - a measured scaling boundary that kills the plan the probe agents actually wrote, rather
  than one nobody reached. Numbers under "The repair, measured".
  C4 - all-or-nothing over 32 hand programs and 378 nonce programs generated after the agent
  finishes, across eight families.
- Assistant's attack on the plan: my first plan is the previous version of this task - roots,
  the pair fixed point, finalizer retention, the remembered set re-read - and it is what all
  three probe agents wrote. It is now wrong in two places that print nothing on a small program
  (a finalizer retired by number, a pair row followed onto a fresh occupant) and it does not
  finish the graded set.
- Estimated solves out of 8: 3 (honest range 2 to 5). This is a prediction and not evidence;
  the external probe is the only thing that settles it.
- Originality check: the parts are documented separately. The conjunction with a stale
  remembered set, a generational split and the reprieve interacting is on no page, and the brief
  names none of the concepts.

## Verifier contract - FROZEN

Re-frozen 2026-09-07 at the start of the easiness recovery, before any environment code changed.

- Artifacts: the five files under `/app/col/`.
- `plan.roots(h, full)`, `scan.reach(h, start, full, barred)`, `keep.settle(h, seen, full)`,
  `age.promote(h, seen, held)`, `wipe.wipe(h, seen, full)`, `wipe.release(h, seen, held, full)`.
- Graded: the ten decisions listed in the `tests/test_outputs.py` docstring. Decision 10 is new:
  a number is not an object, so nothing the runtime recorded about a released object answers for
  the next occupant of its number - not the finished-finalizer record, and not a pair row written
  about it as a key.
- Never graded: traversal order, container types, the order within each returned collection (the
  runtime sorts), internal naming.
- Not graded by any assertion, and decided by the execution limit alone: what a minor collection
  may cost. Three things follow from the same invariant - index the pair table rather than
  rescanning it, scope the nursery passes to `h.young` rather than the heap, and drop
  remembered-set entries that no longer name a nursery object. None of the three moves a line of
  output, which is why none of them can be an assertion.
- Ground truth: `tests/gt.json` for 32 hand programs, frozen from the sealed model and
  cross-checked against the reference through the real runtime. Nonce programs are generated in
  the verifier and checked against `tests/model.py`. The grader asserts model and `gt.json` still
  agree before grading anything.
- Contract change, and it needs the contributor's eye: decision 10 changes what "correct" means.
  It was introduced under the `RAISE-DIFFICULTY.md` recovery, which requires re-freezing at
  Stage 2, and it is the change the whole repair rests on.

## Easiness recovery - 2026-09-07

### 1. The failure, captured before editing

The external easiness probe rejected the bundle: **3 of 3 sampled frontier agents solved it**.
The bundle they were given is the one landed in `e2853fb`, not any earlier draft.

Trajectories supplied by the contributor in the session transcript, not as files under
`probes/reach-pair-sweep/` - recorded here because that directory does not exist for this task:

| Agent | Steps | Tool calls | Shape |
|---|---|---|---|
| `reach-pair-sweep__Ejvf9mj` | 7 | 5 | find+wc+cat, cat-all, rewrite five files, two verification calls |
| `reach-pair-sweep__UmUdmtm` | 7 | 5 | identical shape, plus a hand-case batch |
| `reach-pair-sweep__aVVmqoi` | 6 | 4 | identical shape, one fewer verification call |

All three ran the same plan, and it is the correct one:

- **First plan.** Read the tree, diff each of the five shipped modules against the paragraph of
  the brief that governs it, rewrite all five in one edit.
- **Decisive discovery.** None. Agent `Ejvf9mj` states the complete defect list in its thinking
  block at step 3, immediately after the single `cat` of every file: the remembered set is not a
  minor root and is not seeded at promotion, held objects age, the queue is settled late, old
  pair keys are unready, and the pair loop is quadratic. That is the whole answer, and it is five
  graded decisions plus the scaling boundary, formed with no experiment run.
- **Earliest commit point.** Tool call 2 of 4-5, before any program was executed. The plan
  preceded all evidence gathering; the remaining calls confirmed it and none revised it.
- **Where the plan came from.** The instruction and one read of the project tree. No internet
  retrieval, no generated experiments, no verifier loophole. Nothing was searched for.
- **Existing tactics, and which failed.** Claimed: A2, A3, B1, B2, C1, C2, C3, C4. Failed in
  practice: **A2 and A3** (naming the mechanisms was never the barrier - the brief describes each
  rule operationally and completely, so the concept never had to be recognised); **B1 and B2**
  (279 lines of environment is two `cat` calls, and the nine decisions were settled one file at a
  time); **C2** (running the shipped collector confirms nothing, but `run_prog.py` on a six-line
  hand program confirms every rule individually, which is the same thing); **C3** (dead - see
  below). Surviving with real force: C1 and C4 only.
- **Estimated solves out of 8 for the bundle as submitted:** 8.

### 2. Classification of the winning route

Five of the seven failure modes in `RAISE-DIFFICULTY.md` apply. Concretely:

- **The default plan was correct.** A generational collector with a nursery, a remembered set,
  ephemeron-style pairs and finalizer reprieve is squarely in the prior, and every rule the brief
  states *agrees* with what a careful implementation would do. There was no A1 anywhere in the
  bundle: not one rule contradicted the memorized default, so nothing had to be fought.
- **The instruction delivered the plan.** `instruction.md` was a 724-word specification whose
  paragraphs mapped one-to-one onto the five editable files. "Being kept so a finalizer can run
  is not surviving, so those do not age" *is* the fix to `col/age.py`, verbatim. Worse, the
  opening paragraph handed over the first defect **and its diagnosis**: "that last line should
  not be there: object 3 is unreachable and is only still around because its finalizer has not
  run, which is not the same as having survived". A symptom is fair; a worked cause is plan
  delivery. The brief also named the file holding the one fact it did withhold - "The remembered
  set is how it finds the second kind, and `/app/mem/rset.py` is where it comes from" - which
  turned the only B1 coupling in the task into a pointer.
- **The environment delivered the plan.** 279 lines of Python across 13 files. `DIFFICULTY.md`
  B1 rules on exactly this: "Spreading facts across seven files withholds nothing if the whole
  system is 500 lines - at that size 'distributed' just means 'adjacent'." Measured against the
  retained passing set the line count is fine (229-544); the **density** was not. The nearest
  passing neighbour, `focus-return-point`, is the same shape - a reach/keep/memory engine with
  four editable files - and carries 1727 instruction words over interacting rules: instance
  identity surviving id reuse, memories validated on entry rather than maintained on mutation,
  and a transactional mode that defers effects and answers them against the final tree. This task
  had one memory structure with one subtlety and no deferred mode at all.
- **The agent confirmed each step independently.** `run_prog.py` takes one program and prints
  every event, so each of the nine decisions was settled by a six-line program. All three agents
  did exactly that, and agent `aVVmqoi` wrote its expected output into the shell comment before
  running - per-axis confirmation before commit, which `DIFFICULTY.md` lists as leak 6.
- **The naive method was fast enough - inverted, which is worse.** The C3 boundary graded
  rescanning the pair table against indexing it by key. **No agent ever wrote the rescanning
  form**; indexing a table by its key is the default, not a discovered optimisation. Measured
  margins on the graded shape were 0.07 s, 0.25 s and 0.5 s against a 60 s limit - two orders of
  magnitude of slack. The gate was real and it was dead: it eliminated nobody.

Not applicable: the verifier accepted no false solution, and no route-around was used - the five
frozen entry points held.

**Diagnosis in one line.** Difficulty was sought in the *rules* and the rules are all stated, so
the task reduced to "make the code match the brief", which is mechanical. Nothing had to be
discovered, nothing interacted, and nothing failed late.

### 3. Candidate repairs

Three were drafted and attacked. All three keep the nine existing decisions, which are sound and
fenced from both sides; the question is only what is added.

**Candidate 1 - a second nursery generation (eden / survivor / old).** Every decision becomes
three-valued and the remembered set splits in two.
*Attacked and rejected.* It multiplies rules without making any of them interact - each stays
independently stated and independently testable, so it is B2 without the conjunction condition:
"six independently readable, independently verifiable rules are six easy tasks in a trenchcoat".
It is also precisely the sprawl of corner cases the contributor's earlier review rejected, and
restating cut rules was already recorded as the repair that fails the first review again.

**Candidate 2 - the finalizer keep-set fixed at queue time.** What a queued finalizer keeps is
decided by the collection that queued it and does not follow later mutation of the dead object's
fields.
*Strong on A1* - every implementation, including all three probe agents', walks from the queue
now - and it contradicts the remembered-set rule directly, so the two subsystems answer "trust
the record or re-read it?" oppositely.
*Attacked.* The record has to survive between collections and there is nowhere to put it:
`Heap.__slots__` has no room and no `__weakref__`, so it lands in module-level state in the
agent's own files, keyed by `id(h)`. That is awkward engineering rather than depth, and giving
`Heap` a slot to hold it would be an affordance that announces the mechanism. Held in reserve,
not selected.

**Candidate 3 - SELECTED: a name is not an object.** Object ids are reusable. Once an object has
been released its number is free, and a later `new` with that number allocates a different
object. Everything the runtime remembers about an object - the finalizer queue, the set of
finalizers that have run, weak referents, remembered-set entries - is about the object, not about
the number, and none of it transfers to the new occupant of that number.

Why it is the strongest against the measured failure:

- **A1, which the bundle entirely lacked.** Every collector in the training data, the shipped one,
  the reference, the sealed model and all three probe trajectories key on the integer id. The
  memorized default is specifically wrong and stays wrong at every one of the nine decisions.
- **A2.** Address reuse, generational references and the ABA hazard are all nameable; the brief
  states the behaviour and none of the vocabulary.
- **B1, restored to a real coupling.** The fact lives in `mem/heap.py`, `ops.py`, `mem/rset.py`
  and `mem/tables.py` - none of them editable - and its consequences must be derived for all five
  editable files. Reading the brief cannot supply it; reading one module cannot either.
- **B2, with the interaction condition met.** Identity is not a tenth rule bolted on, it is a
  second axis through all nine: whether a finalizer may run again, whether a weak reference
  retargets, whether a remembered entry is stale, and whether an object in the queue is still the
  object that was queued. Getting ageing right changes which objects get released, which changes
  which numbers come free, which changes what the next collection's memories mean.
- **C1, both fences.** Treating every reused number as a new object breaks `no-requeue` and
  `stays-clear`; treating it as the same object breaks every new case. The razor is tested from
  both sides.
- **C3 and C4, late and fatal.** Reuse only bites in programs that release and re-allocate a
  number, which the old generator never emitted and which no hand program an agent writes to
  check "a finalizer runs at most once" will contain. A collector that is wrong here prints
  correct records for every small program and fails the sealed set.

Second selected change, addressed at the dead C3 rather than at the semantics: the graded set
gains a family with a large surviving heap and many minor collections, where the per-collection
full-heap passes every agent actually wrote (`sorted(h.objs)` three times per collection) are
quadratic while the answers stay correct. Unlike the rescan gate this is the form the observed
trajectories wrote, so it eliminates the plan that actually won.

### 4. The repair, as built

Stage 2 onward were rebuilt. What changed in the environment, all of it outside the five editable
files:

- `mem/heap.py`: `Obj` carries `ser`, a serial that never repeats; `Heap` carries `stamp` and
  `young`.
- `ops.py`: `new` stamps the object and adds it to `young`; `runfin` records the finished
  finalizer under the object's serial; `pair` stamps the row with the serial of the object at its
  key; release takes the gone numbers out of `young`. Nothing sweeps the pair table any more.
- `mem/tables.py`: `Pair` replaces the bare tuple; `by_key` and `drop_gone` are gone with their
  last caller.
- `progs/churn.txt` is added, and the brief points at it for timing.
- The five shipped modules are wrong in all five files now, including on the two new axes.

The verifier: two more graded decisions, six more hand cases (`reuse-fin`, `reuse-key`,
`reuse-live`, `rset-rewrite`, `rset-fields`, `young-promote`), two more generated families
(`reuse`, `sweep`), and the worker returns a digest of each program rather than echoing its text,
so the execution limit prices the collector rather than JSON.

### 5. The repair, measured

Scaling boundary, on the real graded set of 410 programs, against the stated 60 second limit.
Every row below produces byte-identical records; only the cost differs:

| collector | graded set | verdict |
|---|---|---|
| reference: nursery-scoped passes, remembered set pruned | **1.8 s** | passes, 33x margin |
| remembered set pruned, passes over the whole heap | 86.1 s | fails |
| nursery-scoped passes, remembered set unpruned | > 400 s | fails |
| neither - **the form all three probe agents wrote** | > 400 s | fails |

On the single shipped sample the brief tells the agent to time, `progs/churn.txt`: 0.2 s for the
reference against 84.0 s for that same form, so one program alone overruns the whole budget and
the boundary is discoverable locally without the verifier.

Pruning is the load-bearing half: scoping the passes to the nursery without it still fails. The
rule that makes it work is not obvious from the brief - two remembered-set entries that share a
source and a field ask the same question, because the recorded value is never what is read - and
it is what `rset-fields` fences from the over-eager side.

Wrong readings, each built as the reference with one declared override, measured over 120 shaped
programs and 32 hand cases. `wide` and `sweep` are excluded from that population: they are
resource families and semantically ordinary, so counting them would inflate every share with
programs that are not about the reading. All twelve are separated, and every one is named by an
enumerated case rather than by bad luck:

| reading | moves | named by |
|---|---|---|
| `age-held` | 67.5% | `held-no-age` |
| `young-stale` | 48.3% | `old-safe` |
| `release-old` | 33.3% | `old-safe` |
| `no-rset` | 14.2% | `rset-deep` |
| `trust-rset` | 11.7% | `rset-stale` |
| `queue-late` | 10.0% | `queue-first` |
| `id-pair` | 6.7% | `reuse-key` |
| `id-done` | 5.8% | `reuse-fin` |
| `no-promote-rset` | 5.0% | `rset-promote` |
| `over-prune` | 4.2% | `rset-fields` |
| `wipe-old` | 3.3% | `weak-old` |
| `old-key-unready` | 0.8% | `old-key` |

The two identity readings are the quiet ones by design: they move 5-6% of a population shaped to
provoke them and nothing at all on the six-line programs an agent writes to check its own work.
Under all-or-nothing grading a quiet reading still scores 0.

Two tooling defects were found and fixed while measuring, both of the class this repository has
already recorded once:

- `authoring/.../trial.py` and `authoring/.../cheat_report.py` never ran `tests/prepare.py`, which
  the bundle gained when program generation moved to the trusted side. `trial.py` scored the
  reference 0; `cheat_report.py` was worse - with no programs the worker failed for every cheat,
  every assertion in the grader fired, and each cheat's declared layer was duly found among them.
  Twenty clean rows, none of which meant anything. Both now run the preparation stage, and
  `cheat_report.py` runs the reference through its own harness first and refuses to report at all
  unless it scores 1.
- `authoring/.../decisions.py` unpacked pair rows as 2-tuples and crashed `onelinecheck`, the
  tool whose whole job is the leak audit.

## Decisions and their reasons

- Rebuilt on the house shape after the quality review failed `difficult` twice. The previous
  version was 107 lines of environment with one editable file and shipped no engine; every
  retained passing task is 229-544 lines with 1-7 editable files and ships a working-but-wrong
  engine. The earlier removal of the shipped collector was an over-correction on my part.
- The remembered set stores the written value, not just the location. Storing only (source,
  field) made "trust the record" inexpressible, so the staleness reading could not be separated;
  with the value stored it moves 12% of a shaped population and is named by `rset-stale`.
- Terse identifiers kept but widened from the previous version - `ob` and `fl` became `objs` and
  `flds` - after the review called the naming friction rather than expertise.
- The scaling boundary survives the rebuild unchanged and is stated in the brief with the scale.

## Validation status

Re-run in full after the 2026-09-07 rebuild.

| Check | Status | Notes |
|---|---|---|
| Reference vs sealed model | pass | 230 programs, two PYTHONHASHSEED values - the pruning iterates a set, and the output does not depend on that order |
| Oracle scores 1 | pass | host emulation, 410 programs |
| nop scores 0 | pass | the shipped tree is wrong in all five modules |
| Correct variants score 1 | pass | `alt` (level-frontier, rewritten for this contract, 0.055 similarity), `mirror` (74 identifier substitutions) |
| Cheats score 0 | pass | 20 of 23 run on the host; each caught by its own declared layer |
| Cheats needing a container | not run | `reward-daemon` needs fork, `privilege-probe` a second uid, `read-sealed-model` a `/tests` that uid cannot read |
| Scaling boundary | measured | 1.8 s reference against 86.1 s and > 400 s for the two half-fixes, 60 s limit |
| Wrong readings separated | pass | 12 of 12, each named by an enumerated hand case |
| Short-rule leak audit | pass | `onelinecheck`: no graded decision reproduced at depth <= 2, with the new fields offered |
| `preflight` | pass | 0 errors; the 10 warnings are the frozen entry points, which are called by `ops.py` |
| `imagecheck` | pass | 18 files, workdir /app, reference runs all five shipped programs |
| `extraneouscheck` / `deadfieldcheck` / `catcheck` / `hintcheck` / `solvecheck` | pass | clean |
| Instruction prose vs a passing bundle | pass | `textcheck` against `focus-return-point`: at least as irregular on every axis |
| `docker_trial --all` / `--variants` | not run | Docker is not installed on this machine |
| External easiness probe | **not run** | no probe access from here - the recovery does not close without it |

## Open questions and next steps

1. **The recovery is open until the external probe passes.** `RAISE-DIFFICULTY.md` section 6 is
   explicit that a task is never labelled ready on predicted difficulty alone, and the probe
   cannot be run from this machine. Everything in "The repair, measured" is preparation for that
   run, not a substitute for it. If it fails again, section 1 says to diagnose the new winning
   route rather than stack another rule on this one.
2. **Decision 10 is a verifier contract change and wants the contributor's explicit approval.**
   It changes what "correct" means. The recovery procedure requires re-freezing at Stage 2, which
   is what was done, but the sign-off is a person's.
3. The three container-only cheats and the 60 second limit stay unverified in a container until
   Docker exists. The handover must say so, and one of them is worth saying out loud:
   `read-sealed-model` imports the sealed model and forges every record from it, and it **scores
   1** on this host, where `/tests` is readable and on the path. Nothing in the contract stops
   it - only `chmod -R go-rwx /tests` plus the drop to uid 1002 does. That isolation is
   load-bearing and it is exactly what cannot be tested here.
4. The self-probe is again recorded as **not run**: the author of the repair cannot cold-solve it,
   and a self-probe reported as passed by a contaminated author is worse than none. The reading
   separations, the scaling measurements and the leak audit stand in its place.
5. Residual risk on the resource gate, stated plainly: the nearest failing variant is at 86.1 s
   against a 60 s limit, only 1.4x over. On a machine appreciably faster than this one a
   submission that prunes the remembered set but still passes over the whole heap could come in
   under the limit. That is a weaker solution passing, not a correct one failing - the reference
   sits at 1.8 s with 33x of headroom, and the plan the probe agents actually wrote is past 400 s.
