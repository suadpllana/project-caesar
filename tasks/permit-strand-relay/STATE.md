# Task state

Working memory. Never ships - `package.py` drops it. Rewritten 2026-09-05 after the
easiness probe (0 of 3) and the difficulty probe (0 of 8, "unsolvable as specified")
both came back on the same bundle.

## Current stage

`Stage 8 - resubmission`, after a fairness repair and a resource boundary.

## What the two probes found, and what was done

Eleven agents failed, and the three easiness trajectories say why: every one of them
transcribed the brief into the reference in one write - the learned-figure history, the
shed rows at the link, the late window, the reopen reset - and lost on ONE corner the
brief left undecided. The reference measured the small-grant obligation against the
figure the producer had LEARNED, which made it publish a cascade of sub-threshold
follow-on grants for three ticks after every obligation grant; the shipped code and
common sense both measure it against the figure already published, and trajectory 3 said
so in its own words. That reading fails 6 of 24 enumerated and 283 of 300 generated
streams. Reconstructed and graded here; see CLAUDE.md.

Two things changed:

1. **Fairness.** The obligation is now measured against the figure already published
   (a figure in flight counts), which is the regular reading with no cascade, and the
   brief says so in requirement form. The brief also pins the three alignments the
   agents had to guess: a figure published at the end of tick t governs from t+3, the
   teardown gap is the teardown's own tick and the two after it, and a reopened run
   knows its window at once. Two enumerated cases (`owe-in-flight`, `owe-after-pull`)
   separate the old reference's reading, which now ships as `cheat-rule-owe-from-learned`.
2. **Difficulty.** Everything left was transcription, so a semantic resource boundary
   went in (the repo's verified recipe, see CLAUDE.md "Verified recovery"). Five of the
   300 generated streams are wide - 7000-9000 feeds over 110k-130k ticks, each feed busy
   for a few dozen ticks - and the machine now tells the policy about draws (`rtn.took`,
   used by the shipped tree for its own tally). A policy that asks about every open feed
   on every tick (the shipped shape) takes over eleven minutes on ONE wide stream against
   the run's 600 s kill; the reference asks only about levels touched during the tick
   plus the feeds whose idle clock runs out, and does the whole run in under a minute.
   Walking the published record per arrival is a second way to die (`slow-history-walk`).
   The brief states the scale and the ten-minute limit and nothing about the method.

## Task summary

A multiplexed ingest link with a two-level permit budget: a shared link ceiling and a
per-feed one. The shipped tree accounts for permit the way every receiver-side window is
written up, and that accounting is coherent, conventional and wrong here. The graded
artifact is the published obligation: which ceiling each level is told and on which tick,
plus the store the stream leaves behind.

## Why it is hard

- Expert time estimate: 8 hours
- Why a frontier agent cannot one-shot the plan (the strategic answer - required): every rule transcribes,
  and the trajectories prove it; what does not transcribe is that the
  natural policy never finishes a wide stream, and the schedule that does finish has to
  be complete - draws, accepted arrivals, sheds, reopens, the idle clock of every feed
  including the thousands that never see an event - or it is wrong on a stream the
  agent's own small-stream oracle would have caught only if its generator makes silent
  feeds.
- Tactics making that true: prong A and prong C, with C3 as the load-bearing one (the
  schedule's triggers are consequences of the frozen machine's hooks, not stated; there is
  no oracle for the published obligation; and the natural implementation cannot cross the
  resource boundary).
- My own attack on the plan (my first plan, and where it is wrong): mark levels dirty on
  events and publish for those; wrong because the idle pull-back fires with no event on
  the feed, for every feed the book armed, including the ones the stream never touches.
- Estimated solves out of 8: 2 of 8, designed for the lower half of the band.

## Verifier contract (frozen)

Graded all-or-nothing on three axes: the published rows per level per tick, the parked
store at the end of the stream, and the lifecycle log. 26 enumerated streams and 300
generated inside the verifier from a nonce made after the agent has finished, five of
them wide. Ground truth is re-proved at verification time by `tests/oracle.py`, which
shares no code with the engine and is itself event-driven.

## What ran, 2026-09-05

See the CLAUDE.md entry for the numbers: `build_gt` proved on 26 + 400 (wide included),
`prove` 300/0, `audit` 26 states and 7 variants agreeing, `variant_check` 7/7 on 199
small plus 2 wide, `readingcheck` 11/11 separated, `tiecheck` 326 streams 0 clashes,
`determinism` identical across 5 seeds, `field_report` no dead field, `textcheck` clean
against three passing briefs, `structcheck` and `hintcheck` clean.

## Gates NOT run

The three-agent easiness probe (the owner's rule: no subagents). Whatever the trial
output in `probe/fulltrial.out` says at handover time is what ran in docker.
