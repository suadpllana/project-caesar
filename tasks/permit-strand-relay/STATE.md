# permit-strand-relay

Working notes. This file never ships; `package.py` drops it.

## Why it is hard

- Expert time estimate: 8 hours
- Why a frontier agent cannot one-shot the plan (the strategic answer): the retrieved receiver-window plan is right about the shape and specifically wrong twice here, and the two defects are entangled, so neither can be repaired before the other and the natural implementation of each is what breaks the other.
- Tactics making that true (docs/DIFFICULTY.md): A1 poisons the memorised receiver-window plan, B2 stacks twelve stated rules whose interactions are the work, C1 fences nine of the twenty-four enumerated streams as cases the shipped tree already passes, C2 removes the oracle by shipping no producer simulator, so running it returns no verdict on the obligation.
- Assistant's attack on the plan (its first plan, and where that plan is wrong): charge both levels on arrival, return both when the consumer draws, hold a raise under the threshold, flush when the remaining ceiling drops below a minimum batch - about ninety minutes, and wrong on the link's drained total, on the obligation's argument, on the teardown window and on generation-scoped belief across a reopen.
- Estimated solves out of 8 (design for 1, the hard edge): 2 of 8 is the design target here.
- Leak audit (docs/DIFFICULTY.md): run as a procedure, not a feeling. `gen` was written and never read and is deleted; liveness now reads `shut`, which the late window needs anyway. `Plan.name` was dead and is deleted. Every pair of exposed numeric fields was tested for a witness: `lsnt - ltkn - sum(held)` does equal the shed total, so that identity ships as the `ok-identity` variant and scores 1, and the fix stays a real derivation rather than a lookup. Nothing witnesses the published history, because no field records it. No unused imports, no manifest, no self-labelling data, no shipped validator.
- Expert path, described step by step: see solution_explanation in `task.toml`.
- Originality check: receiver-side windowing is documented in HTTP/2 and QUIC, and the deviations are stated - receiver-initiated teardown so there is no final-size signal, absolute generation-scoped ceilings, and a stated learning delay. The obligation-from-emitted-history half is in neither specification.

## The long version

The retrieved plan for receiver-side flow control is right about the shape and wrong here
twice, and the two are entangled. Permit is returned when the consumer draws rows off; an
arrival is judged against the ceiling the receiver currently holds; a raise is held back
until it clears a threshold. All three are what the shipped tree does and all three are
what a page on windowed flow control describes.

The first thing that must be derived is that the link finishes with rows nobody draws. A
feed can be torn down with rows still parked, those rows are discarded, and they were
charged to the link when they landed, so a ceiling built on what was drawn can never
account for them. The second is that the obligation to publish below the threshold is a
question about what the producer has been told, not about what the book holds - and
nothing in the environment records what has been told, so a policy that wants it has to
have been keeping it. In the shipped tree the two quantities are equal, which is why the
natural implementation reads the answer off the book and is right; fixing the first defect
is exactly what pulls them apart. Neither can be repaired before the other.

- Tactics making that true: A1 (the memorised receiver-window plan is specifically wrong
  on both), B2 (twelve stated rules whose interactions are the work), C1 (nine of the
  twenty-four enumerated streams are fences the shipped tree already passes and a repair
  must not break), C2 (no producer simulator ships, so "run it and see whether it wedges"
  returns no verdict and the agent's own harness cannot confirm the obligation).

## My own attack on the plan

My first plan: charge both levels on arrival, return both when the consumer draws, hold a
raise under the threshold, flush when the remaining ceiling drops below a minimum batch.
About ninety minutes. I would probably notice the stranded rows, because "credit lost on
teardown" is a known smell. I would not notice that the flush test must be evaluated
against the delayed ceiling, because in the shipped tree that number agrees with the book
on every stream that does not abandon, and my own harness would confirm it.

Where it is wrong: the link's drained total, the obligation's argument, the teardown
window, and generation-scoped belief across a reopen.

## Estimated solves out of 8: 2

## Verifier contract

Frozen before the environment was written; the load-bearing half is the docstring of
`tests/test_outputs.py`, which is the copy that ships.

Graded per stream, all or nothing: the ordered rows the machine emitted (`grant`, `pull`,
`over`, `late`, `drop`) and the rows parked on every live feed at the end. Not graded:
how the policy stores anything, what it names anything, when it computes anything, and
order within a tick - the machine sorts what the policy hands it before appending.

Uniqueness is an induction, not a hope: an emission at tick T changes only what a producer
has learned at T+LAG, so the state at T never depends on emissions at T, the emit
predicate is total and the value is a formula, and the log is therefore a deterministic
function of the stream. Checked, not asserted: a sealed model sharing no code agrees on 24
enumerated and 400 generated streams, and six alternative correct implementations agree
bit for bit on 500 more.

## Numbers, measured

- Shipped tree: 9 of 24 enumerated (the fences), 0 of 300 generated.
- Real two-image trial: oracle 1, nop 0, 23 cheats 0.
- Variants: 6 of 6 score 1.
- Wrong readings against the reference over 300 generated streams: thr-on-spent 100%,
  emit-dead-feeds 94%, owe-from-held 94%, judge-on-held 93%, drain-taken-only 92%,
  pull-as-delta 91%, feed-drain-shed 91%, no-late-window 73%, late-not-shed 73%,
  keep-said-on-reopen 58%, owe-ignores-free 2%.
- Reference time for the whole graded set (324 streams) on this sandbox: 0.33 s. There is
  no resource gate, so no budget is graded and none is stated in the brief.

## Gates not run

The three-agent probe (the owner's rule for this build is a cold self-solve instead; see
the handover). The apt layer is absent by design, so nothing here exercises it.

## Coverage walk, both directions

For every graded decision, the sentence that decides it:

1. two-level charging - "An arrival is charged to the permit for its feed and to the permit
   for the link together."
2. refusal, nothing moves, `over` - "A batch that would carry either of them past what that
   producer has learned is turned away, neither permit moves, nothing is parked, and we
   record an `over`." plus "Either level is enough to refuse it."
3. acceptance - "Anything not refused is `ok` and is parked."
4. draw semantics, and the two no-ops - "The consumer draws whole batches in the order they
   landed, drawing them frees the rows, and a draw against a feed holding nothing does
   nothing at all, as does a draw against a feed that has gone."
5. teardown discards, one `drop` - "A feed can be torn down with rows still parked on it,
   and the streams we grade do that. Those rows are thrown away. One `drop` records the
   total."
6. the teardown window, and what falls outside it - "A teardown takes the same three ticks
   to reach the producer, so it carries on sending into the gap ... After the window closes,
   everything from that feed is an `over`."
7. idempotent teardown and reopen - "Tearing down a feed that has gone does nothing. Neither
   does reopening one that is still up."
8. generations, and the link never restarting - "A feed torn down and later reopened is a
   fresh run of that feed ... The link never restarts. Its totals carry on across the whole
   stream."
9. a ceiling is absolute, monotone, window on top of finished-with - "A ceiling is a running
   total. It is absolute and never a step ..." plus "We never publish a figure that is not
   above the one already standing".
10. the emit predicate - "We publish one exactly when the raise clears the threshold, or when
    holding it back would leave that producer unable to send its smallest batch while rows
    are free. Nothing else earns a `grant`."
11. the idle fallback - "the single exception is the idle fallback, which lowers a feed to
    the floor above what it has finished with and which we record as a `pull`", with the
    seven ticks and the floor of twelve in the constants paragraph.
12. what is graded, the level encoding, and that order is not the policy's - the grading
    paragraph.

The other direction: every sentence in the brief is either one of the twelve above, a
constant the machine works to, an input-space statement ("the streams we grade do that"),
or the grounding run. The grounding paragraph asserts nothing and quotes only the shipped
broken tree.

## Self-probe, and its honest limit

The session that built the task cannot solve it cold, so what was run instead is the
ablation in CLAUDE.md plus a written first plan put through `tools/leakcheck.py`, which came
back with nothing above the floor. That write-up flagged four guesses; three of them - does
a refused arrival count as activity for the idle fallback, does a draw against a torn-down
feed do anything, do the link's totals restart on a reopen - are decided by the brief, and
the fourth is the intended discovery. The three-agent easiness probe has not been run and is
the first thing this bundle needs.
