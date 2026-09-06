# Task state

Working memory for `batch-admit-reclaim`. It never ships in the zip.

## Current stage

`Stage 7 - pre-flight and packaging`.

## Assistant's assigned role

The contributor confirmed ML / Inference and left the rest to the operating manual, so the
role was taken from the work rather than dictated: a senior inference-serving engineer who
owns the scheduler and the paged key-value block manager of a serving stack, and who has
spent time on continuous batching, prefix reuse, preemption under memory pressure and the
throughput collapses that follow from getting any of the three slightly wrong.

## Source repository

- Repo URL: none - idea-based task. No repository was offered, so no shape choice was owed.
- The design is authored from the incident class rather than from any codebase, and nothing
  is vendored.

## Task summary

The tree under `/app` is a serving engine replaying recorded request traces against a fixed
pool of key-value blocks. The agent supplies the scheduling policy in four files. What is
graded is the timeline: per request, the step it came in and the token it started from, the
steps it was put out and how many tokens it had, the steps it came back and where it started
again, and the step it finished. The engine emits those lines itself, from a file the agent
cannot edit.

## Why it is hard

The shipped engine has a coherent and specifically wrong idea of what a step costs: it asks
the pool how much room it has and compares that against the blocks a newcomer is missing.

- Expert time estimate: 8 hours
- Why a frontier agent cannot one-shot the plan (the strategic answer): the entry decision is
  settled before the step decodes and applied after it, so it can only be answered by playing
  the rest of the step out - the merges a filling block performs, the releases a finisher
  makes, and the reclaims the entry itself forces - and the natural implementation of that,
  once found, treats those releases as room recovered, which is the second and opposite
  discovery. The first plan is arithmetic over the pool as it stands; it is wrong on 73 per
  cent of generated traces, and the repair that makes it work is wrong again on 16 and 65 per
  cent.
- Tactics making that true (docs/DIFFICULTY.md): A1, A2, B2, C1, C2, C4. A1 (the prior - an admission check that
  compares a need against free space is what every engine ships and what every write-up
  describes), A2 (the two discoveries are described operationally and never named), B2 (ten
  stated rules that interact: block identity through the prefix, merge on fill, release
  against eviction, last-use order, the part block, the entry condition, arrival order, the
  put-out rule, the empty-pool floor, the allowance), C1 (both fences graded - eleven
  enumerated traces exist to protect ordinary behaviour so that turning cautious fails), C2
  (no oracle: the tokens each request emits are fixed by the recorded trace and identical
  under every reading, so running it two ways diffs nothing and no expected output ships),
  C4 (exact, all-or-nothing, 29 enumerated traces plus 300 built from a nonce drawn after the
  agent stops).
- Assistant's attack on the plan: my first plan was a refcounted block table, a prefix hash
  per full block, an LRU free queue, admit in arrival order while there is room, decode the
  running set, preempt the latest arrival on failure. That plan is wrong in two places that
  matter - it counts a release as room recovered on the step it happens, and it settles the
  entry question against the pool at the top of the step rather than against the pool the
  step will leave behind. Neither shows up in testing, because the engine prints a plausible
  timeline under both.
- Estimated solves out of 8: 2 of 8, designed at the hard edge and allowed to drift up
- Difficulty score anchor: not yet submitted, so no anchor.
- Score history: none yet.
- Leak audit: run as a procedure, not as a feeling. For each graded decision I tried to
  reproduce the answer from shipped files with a join, a sort or a field comparison, and for
  every pair of exposed numeric quantities asked whether a-b, a==b or len(a)==len(b)
  witnesses the hidden thing. `tools/onelinecheck.py` reports no exact rule at depth <= 2 for
  any of the three graded questions over the primitives the pool exposes (cap, occupancy,
  loose count, decoders, allowance left, blocks held, blocks missing, part block, joiners).
  `tools/deadfieldcheck.py` reports no field written and never read. There is no manifest, no
  self-labelling data, no shipped validator, and no expected output anywhere in the tree. The
  three shipped traces are inputs only. The engine's own preempt-on-demand valve was added
  deliberately so that a wrong policy produces a plausible timeline rather than a crash: an
  engine that faults on a wrong policy is a confirmation signal, and the earlier build had
  one - 16 of 120 traces tore under one misreading before the valve went in, and none do now.
- Expert path, described step by step: read `eng/step.py` and see that the entry question is
  asked before the decodes and applied after them; read `eng/pool.py` and see that `give`
  only drops a reference while `sweep` is the separate act that removes a block; hand-trace
  one preemption and notice that the blocks it releases are the freshest in the pool and
  therefore the last to be reclaimed; write the entry question as a play-out of the rest of
  the step on a copy of the pool; make the reclaim order last-use with the older block first
  on a tie; make the starting token a query against the pool at the moment the request comes
  back, stopping at the first block the pool no longer has; leave the arrival order and the
  choice of victim alone. Then the corners: a lone request that is never put out, a prompt
  that ends on a block edge, a prompt shorter than a block, a request too large for the
  allowance.
- Originality check: searched for public write-ups of the specific rule set. Paged key-value
  caching, continuous batching and preemption are all documented in open serving engines, and
  that is the point of A1: the retrieved design supplies the vocabulary and the wrong
  defaults. The combination graded here - the entry condition stated against the end of the
  step, release separated from eviction, and the starting token decided by what the reclaim
  left behind - is not the design of any engine I could find, and the timeline artifact
  exists nowhere.

## Verifier contract - FROZEN after Stage 2

- Artifacts the agent produces: `/app/eng/fit.py`, `/app/eng/room.py`, `/app/eng/back.py`,
  `/app/eng/pick.py`. Three of the four ship wrong; `pick.py` ships correct.
- What is checked: the timeline, exactly and in order, on 29 enumerated traces against
  `tests/gt.json` and on 300 nonce-generated traces against `tests/oracle.py`. Plus four
  attestations: the executed tree outside the four artifacts is byte-identical to the
  pristine copy (with the file count asserted first), every sealed engine function
  fingerprints to what the pristine sources compile to at import and at the end of each
  trace, the interpreter's own count of entries into the emitter equals the number of lines
  and the instrumentation was still armed, and the report carries the run nonce.
- Real work versus implementation choice: the timeline is real work - two correct
  implementations agree on it by construction, and five do. Everything else is implementation
  choice and is not graded: how the entry question is answered, what is cached between steps,
  which of the four files holds the reasoning, and how many times each policy hook is
  entered. Hook entry counts are compared only as floors across the whole run.
- Tolerances: none. Exact equality, all or nothing.
- Ground truth, and where it lives: `tests/gt.json`, root-only in the verifier image,
  produced by `tests/oracle.py` rather than by the tree.
- Route-around guard: `artifacts` lists only the four policy files. The engine, the pool, the
  emitter, the parser and the traces are frozen and compared after the run.

## Decisions and their reasons

- Category ML / Inference, confirmed by the contributor. The environment is a serving engine
  and `tools/catcheck.py` measures the vocabulary in the tree rather than in the prose.
- The graded artifact was changed during review from the block event log to the per-request
  timeline. Grading every allocate, merge, release and reclaim was process grading: block
  identities are the machine's business, and every misreading still moves the timeline.
- The step order was changed during the build. Entries were originally applied before the
  decodes, which let a wrong policy livelock (admit, put out, admit again, with nothing ever
  decoding) and tore 16 of 120 traces. Deciding entries at the top of the step and applying
  them after the decodes guarantees progress and is what makes the entry question
  forward-looking.
- No resource boundary. The reference plays 300 traces in 0.5 seconds and the sealed model in
  0.3, so there is no naive-but-correct implementation to gate on time; `guard-mark-unwind`
  and `focus-return-point` both passed without one. C3 stays available as the repair lever if
  the probe comes back too easy.

## Measured, for calibration

- Readings, share of 150 generated traces each misreading moves: pool asked instead of played
  73%, only the newcomer asked about 67%, pool gives up what came free last 65%, shortest
  waiting request first 86%, first to arrive put out 77%, request keeps the blocks it had
  97%, starts over from nothing 97%, only a first-time request shares 64%, part block
  forgotten 47%, hole stepped over 45%, finishers counted as room 16%, tail give-back missed
  13%, oldest block made 11%. Nothing below the one-tenth line.
- The shipped tree agrees with the reference on 3 of 150 generated traces.
- Reference and sealed model agree on 29 enumerated and 400 generated traces.
- Five behaviour-preserving permutations of the reference produce byte-identical timelines on
  150 traces (`orderfuzz.py`), which is the uniqueness evidence.
- 22 cheats score 0. Five correct variants score 1.
- The answer-key cheat is right on all 29 enumerated traces and scores 0.

## What remains

- The three-agent probe is not run here; the cold self-solve in `probes/` stands in for it.
- `harbor check` needs an API key that is not present in this sandbox.
