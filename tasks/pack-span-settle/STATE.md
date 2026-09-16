# Task state

Working memory for this task. The assistant updates it after every stage. Assume the next
session starts with no memory of this one - anything not written here is lost.

## Current stage

`Stage 7 - Pre-flight and packaging`

## Assistant's assigned role

You are a data-pipeline engineer on a language-model pretraining team. You own the part of the
data path that turns tokenized records into fixed-width training windows, decides which
positions carry loss, and hands the trainer its per-step normalisation. You have spent your
time on packed-sequence pipelines, boundary masking, document-level reweighting and the
accounting that has to survive a record being cut across windows and steps.

## Source repository (repo-based tasks only)

- Repo URL: none - idea-based task
- Task shape chosen: not applicable, no repository vendored
- Contributor's relationship to it: not applicable
- License, and why vendoring it is permitted: not applicable
- Pinned commit vendored into environment/app_src/: not applicable
- Load-bearing couplings found during research: not applicable
- Identifier degradation done? Not applicable; the tree is authored, and its identifiers are
  written in a legacy register from the start
- Proper-noun sweep done? Not applicable; nothing is vendored, and no framework, product or
  project name appears anywhere in the agent-facing tree
- Upstream-diff check: not applicable

## Task summary

`/app` is the packing half of a pretraining data pipeline. A shard is a text file of ops: `rec`
declares a tokenized record with a length and a weight, `width` sets the window width from the
next window on, `span` sets how many windows an optimizer step holds from the next step on, and
`seal` ends the shard. `/app/run_shard.py` replays a shard and prints one line for each record
that settles, each record that is passed over, and each step that settles. The engine has been
wrong since the pipeline was rewritten: it cuts records so that a piece can be one token long,
it divides a record's weight as if the record had never been cut, it prints a record's line at
the moment its first piece is placed, and it settles a step the moment its windows run out. The
agent repairs six modules under `/app/pipe/` so the trace is right, and so both wide shards
finish inside the stated limit.

## Why it is hard

The load-bearing quantity is a record's divisor: its weight is spread over the scored positions
it actually has, and a record loses one scored position for every piece the layout cuts it into.
The divisor is therefore a property of the layout, not of the record, and is unknown until the
record's last piece is placed. That one requirement invalidates the shipped streaming emitter,
the shipped step-settlement rule, and the natural reading of every other rule in the brief.

- Expert time estimate: 10 hours
- Why a frontier agent cannot one-shot the plan (the strategic answer - required): every rule in
  the brief reads as a statement about token positions, and the shipped engine is built that way,
  so the first plan is to repair the position arrays in place. Two findings break it: the divisor
  cannot be known while the record is in flight, which moves the emission of a record's line and
  blocks every step that record touches, and the wide shards declare two billion tokens against
  sixty seconds and 2048 MB, so the position arrays cannot be built at all and every intermediate
  value has to be re-derived as arithmetic over pieces.
- Tactics making that true (prongs A, B and C of docs/DIFFICULTY.md): A1, A2, B2, C1, C3 and C4,
  with the route-around guard. A1 the retrievable packing convention resets position ids per sample and
  normalises a document by its own length, both of which are wrong here; A2 no mechanism is
  named, so the recognition that the divisor belongs to the layout has to be made; B2 the
  two-token floor, the tail that may not be left at one, the short close, the refusal of a
  one-token record, carried position ids, the settlement order and exact fractions all hold at
  once and each moves where the next record's pieces fall; C1 both sides are fenced, so an
  implementation that opens a fresh window per record or holds every step to the end of the shard
  fails the ordinary shards; C3 the wide shards kill every per-position representation, which is
  the one the shipped engine uses; C4 traces are compared line for line over hand shards and over
  generated shards drawn from a seed the submission never saw.
- Assistant's attack on the plan (its first plan, and where that plan is wrong): my first plan is
  to run the shipped reader on the small shard, diff it against the one corrected line in the
  brief, and repair the engine where it stands - cut so no piece is one token, divide by length
  less one, count scored positions off the arrays already there, close a step at its window count.
  That plan is wrong in two places that matter. Dividing by length less one is wrong for every
  record the layout cut, and I would not see it on a shard whose records all fit in one window.
  Printing a record when its first piece lands and settling a step at its window count are both
  wrong for the same reason, and neither shows up until a record is carried. I could not commit
  to the settlement structure without first working out what a divisor depends on, and I would
  keep the position arrays until a wide shard showed me they cannot exist.
- Estimated solves out of 8 (design for 1, the hard edge; the realized rate drifts up): 2 out of 8, designed at the hard edge of the 1 to 3 band
- Difficulty record score (tools/difficultycheck.py on authoring/<slug>/difficulty.toml, before
  Stage 2; every attempt's score and what changed, until it reaches the band in
  docs/DIFFICULTY-SCORE.md): first and only attempt scored 100/100 on 2026-09-16, in the 95-100
  band with no hard stop. The one warning is `gate.measured = false`, which stands until the
  naive and expert timings are actually run (see Validation status).
- Difficulty score anchor (50 at first complete submission, approved by contributor): not yet set
- Score history (date, score, what moved, and any pipeline re-anchor): 2026-09-16, 100, initial
  record
- Leak audit (docs/DIFFICULTY.md): for each mechanism, what in the bundle could let an agent
  discover, name or verify it without reasoning? Answer must be "nothing". A record carries only
  its id, length and weight, so no scored count or divisor is stored anywhere. The trace carries
  records and steps only - no window line, no offset, no piece listing - so the layout cannot be
  read off any shipped output. No expected trace ships beside any shard. The frozen emitter is
  handed a numerator and a denominator and prints them, and the frozen fraction primitive reduces
  a pair it is given, so neither computes a divisor. No shipped function answers how many windows
  a record spans.
- Expert path, described step by step (the harder the aim, the more this guard must hold): run
  the shipped reader on every shard and read the trace against the brief; separate what the reader
  and the emitter are frozen to do from what the six editable modules decide; derive the piece
  rule from the two-token floor and check the room and remainder corners by hand; move a record's
  line to the moment its last piece is placed and carry the piece count with it; hold each step in
  a ledger keyed by the records with pieces still in flight and settle it when the last of them
  ends; compute the weight as one exact fraction per record and accumulate each step's sum from
  the pieces inside it; replace the per-position arrays with per-piece arithmetic once the wide
  shard shows the representation cannot be built; time both wide shards under the limit and
  re-check the small shards.
- Originality check: searched 2026-09-16 for the mechanism and for the task. The closest public
  material is the torchtune `PackedDataset` documentation, `Efficient Sequence Packing without
  Cross-contamination` (arXiv 2107.02027), `Enhancing Training Efficiency Using Packing with
  Flash Attention` (arXiv 2407.09105) and the packing-and-token-weighting write-ups. They cover
  boundary masking, per-document normalisation, and whether a sample is split or carried whole;
  none of them covers a divisor that the cut decides, a two-token floor, a short close, or a
  settlement order. Searching for the task itself returns nothing.

## Instruction contract (docs/INSTRUCTION-CONTRACT.md, read before anything else)

Every graded assertion traces to a sentence in the instruction. Walk the tests, the sealed model
and test.sh line by line into authoring/<slug>/trace.md, start it with
`python tools/tracecheck.py <slug> --skeleton`, and keep `python tools/tracecheck.py <slug>` clean.
`preflight.py` errors while any line below is unanswered.

- Instruction trace (authoring/<slug>/trace.md; rows walked, NOT STATED left, tracecheck result): 48 graded-assertion rows walked, no row left NOT STATED, tracecheck clean.
  `authoring/pack-span-settle/trace.md`. Forty-eight graded-assertion rows walked - four test
  functions, twenty-nine enumerated shards, six collected artifacts, the 60 s clock and sixteen
  rules of the sealed model split out with their line ranges - plus twenty-three reading rows,
  four shortcut rows and three tolerance rows. No row was left NOT STATED: the two the walk
  found unstated were fixed in the instruction rather than left (see the cold-reader line
  below). `python tools/tracecheck.py pack-span-settle` is clean.
- Identifiability (readings enumerated, which survived the published evidence, what separated them): 25 enumerated, 23 separated by the case named for the rule, 1 real hole found and closed.
  Twenty-five readings were written down and run. Twenty-three are separated, and
  `authoring/pack-span-settle/cheat_report.py` asserts each is separated by the enumerated case
  named for its rule, not merely by whichever case comes first - `cut-always-back` was caught
  only by that check, since `carry-two` cannot see where a cut fell. Two did not survive
  measurement and were not kept on paper: settling a record by the step it started in is
  semantically equivalent to settling it by the step it ended in, because only one record is
  ever in flight, so it became `variants/settle-by-first` and must score 1; and a step-back rule
  without the two token floor cannot terminate, so it is not a reading a solver can hold. One
  survivor of the published evidence was a real hole - printing a whole fraction as `3` rather
  than `3/1`, which no published example decided - and the instruction now states it.
- Shortcut strategies scored (nop, constant, positional, replayed example; score and cases matched): all four score 0, and the fraction of cases each matches is recorded below.
  The nop scores 0 and matches 1 of the 29 enumerated shards (`seal-empty` alone).
  The constant strategy is `cheat-sum-positions`, a step reporting its position count where its
  weight belongs: 0. The positional strategies are `cheat-first-at-op` (always the window open
  when the record arrived) and `cheat-div-first-step` (always the first step's share): both 0.
  The replayed answer key is `cheat-forge-truth`, which reproduces all 29 enumerated shards
  byte for byte and prints nothing at all on the 366 generated ones: 0.
- Independent implementation behind every tolerance and limit (path, measured headroom): four written apart from the reference, about 30x headroom on the clock and 34x on memory.
  There is no numeric tolerance - every graded quantity is an integer or an exact rational in lowest
  terms. The 60 s clock and the 2048 MB cap are validated against four implementations written
  apart from the reference: `tests/seal/model.py` (1.10 s over the whole graded set) and
  `authoring/pack-span-settle/variants/own-tally`, `variants/rational` and
  `variants/settle-by-first`, all three of which score 1 through the real verifier. The
  reference settles all 395 graded shards in 2.02 s at 59 MB, so the headroom is about 30x on
  the clock and 34x on memory. The gate is measured on the other side too: `cheat-slow-positions`
  is exactly correct on all 29 enumerated shards and takes 248 s on one deep shard, and
  `cheat-slow-steps` is exactly correct and takes 36 s on each of three wide shards.
- Undecided decisions from the cold-reader pass (author-run or fresh session; sentence or example added for each): two found, two fixed in the instruction; the pass was author-run.
  Put mechanically - every printed token, every model
  branch that can move it, and the four clusters put to each. It is recorded as author-run
  rather than cold: this session wrote the model and cannot un-know it. Two decisions came back
  unsettled and both were fixed rather than argued. A fraction that reduces to a whole number
  had no published case, so `lay b 1 1 3 1/1` was indistinguishable from `lay b 1 1 3 3`; the
  instruction now says a whole fraction keeps its denominator. And nothing said the width, span
  and floor arrive before the first record, which a shard with a record ahead of them would have
  left undefined; the instruction now says they do.

## Verifier contract - FROZEN after Stage 2

Once agreed, this does not change without the contributor's explicit approval. Frozen 2026-09-16.

- Artifacts the agent produces: the six editable modules, taken from the agent at their original
  absolute paths - `/app/pipe/win.py`, `/app/pipe/cut.py`, `/app/pipe/lay.py`,
  `/app/pipe/hold.py`, `/app/pipe/step.py`, `/app/pipe/weigh.py`. The verifier reads nothing else
  from the agent's container.
- What is checked: the six files are laid over the verifier's own pristine copy of `/app`, and
  `run_shard.py` is run on every graded shard. Its stdout must equal the sealed model's output
  byte for byte, for every shard, with a non-zero exit or any stderr treated as a failure. One
  wrong line anywhere scores 0.
- Tolerances: none. Every graded quantity is an integer or an exact fraction printed as
  `<numerator>/<denominator>` in lowest terms. The only limits are the wall clock on the whole
  graded run and the memory cap the task declares, both stated in the instruction.
- Ground truth, and where it lives: `tests/seal/gt.json` holds the frozen traces of the
  enumerated shards, built before the grading file was written; `tests/seal/model.py` is the
  sealed model, written independently of `solution/`, and the grader asserts it still reproduces
  `gt.json` exactly before grading anything. Generated shards are produced inside the verifier
  from a seed drawn after the agent's container is gone. `tests/seal/` is mode 700 and owned by
  root, so code running inside the verifier cannot read it.

### The graded semantics, in full (the frozen contract)

Windows are numbered from 1 in the order they are opened, steps from 1. `width` sets the width of
windows opened from then on; `span` sets the number of windows a step holds from the next step
opened. Records are laid in file order into the open window and the windows after it.

1. A record one token long has no scored position and is passed over: it is not laid, consumes no
   room, and prints `skip <id>`.
2. The piece placed in the open window is the longest run of at least two tokens that fits in the
   room left and leaves the record either finished or with at least two tokens still to place.
   When no such run fits, the window is closed with the room left unused and the next window is
   opened.
3. A window is closed when it is full, when rule 2 leaves it unusable, and at `seal`.
4. A position is scored when the next position lies in the same window and belongs to the same
   record. A piece of length `t` therefore carries `t - 1` scored positions, and a record of
   length `L` cut into `p` pieces carries `L - p`.
5. A record's weight `w` is spread equally over its scored positions: every one of them carries
   `w / (L - p)`, printed in lowest terms.
6. A step holds `span` windows. A step settles when it has been closed and every record with a
   piece inside it has been laid in full.
7. A record prints `lay <id> <first window> <pieces> <scored> <num>/<den>` when its last piece is
   placed. A step prints `step <index> <windows> <positions> <num>/<den>` when it settles, where
   `positions` is the number of scored positions in the step and `num/den` is the sum of their
   weights in lowest terms.
8. When one record's last piece settles several steps at once, the record's line is printed first
   and the step lines follow in index order.
9. `seal` closes the open window and the open step, and settles everything still open.

## Decisions and their reasons

- Category was ML / Training and is now Software / Data engineering. The story is a pretraining
  data path and stays so, but `tools/catcheck.py` measured what the reviewer measures: the
  environment carries no ML machinery at all (0 hits) while the prose asserted it 57 times, which
  is exactly the finding that rejected `alias-settle-report` on 2026-09-04. The skill the graded
  work exercises is data-pipeline engineering - laying a record stream into fixed windows,
  deferring a settlement until a decision downstream of it is made, and exact rational
  accounting - so the label names that. Under Software the same check reads 3 environment hits
  against 28 in the prose and passes. Adding tokenizer or tensor machinery to earn the ML label
  would have been scenery, which is the anti-pattern rather than the repair.
- The floor, and with it the dropped step, was added after the first contract draft. Without it a
  record's divisor is a pure property of the layout and is known the moment its last piece lands;
  with it the divisor waits on a decision taken when the last step the record touches closes,
  which is what defers a record's line across several later ops and gives the settlement order
  its teeth.
- Records may be carried across a step boundary. The alternative - never splitting a record across
  a step - was rejected because it would make every step settle at its own close and destroy the
  settlement order, which is the deepest of the graded decisions.
- The step's weight sum is graded as an exact fraction rather than a float, so the verifier grades
  the contract rather than a summation order.
- The wide shards kill the per-position family only. Per-piece and closed-form implementations
  both pass with headroom, so the gate bans a representation rather than a technique.

## Validation status

| Check | Status | Notes |
|---|---|---|
| Agent image builds | not run | Docker daemon unavailable in this container; `tools/imagecheck.py` stands in |
| No answer leaked into agent image | pass | `extraneouscheck`, `leakcheck`, and a read of the tree: no gt, no model, no expected trace, no conversion table |
| `harbor run -a oracle` = 1 | not run | harbor not installed here; host emulation scores 1 |
| `harbor run -a nop` = 0 | not run | host emulation scores 0 |
| Cheats all score 0 | pass (host emulation) | 35 cheats through `authoring/pack-span-settle/host_trial.py --all` |
| Cheat layer asserted | pass | `cheat_report.py`: each reading caught by the case named for its rule |
| Correct variants score 1 | pass (host emulation) | three, through the real verifier |
| `tracecheck.py` (every graded assertion traced) | pass | clean |
| `preflight.py` | pass | |
| `harbor check` rubric | not run | no API key and harbor not installed |
| Resource gate measured | pass | 248 s on one deep shard against a 60 s clock; reference 2.02 s on all 395 |

## Stage 7 re-attack, against the finished bundle

Read cold, the brief hands over the rule list and withholds the structure. My own first plan
against the built tree is still: run the shipped reader on `tiny.txt`, read the six modules,
repair the cut, the floor comparison and the same-record scoring where they stand, then the
divisor, then the settlement. Four of those are one-line repairs and the brief states each. What
the brief cannot hand over is that the divisor waits on a decision taken after the record's last
piece landed, which invalidates the shipped emitter rather than patching it; that the window a
record reports only moves once the cut is right, so the `first` defect is invisible until then;
and that the representation the whole engine is built on cannot run at the stated size.

Honest estimate, updated: 3 of 8, against a design target of 2. It moved up by one because every
rule is stated plainly and a careful solver can reason each out on its own; what holds it inside
the band is the conjunction, the deferred settlement, and the measured scale boundary, not any
one rule. Below 7 and above 0 on both the design and the built tree.

## Quality self-review (docs/QUALITY-REVIEW.md, criterion by criterion)

- Instruction and verifier agree both ways: `authoring/pack-span-settle/trace.md` walks all 48
  graded sites to a quoted sentence and `tracecheck` is clean; every sentence of the brief has a
  case, which `cheat_report.py` proves by naming the case that catches each wrong reading.
- Every collected path is named in the brief with its absolute path, and "Nothing else" states
  that a seventh file is never taken.
- Boundaries settled in the text: at least two tokens, at least `floor` positions, at least four
  wide, the whole fraction keeping its denominator, and the three settings reaching only what is
  opened after them. The last two were found by the cold-reader pass and written rather than left.
- No two readings that reproduce the published evidence disagree on the graded set: measured by
  `readingcheck` and `cheat_report.py`.
- Prose: no run of same-structured sentences; openers vary across the rule paragraphs.
  `tools/textcheck.py` still reports the cadence as more even than the retained briefs
  (burstiness 0.750 against 0.79-0.92) and counts three dash asides, which are the arithmetic
  `t - 1` and `n - p`; the remaining gap was not worth buying with a run-on sentence in a
  contract, and it is recorded here as a residual risk rather than fixed.
- Verifier rigor: the grader never runs agent code, reads the worker's report defensively, and
  asserts the sealed model still reproduces the frozen answers before grading anything. Test
  code carries a docstring naming each graded decision.
- Determinism: the population varies with the nonce, the verdict does not - the model defines
  correct for any seed, and the reference and three variants score 1 on every run.
- Environment hygiene: the image copies `app_src/` only; no comments, docstrings or `.md` files
  anywhere in the agent-facing tree; every path named in the brief exists and is spelled the
  same; pytest pinned `==`, no apt pin.
- Solution quality: `solve.sh` installs the reference modules, which the verifier then executes;
  nothing is written as an answer.
- Anti-cheating: no ground truth, model, expected trace or answer table anywhere the agent can
  read; `forgecheck` confirms the answer-key carrier is present and scores 0.
- Metadata: `Software` / `Data engineering` with five specific tags, none restating either; the
  legacy naming register is stated as a design choice in `difficulty_explanation`; ten hours is
  consistent with a six-module repair plus a representation rebuild.
- Known risk carried forward: `environment/Dockerfile` is byte-identical to a retained bundle's
  (`simcheck` 1.000). It is six lines, every one of which this task needs, and differentiating it
  would be decoration rather than engineering.

## Open questions and next steps

No open questions. Docker and harbor are unavailable in this container, so the oracle, the nop,
the cheats and the variants were run through the host emulation in
`authoring/pack-span-settle/host_trial.py`, which runs `tests/test.sh` verbatim as root and
reproduces the privilege drop, the locked reward channel, the session and clock around the
worker, the survivor reap and the reward written last. It does not reproduce an image build or
filesystem isolation between the two stages. Container evidence is container evidence, and this
is not it: the platform's own oracle and nop runs are still owed.
