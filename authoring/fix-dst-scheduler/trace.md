# Instruction trace: fix-dst-scheduler

Walked from the verifier toward the instruction (docs/INSTRUCTION-CONTRACT.md). Every graded
assertion, every enumerated case, every branch of the sealed model that can move a printed token,
every collected artifact and the graded run's clock has a row here with the sentence that tells the
agent about it. Re-walked in full on 2026-09-17 after the easiness recovery added the reservation
rule (contract rule 10a), eleven enumerated plans and eight readings. Checked with
`python tools/tracecheck.py fix-dst-scheduler`.

## Graded assertions

| Verifier site | What it grades | Instruction sentence |
|---|---|---|
| `tests/test_outputs.py:83` test_only_the_planner_modules_differ | everything outside the four collected paths is the shipped file | "stay exactly as they are, nothing outside those four files is read" |
| `tests/test_outputs.py:102` test_worker_ran_every_plan | the planner did not raise on any plan | "We grade every printed line of every plan, exactly, all or nothing" |
| `tests/test_outputs.py:111` test_nonce_echo | the traces belong to this run's population | "on the two plans in the tree and on several hundred plans you have not seen" |
| `tests/test_outputs.py:117` test_every_line_came_from_a_record | every printed line came from the frozen record type | "still has to hand back a list of" `sked.rec.Ev` records for `sked.emit.lines` to print |
| `tests/test_outputs.py:133` test_enumerated_plan | each frozen corner plan, line for line | "We grade every printed line of every plan, exactly, all or nothing" |
| `tests/test_outputs.py:141` test_frozen_answers_still_match_the_model | the sealed model still reproduces the frozen answers; grades nothing the agent wrote | "We grade every printed line of every plan, exactly, all or nothing" |
| `tests/test_outputs.py:151` test_generated_families | the generated plans, line for line, against the sealed model | "on the two plans in the tree and on several hundred plans you have not seen" |
| `tests/cases.py:20` case plain-run | two uncontended clock jobs must still produce every ordinary run | "the one waiting occurrence that can start does" |
| `tests/cases.py:28` case plain-follow | an uncontended follow job re-enters its window after a drop | "every later occurrence due `step` minutes in elapsed time after the instant the one before it was attempted" |
| `tests/cases.py:36` case fold-repeat | a local minute that names two instants | "Where instants exist whose local minute is exactly the one wanted, take the latest of them" |
| `tests/cases.py:45` case gap-jump | a local minute that names none, and wall-clock advance across it | "where none does, take the first instant whose local minute is past the one wanted" |
| `tests/cases.py:54` case wait-chain | a displaced follow job re-anchors on the start it got | "due `step` minutes in elapsed time after the instant the one before it was attempted" |
| `tests/cases.py:63` case starve-drop | a drop is an attempt and anchors the chain at the drop minute | "An occurrence is attempted when it starts, and also when it is dropped, at the minute it is dropped" |
| `tests/cases.py:72` case yield-order | a long low run is held back for two shorter higher jobs due inside it, and they run in priority order | "would not stand in the way of a higher job"; "the one waiting occurrence that can start does" |
| `tests/cases.py:82` case cap-yield | a capped top-priority occurrence does not hold the worker shut | "does not keep the worker shut, and does not stop waiting either" |
| `tests/cases.py:93` case pool-zone | the ledger counts days in the pool's zone, not the job's | "at most `cap` starts per local day of the pool's own zone, which is not always the local day of the job that is running" |
| `tests/cases.py:102` case pool-midnight | a run spanning the pool's midnight is charged where it started | "the charge falls on the day the run started" |
| `tests/cases.py:110` case cap-rollover | a waiting occurrence starts when the pool day rolls over | "Nothing is planned for an instant later than it could have started" |
| `tests/cases.py:120` case shift-in-window | a shift inside a window moves the deadline | "A shift inside a window moves that boundary with it" |
| `tests/cases.py:130` case shut-edge | an occurrence due on the closing minute is dropped at once | "at or after the opening and strictly before the closing" |
| `tests/cases.py:138` case open-edge | an occurrence due on the opening minute is admitted | "at or after the opening and strictly before the closing" |
| `tests/cases.py:146` case dead-edge | the deadline minute is not a minute to start on | "up to but not including the first instant after that which its job does not admit" |
| `tests/cases.py:155` case same-minute | a run ending on the minute its job is next due does not suppress it | "runs that finish do so first, then occurrences come due, then deadlines fall, then the worker starts at most one run" |
| `tests/cases.py:163` case run-overlap | a running occurrence suppresses the next one | "comes due while its job still has an occurrence that has not ended, been dropped or been skipped is skipped at the minute it comes due" |
| `tests/cases.py:171` case index-gap | the index counts skipped and dropped occurrences | "numbered from 0 in the order they come due, counting the ones that are skipped and the ones that are dropped" |
| `tests/cases.py:179` case horizon-cut | a run starting inside the horizon and finishing outside it | "a run that starts inside the horizon and would finish outside it prints its start and nothing else" |
| `tests/cases.py:187` case shipped-coast | the first shipped plan, line for line | "on the two plans in the tree and on several hundred plans you have not seen" |
| `tests/cases.py:199` case shipped-island | the second shipped plan, line for line | "on the two plans in the tree and on several hundred plans you have not seen" |
| `tests/cases.py:212` case reserve-fit | a short lower run that ends before the higher due starts on time | "would not stand in the way of a higher job"; "up to but not including the one at which this run would end" |
| `tests/cases.py:221` case reserve-straddle | a lower run that would straddle the higher due waits for it | "plan them on their own from there with the worker free and the pools as they stand before this start" |
| `tests/cases.py:230` case reserve-edge | a higher start exactly when the run would end does not hold it back | "A higher start exactly when the run would end is no obstacle" |
| `tests/cases.py:239` case reserve-dropped | a higher due the window would drop holds nothing back | "see whether any of them starts a run at any instant from that one" |
| `tests/cases.py:249` case reserve-capped | a capped higher occurrence's rollover inside the run holds it back | "in the state they are in at that instant"; "the pools as they stand before this start" |
| `tests/cases.py:261` case reserve-chain | the higher jobs are planned with the same rule among themselves | "plan them on their own from there" |
| `tests/cases.py:271` case reserve-follow | a higher follow job's next due is where its attempt chain stands | "in the state they are in at that instant"; "after the instant the one before it was attempted" |
| `tests/cases.py:281` case reserve-deadline | a held-back occurrence still drops at its deadline | "does not stop waiting either: it still drops at its deadline" |
| `tests/cases.py:290` case reserve-horizon | a higher start past the horizon still holds a run back | "a higher start that would fall past the horizon keeps a run waiting just as one inside it does" |
| `tests/cases.py:300` case reserve-charge | the pools are judged before this run's own charge | "the pools as they stand before this start" |
| `tests/cases.py:310` case reserve-mid | every higher job counts, not only the highest | "Take the jobs of higher priority" |
| artifact `/app/sked/zt.py` | only the declared files are collected | "`/app/sked/zt.py`, `/app/sked/due.py`, `/app/sked/gate.py` and `/app/sked/lane.py` are the four files you may change" |
| artifact `/app/sked/due.py` | only the declared files are collected | "are the four files you may change" |
| artifact `/app/sked/gate.py` | only the declared files are collected | "are the four files you may change" |
| artifact `/app/sked/lane.py` | only the declared files are collected | "are the four files you may change" |
| `tests/test.sh:44` a 600 s clock on the graded run | the whole graded population must plan inside it | "The graded run has 600 seconds for all of them together" |
| `tests/seal/model.py:34-45` Zone.off, Zone.loc, Zone.tod, Zone.dayno | an instant's offset, local minute, time of day and local day | "a local minute is the instant plus the zone's offset at that instant"; "The time of day of an instant is its local minute modulo 1440, and the local day of an instant is its local minute divided by 1440, rounded down" |
| `tests/seal/model.py:51-66` Zone.to_abs, exact branch | a local minute that names one or two instants resolves to the latest | "Where instants exist whose local minute is exactly the one wanted, take the latest of them" |
| `tests/seal/model.py:51-66` Zone.to_abs, empty branch | a local minute that names none resolves past itself | "where none does, take the first instant whose local minute is past the one wanted" |
| `tests/seal/model.py:68-70` Zone.seg_end | the next offset segment bounds every forward walk | "A shift inside a window moves that boundary with it" |
| `tests/seal/model.py:73-78` Pool | a pool's zone and cap are read from the plan | "A `pool` line gives a name, a zone and a cap" |
| `tests/seal/model.py:80-91` Job.__init__ | a job's fields are read in the order the plan writes them | "A `job` line gives an id, a zone, a priority, a pool, a duration, an opening and a closing time of day, a mode, a step and an anchor" |
| `tests/seal/model.py:93-95` Job.admits | the window is closed at the opening and open at the closing | "at or after the opening and strictly before the closing" |
| `tests/seal/model.py:97-115` Job.flip | the next instant at which admission can change | "A shift inside a window moves that boundary with it" |
| `tests/seal/model.py:117-122` Job.closes | the deadline is the first instant after the due one the job does not admit | "up to but not including the first instant after that which its job does not admit" |
| `tests/seal/model.py:124-130` Job.due, clock branch | a clock cadence advances in local minutes | "has its occurrence `k` due at the local minute `anchor + k * step`" |
| `tests/seal/model.py:124-130` Job.due, follow branch | a follow cadence advances in elapsed minutes from the attempt | "due `step` minutes in elapsed time after the instant the one before it was attempted, with no local resolution at all" |
| `tests/seal/model.py:133-146` next_midnight | the pool day rolls over at the pool zone's local midnight | "at most `cap` starts per local day of the pool's own zone" |
| `tests/seal/model.py:149-169` read | the plan directives and their field order | "A `zone` line gives a name and a base offset, and each `shift` line gives an instant and the offset in force from that instant on" |
| `tests/seal/model.py:171-179` Run | an occurrence waits from the minute it is due until its deadline | "it may start at any instant from when it is due" |
| `tests/seal/model.py:198-200` Sim.push | nothing is scheduled at or past the horizon of the plan being run | "Every event whose instant is below the horizon is printed and no event at or above it is" |
| `tests/seal/model.py:202-221` Sim.snapshot | the higher jobs in their current state, worker free, pools as they stand, planned no further than the run's end | "Take the jobs of higher priority in the state they are in at that instant, plan them on their own from there with the worker free and the pools as they stand before this start" |
| `tests/seal/model.py:223-231` Sim.reserved, the interval | a start at any instant from this one up to but not including the run's end holds it back | "at any instant from that one up to but not including the one at which this run would end"; "A higher start exactly when the run would end is no obstacle" |
| `tests/seal/model.py:223-231` Sim.reserved, past the horizon | the projection ignores the plan's horizon | "The horizon limits what is printed and not what is planned" |
| `tests/seal/model.py:233-236` Sim.note | the printed order of events inside one instant | "Lines come in order of instant, then in that order of kind, then by ascending priority" |
| `tests/seal/model.py:238-246` Sim.slot, Sim.room, Sim.spend | the cap ledger's key and when it is charged | "at most `cap` starts per local day of the pool's own zone"; "the charge falls on the day the run started" |
| `tests/seal/model.py:248-250` Sim.busy_with | a running occurrence still counts as its job's | "still has an occurrence that has not ended, been dropped or been skipped" |
| `tests/seal/model.py:252-256` Sim.after_attempt | only a follow job's next due instant moves with the attempt | "every later occurrence due `step` minutes in elapsed time after the instant the one before it was attempted" |
| `tests/seal/model.py:258-262` Sim.step_ends | runs that finish do so before anything else in that minute | "runs that finish do so first" |
| `tests/seal/model.py:264-284` Sim.step_arrivals, skip branch | an occurrence arriving on a busy job is skipped | "is skipped at the minute it comes due" |
| `tests/seal/model.py:264-284` Sim.step_arrivals, index | the occurrence number counts every occurrence | "numbered from 0 in the order they come due, counting the ones that are skipped and the ones that are dropped" |
| `tests/seal/model.py:264-284` Sim.step_arrivals, deadline | an occurrence due outside its window is dropped at that instant | "An occurrence due at an instant its job does not admit is dropped at that instant" |
| `tests/seal/model.py:286-292` Sim.step_drops | deadlines fall after occurrences come due and before a run starts, and a held-back occurrence drops too | "then deadlines fall, then the worker starts at most one run"; "it still drops at its deadline" |
| `tests/seal/model.py:294-315` Sim.step_start, choice | the one occurrence that can start does | "the one waiting occurrence that can start does" |
| `tests/seal/model.py:294-315` Sim.step_start, cap and reservation | a capped or held-back occurrence is passed over rather than blocking | "does not keep the worker shut, and does not stop waiting either" |
| `tests/seal/model.py:294-315` Sim.step_start, wake on cap | a waiting occurrence is reconsidered when its pool day rolls | "Nothing is planned for an instant later than it could have started" |
| `tests/seal/model.py:317-330` Sim.go | one run at a time, never interrupted, one start per minute, and a projection stops at its first start | "The worker runs one job at a time and never interrupts a run that has started"; "no two runs ever start on the same minute"; "If one does, this occurrence cannot start yet" |
| `tests/seal/model.py:332-334` trace | the printed line and its separators | "the kind, the job id, the occurrence number and the instant, separated by single spaces" |

## Readings

| Reading | Sentence or published example that rules it out | Case that separates it |
|---|---|---|
| amb-early | "Where instants exist whose local minute is exactly the one wanted, take the latest of them" | fold-repeat |
| gap-naive | "where none does, take the first instant whose local minute is past the one wanted" | gap-jump |
| clock-abs | "has its occurrence `k` due at the local minute `anchor + k * step`, resolved to an instant by the rule above" | gap-jump |
| follow-nominal | "due `step` minutes in elapsed time after the instant the one before it was attempted" | wait-chain |
| drop-at-nominal | "An occurrence is attempted when it starts, and also when it is dropped, at the minute it is dropped" | starve-drop |
| lane-top-only | "does not keep the worker shut, and does not stop waiting either" | cap-yield |
| cap-job-zone | "per local day of the pool's own zone, which is not always the local day of the job that is running" | pool-zone |
| cap-at-end | "the charge falls on the day the run started" | pool-midnight |
| shut-closed-form | "A shift inside a window moves that boundary with it, so the minute a window closes is not always a fixed distance from the minute the occurrence was due" | shift-in-window |
| no-cap-wake | "Nothing is planned for an instant later than it could have started" | cap-rollover |
| win-shut-inclusive | "at or after the opening and strictly before the closing" | shut-edge |
| win-open-exclusive | "at or after the opening and strictly before the closing" | open-edge |
| dead-inclusive | "up to but not including the first instant after that which its job does not admit" | dead-edge |
| skip-only-waiting | "still has an occurrence that has not ended, been dropped or been skipped" | run-overlap |
| end-after-arrive | "runs that finish do so first, then occurrences come due" | same-minute |
| index-started | "counting the ones that are skipped and the ones that are dropped" | index-gap |
| no-reserve | "it would not stand in the way of a higher job" | reserve-straddle |
| reserve-inclusive-end | "A higher start exactly when the run would end is no obstacle" | reserve-edge |
| reserve-dues-only | "plan them on their own from there with the worker free and the pools as they stand before this start" | reserve-dropped |
| reserve-top-only | "Take the jobs of higher priority" | reserve-mid |
| reserve-no-recursion | "plan them on their own from there" | reserve-chain |
| reserve-waiting-only | "see whether any of them starts a run at any instant from that one" | reserve-straddle |
| reserve-after-charge | "the pools as they stand before this start" | reserve-charge |
| reserve-stop-at-horizon | "The horizon limits what is printed and not what is planned" | reserve-horizon |

Every reading above is a whole planner in `authoring/fix-dst-scheduler/readings.py`; the fraction
of the generated population each one moves, and the enumerated case that names it, are measured
by `readings.py` and `casecheck.py`. The smallest is lane-top-only at 1.1 per cent of plans and
the largest dead-inclusive at 71.8 per cent; `no-reserve`, the method every probe trajectory used,
moves 42 per cent; none moves nothing. A reading that was carried before the recovery, choosing
the longest-waiting occurrence rather than the best priority, was dropped on 2026-09-17: under the
reservation rule the order in which waiting occurrences are considered cannot change which one
starts, because any higher occurrence that could start stands in the way of every lower one, so
it measured 0 of 280 plans and separates nothing. The instruction states the choice as an outcome
for the same reason.

## Shortcuts

| Strategy | Result |
|---|---|
| the shipped tree unchanged (nop) | reward 0; the sweep-shaped planner fails the contended enumerated plans and every generated family |
| constant: an empty trace for every plan (`cheat-flat-empty.sh`) | reward 0; matches 0 of 382 plans |
| constant: every occurrence dropped on its nominal (`cheat-flat-drop-all.sh`) | reward 0; matches 0 of 382 plans, and the ordinary plains are the first to fail |
| positional: only the first job, started at its first nominal (`cheat-flat-first.sh`) | reward 0; matches 0 of 382 plans |
| positional: every occurrence started on its nominal, worker ignored (`cheat-flat-cadence.sh`) | reward 0; matches 0 of 382 plans, including plain-run where nothing contends |
| the printout in the brief replayed (`cheat-flat-replay.sh`) | reward 0; the brief prints the shipped planner's wrong trace, so replaying it matches no plan at all, not even shipped-coast |
| every local rule right, no reservation (`cheat-rule-no-reserve.sh`, the probe trajectories' method) | reward 0; fails reserve-straddle and ten other enumerated plans and 42 per cent of the generated population |

## Tolerances

| Tolerance or limit | Independent implementation | Measured |
|---|---|---|
| `tests/test.sh:44` a 600 s clock on the graded run | `tests/seal/model.py`, written apart from `solution/`, and the two correct variants under `authoring/fix-dst-scheduler/variants/` | measured on the full 382-plan population, 18190 events: sealed model 0.11 s, reference 0.12 s, ok-heap 0.13 s, ok-tick 0.19 s. The clock is roughly 3000 times the slowest of them, so it bounds a hang rather than grading speed |

No other tolerance exists: every graded quantity is an integer and every comparison is exact.
