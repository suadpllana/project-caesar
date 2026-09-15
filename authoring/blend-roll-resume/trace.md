# Instruction trace: blend-roll-resume

Walked from the verifier toward the instruction (docs/INSTRUCTION-CONTRACT.md). Every graded
assertion, enumerated case, sealed-model rule, artifact and limit has a row, with the sentence
of `instruction.md` that tells the agent about it quoted word for word. Checked with
`python tools/tracecheck.py blend-roll-resume`.

## Graded assertions

| Verifier site | What it grades | Instruction sentence |
|---|---|---|
| `tests/test_outputs.py:120` test_frozen_truth_matches_the_model | that the frozen answers and the sealed model still say the same thing about what a script prints, before either is used to judge anything | "Every line is printed at the moment the thing happens." |
| `tests/test_outputs.py:130` test_hand_case | every enumerated script's printed lines, exactly and in order | "Every line is printed at the moment the thing happens." |
| `tests/test_outputs.py:139` test_every_nonce_script_matches | every generated script's printed lines, exactly and in order | "The graded set is 394 scripts, three of them that size" |
| `tests/test_outputs.py:158` test_every_family_is_represented | that the generated population still covers every family, so a shrunk exam is not a pass | "The graded set is 394 scripts, three of them that size" |
| `tests/cases.py:29` case pick-tie-order | a tie in the draw rule falls to the earlier declared source | "when two of them are equal the source declared earlier takes it" |
| `tests/cases.py:38` case pick-tie-weight | a tie does not fall to the heavier source | "when two of them are equal the source declared earlier takes it" |
| `tests/cases.py:48` case pick-ratio | the draw rule itself: smallest counter over weight | "A draw goes to the live source whose counter divided by its weight is smallest" |
| `tests/cases.py:60` case base-weigh | a reweighing returns every live counter to 0 | "each puts every live source's counter back to 0 before the next draw is made" |
| `tests/cases.py:71` case base-weigh-same | a `wt` naming the weight already in force still returns the counters to 0 | "a `wt` line included, whatever weight it names, the one already in force included" |
| `tests/cases.py:82` case base-depart | a departure returns the remaining counters to 0, inside the step | "Declaring a source, reweighing one and a source leaving are each a change" |
| `tests/cases.py:95` case base-hold | the counters are not reset when nothing changed the blend | "A counter counts draws taken since the blend last changed rather than since the run began." |
| `tests/cases.py:108` case roll-over | the cursor advances, the epoch turns over, and the permutation changes with it | "a cursor reaching `n` starts the next epoch with the cursor back at 0" |
| `tests/cases.py:120` case roll-edge | the epoch turns over on reaching `n`, not before and not after | "A draw takes the sample under the source's cursor and moves the cursor on by one" |
| `tests/cases.py:130` case roll-share | two sources turning over independently under one draw rule | "Each source serves its samples in a permutation of 0 to `n - 1` settled by the seed" |
| `tests/cases.py:143` case cap-edge | a capped source leaves at the last sample of epoch `cap - 1` | "it goes at the draw that takes the last sample of epoch `cap - 1`" |
| `tests/cases.py:153` case cap-two | a cap of two serves exactly two epochs, the must-still-work side | "Rather than start the epoch its cap numbers, a capped source leaves the blend" |
| `tests/cases.py:163` case cap-none | a cap of 0 never retires the source, the must-still-work side | "allowed `cap` epochs, where a cap of 0 is no limit" |
| `tests/cases.py:173` case cap-first-draw | a departure on draw 0 of a step, and the `done` line that names it | "naming the step holding the draw that took its last sample and that draw's number inside the step counting from 0" |
| `tests/cases.py:184` case cap-last-draw | a departure on the last draw of a step stays in that step | "naming the step holding the draw that took its last sample and that draw's number inside the step counting from 0" |
| `tests/cases.py:194` case cap-two-out | two departures in one run, each rebasing what follows | "and it goes before any further draw, so the rest of that step is drawn from a blend without it" |
| `tests/cases.py:208` case lay-spread | which draws of a step reach which rank and slot | "Draw `i` of a step, counting from 0, belongs to rank `(i // micro) % ranks` in slot `i // (micro * ranks)`" |
| `tests/cases.py:219` case lay-single | one rank, several slots: the width where both readings agree must still pass | "and takes place `i % micro` of that micro-batch" |
| `tests/cases.py:231` case back-plain | a restart with the same blend and width continues the stream unchanged | "the ones a `stop` puts back stand when the live sources and their weights are what they were when the checkpoint was written" |
| `tests/cases.py:247` case back-step | the step number goes back to the checkpoint's | "A checkpoint holds the step number, and the epoch, cursor and counter of every source declared by the time it is written." |
| `tests/cases.py:261` case back-blend | a source that left before the stop stays out | "so a source that has left stays out" |
| `tests/cases.py:277` case back-weight | a weight changed since the checkpoint stays changed | "a weight changed since stays changed" |
| `tests/cases.py:290` case back-rebase | the counters are 0 when the blend is not the one they were counted under | "and every live source's counter is 0 when they are not" |
| `tests/cases.py:305` case back-swap | two sources trade weights between the checkpoint and the stop, so the live set and the weight total both hold and the blend is still not the one the counters were counted under | "the ones a `stop` puts back stand when the live sources and their weights are what they were when the checkpoint was written" |
| `tests/cases.py:320` case back-hold | the counters stand across a restart that changed nothing | "the ones a `stop` puts back stand when the live sources and their weights are what they were when the checkpoint was written" |
| `tests/cases.py:336` case show-twice | a feed changes nothing, so two of them report the same samples | "so two `feed` lines running report the same samples" |
| `tests/cases.py:347` case show-quiet | a departure a feed only previewed is not announced | "and a departure a `feed` saw is not announced" |
| `tests/cases.py:358` case show-tail | a feed at the last slot still needs the draws of the step before it | "It reports that micro-batch as it would be, a departure inside the step included" |
| `tests/cases.py:370` case join-mid | a source declared mid-run joins the blend and rebases the counters | "Declaring a source, reweighing one and a source leaving are each a change" |
| `tests/cases.py:381` case join-back | a source declared after the checkpoint keeps its own epoch and cursor | "and a source declared after the checkpoint was written keeps the epoch and cursor it has reached" |
| `tests/cases.py:397` case join-cap | a source declared mid-run with a cap leaves like any other | "Rather than start the epoch its cap numbers, a capped source leaves the blend" |
| artifact `/app/mix/deck.py` | only the declared files are collected | "The files you may change are `/app/mix/deck.py`, `/app/mix/pick.py`, `/app/mix/walk.py`, `/app/mix/lay.py`, `/app/mix/keep.py` and `/app/mix/turn.py`." |
| artifact `/app/mix/pick.py` | only the declared files are collected | "Those six are the only files taken from this machine" |
| artifact `/app/mix/walk.py` | only the declared files are collected | "Those six are the only files taken from this machine" |
| artifact `/app/mix/lay.py` | only the declared files are collected | "Those six are the only files taken from this machine" |
| artifact `/app/mix/keep.py` | only the declared files are collected | "Those six are the only files taken from this machine" |
| artifact `/app/mix/turn.py` | only the declared files are collected | "every other file the graded runs use is a clean copy of the tree as you found it" |
| `tests/test.sh:27` a 60 s clock | the wall clock on the stage that runs the submitted feed | "all of it has to get through inside 60 seconds" |
| `tests/seal/model.py:68-83` `_order` | the permutation is settled by the seed, the declaration index and the epoch | "Each source serves its samples in a permutation of 0 to `n - 1` settled by the seed, the source's place in the declaration order and the epoch" |
| `tests/seal/model.py:85-87` `_rebase` | every live counter goes to 0 on a blend change | "each puts every live source's counter back to 0 before the next draw is made" |
| `tests/seal/model.py:89-92` `_sig` | the blend as the draw rule sees it: who is live, in order, and what each weighs | "The live sources and their weights are the blend" |
| `tests/seal/model.py:94-102` `_who` | smallest counter over weight, earlier declaration takes a tie | "A draw goes to the live source whose counter divided by its weight is smallest, and when two of them are equal the source declared earlier takes it" |
| `tests/seal/model.py:104-116` `_spot` | the same rule read as an order over draws, used to jump | "A draw goes to the live source whose counter divided by its weight is smallest" |
| `tests/seal/model.py:117-136` `_count` | the counters after any number of draws of a segment | "A counter counts draws taken since the blend last changed rather than since the run began." |
| `tests/seal/model.py:138-145` `_take` | the sample under the cursor, the cursor moving on, the epoch turning over | "A draw takes the sample under the source's cursor and moves the cursor on by one, and a cursor reaching `n` starts the next epoch with the cursor back at 0." |
| `tests/seal/model.py:147-151` `_jump` | the same advance done in one move rather than draw by draw | "A draw takes the sample under the source's cursor and moves the cursor on by one" |
| `tests/seal/model.py:153-154` `_spent` | a source is finished when it would start the epoch its cap numbers | "Rather than start the epoch its cap numbers, a capped source leaves the blend" |
| `tests/seal/model.py:156-161` `_room` | how many draws are left before the cap is finished | "it goes at the draw that takes the last sample of epoch `cap - 1`" |
| `tests/seal/model.py:163-180` `_reach` | which draw of the segment finishes a capped source | "it goes at the draw that takes the last sample of epoch `cap - 1`" |
| `tests/seal/model.py:182-186` `_span` | which draws of a step belong to one rank and slot | "Draw `i` of a step, counting from 0, belongs to rank `(i // micro) % ranks` in slot `i // (micro * ranks)`, and takes place `i % micro` of that micro-batch." |
| `tests/seal/model.py:189-191` `_slide` | a stretch of draws taken without laying any of them out | "Which source a draw goes to is settled before any of that, and does not depend on the rank count, the micro-batch size or the accumulation depth." |
| `tests/seal/model.py:193-223` `_go` | steps are taken, a departure is announced where it fell, and the counters rebase | "and it goes before any further draw, so the rest of that step is drawn from a blend without it" |
| `tests/seal/model.py:193-223` `_go` (the `done` line) | the source, the step holding the draw, and the draw's number in the step | "A source leaving prints `done <name> <step> <draw>`, naming the step holding the draw that took its last sample and that draw's number inside the step counting from 0." |
| `tests/seal/model.py:193-223` `_go` (the step counter) | steps run on from where the script has got to | "Steps are numbered from 0 across the whole script." |
| `tests/seal/model.py:225-240` `_feed` | the step about to be taken, reported and then put back | "It reports that micro-batch as it would be, a departure inside the step included, and leaves the run exactly where it found it" |
| `tests/seal/model.py:225-240` `_feed` (the printed line) | one entry per place, in the order the draws are taken | "one entry per place in the micro-batch in the order the draws are taken" |
| `tests/seal/model.py:242-244` `_save` | what a checkpoint holds | "A checkpoint holds the step number, and the epoch, cursor and counter of every source declared by the time it is written." |
| `tests/seal/model.py:246-257` `_stop` (what goes back) | the step, and the epoch, cursor and counter of the sources it holds | "A `stop` puts those back and nothing else" |
| `tests/seal/model.py:246-257` `_stop` (the manifest) | the blend is not put back | "who is live and what they weigh is the manifest's" |
| `tests/seal/model.py:246-257` `_stop` (a later source) | a source declared since keeps its own epoch and cursor | "and a source declared after the checkpoint was written keeps the epoch and cursor it has reached" |
| `tests/seal/model.py:246-257` `_stop` (the rebase) | the restored counters stand only under the blend they were counted in | "and every live source's counter is 0 when they are not" |
| `tests/seal/model.py:259-296` `ex` (`src`) | a declaration adds to the blend at epoch 0 with the cursor at 0 | "it starts at epoch 0 with its cursor at 0" |
| `tests/seal/model.py:259-296` `ex` (`at`) | the epoch and cursor a source stands at, or that it has left | "or `at <name> <epoch> <cursor>`, or `at <name> out` where the source has left" |
| `tests/seal/model.py:259-296` `ex` (nothing else) | no other line is produced by any op | "Nothing else is printed." |
| `tests/seal/model.py:41-46` `_turn` | the mixing step inside the permutation; no rule of its own | "which `/app/mix/perm.py` already computes" |
| `tests/seal/model.py:48-66` `Mix` | the state record the rules act on; no rule of its own | "A checkpoint holds the step number, and the epoch, cursor and counter of every source declared by the time it is written." |
| `tests/seal/model.py:298-302` `expect` | drives the ops of one script in order | "A script is a text file of those lines" |

## Readings

| Reading | Sentence or published example that rules it out | Case that separates it |
|---|---|---|
| total-counter | "A counter counts draws taken since the blend last changed rather than since the run began." | base-weigh |
| tie-weight | "when two of them are equal the source declared earlier takes it" | pick-tie-weight |
| tie-late | "when two of them are equal the source declared earlier takes it" | pick-tie-order |
| no-rebase-weigh | "a `wt` line included, whatever weight it names, the one already in force included" | base-weigh |
| no-rebase-drop | "Declaring a source, reweighing one and a source leaving are each a change" | base-depart |
| no-rebase-join | "Declaring a source, reweighing one and a source leaving are each a change" | join-mid |
| cap-late | "it goes at the draw that takes the last sample of epoch `cap - 1`" | cap-edge |
| cap-early | "Rather than start the epoch its cap numbers, a capped source leaves the blend" | cap-two |
| depart-step-end | "and it goes before any further draw, so the rest of that step is drawn from a blend without it" | cap-last-draw |
| done-next-draw | "naming the step holding the draw that took its last sample and that draw's number inside the step counting from 0" | cap-first-draw |
| lay-contig | "Draw `i` of a step, counting from 0, belongs to rank `(i // micro) % ranks` in slot `i // (micro * ranks)`" | lay-spread |
| lay-no-accum | "A step takes `ranks * micro * accum` draws and each draw is one sample." | back-plain |
| keep-blend | "who is live and what they weigh is the manifest's" | back-blend |
| rebase-always | "the ones a `stop` puts back stand when the live sources and their weights are what they were when the checkpoint was written" | back-hold |
| rebase-never | "and every live source's counter is 0 when they are not" | back-rebase |
| rebase-by-sum | "stand when the live sources and their weights are what they were when the checkpoint was written" | back-swap |
| join-reset | "and a source declared after the checkpoint was written keeps the epoch and cursor it has reached" | join-back |
| feed-commits | "and leaves the run exactly where it found it" | show-twice |
| feed-announces | "and a departure a `feed` saw is not announced" | show-quiet |
| feed-own-slot | "It reports that micro-batch as it would be, a departure inside the step included" | show-tail |
| at-departed | "or `at <name> out` where the source has left" | show-quiet |

Two readings that read every rule correctly and differ only in cost - taking every draw, and
settling the counters once per step - are not in this table and are not claimed to be separated
by any script. Nothing but "all of it has to get through inside 60 seconds" rules them out, and
that limit is in the Tolerances table below with its measurement. Both ship as cheats
(`cheat-slow-per-draw`, `cheat-slow-per-step`) and both score 0.

Two further readings were enumerated and discarded before they were built, because the
published evidence does not leave them open. That a query might report the step just taken
rather than the one about to be taken is settled by "asks which samples that rank would be
handed in that slot of the step about to be taken"; that the permutation might be reshuffled
when a run restarts is settled by "settled by the seed, the source's place in the declaration
order and the epoch", which names nothing that a restart changes.

## Shortcuts

| Strategy | Result |
|---|---|
| the shipped tree unchanged (the nop) | reward 0; matched 10 of 190 scripts, and the big family alone exceeds the 60 s clock |
| constant: one fixed micro-batch for every question, no departures | reward 0; matched 0 of 190 scripts (`cheat-shortcut-const`) |
| positional: every draw goes to the first live source | reward 0; matched 1 of 190 scripts (`cheat-shortcut-first-source`) |
| the worked example's output replayed for every question | reward 0; matched 0 of 190 scripts (`cheat-shortcut-example`) |
| the frozen answers for all 30 enumerated scripts, carried and replayed | reward 0; reproduced all 30 and matched 125 of 190, failing only `test_every_nonce_script_matches` (`cheat-forge-from-truth`) |

## Tolerances

| Tolerance or limit | Independent implementation | Measured |
|---|---|---|
| `tests/test.sh:27` a 60 s clock on the stage that runs the submitted feed | `authoring/blend-roll-resume/variants/ok-bisect` and `.../ok-reach`, both written apart from the reference, and `tests/seal/model.py` | the whole graded set of 394 scripts takes 0.065 s under the reference; both correct variants agree with the model on all 393; the step-by-step reading runs at about 812 thousand draws a second against the 2.15 thousand million a wide script asks for, and the per-step reading extrapolates to 84 s for one wide script |
| exact string equality on every printed line - no numeric tolerance anywhere | `authoring/blend-roll-resume/naive.py`, a brute-force engine written straight from the contract, plus `authoring/blend-roll-resume/variants/ok-bisect` and `authoring/blend-roll-resume/variants/ok-reach` | 0 disagreements between reference, sealed model and the brute-force engine over 963 generated scripts on each of two seeds, plus all 30 enumerated scripts; both variants match the model on all 394 graded scripts |
