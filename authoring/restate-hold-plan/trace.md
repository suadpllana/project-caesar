# Instruction trace: restate-hold-plan

Walked from the verifier toward the instruction (docs/INSTRUCTION-CONTRACT.md) on 2026-09-22,
starting from `python tools/tracecheck.py restate-hold-plan --skeleton`. Every quote is cut from
`tasks/restate-hold-plan/instruction.md` word for word. The sealed model is split into one row per
rule it applies, with its lines. The rule numbers R1-R15 are the ones the model carries in its
comments.

## Graded assertions

| Verifier site | What it grades | Instruction sentence |
|---|---|---|
| `tests/test_outputs.py:103` test_model_reproduces_the_frozen_plans | the sealed side agrees with its own frozen answers before it grades anything; no agent-facing rule | "planned in one process with one CPU" is the only condition it shares with the run; it grades nothing the agent writes (a guard on the verifier, stated so a reader of this row knows it is not a hidden rule) |
| `tests/test_outputs.py:112` test_enumerated_plan | each hand-written pipeline's plan equals its frozen plan, line for line, and was not altered | "and thirty written by hand" and "prints the plan that brings the platform back into agreement" |
| `tests/test_outputs.py:121` test_population_covers_every_family | the generated set holds every family and at least four hundred small pipelines | "four hundred smaller ones generated when it is graded" |
| `tests/test_outputs.py:126` test_every_generated_plan | every generated pipeline's plan equals the model's, line for line | "four hundred smaller ones generated when it is graded" and "four pipelines of each of those two shapes" |
| `tests/test_outputs.py:62` plan_of | a planner that raises, or returns rows that are not lines, fails that pipeline | "prints each row it gets back with the items of the row joined by single spaces" |
| `tests/worker.py:31` planner_tree | only the five files are laid over the pristine tree; a new file is ignored | "The files you may change are" and "a new file put beside those five is not collected" |
| `tests/worker.py:54` main (run_plan.run) | the frozen driver calls reach, settle and order in that shape | "passes the parsed pipeline to" and "passes what that returns to" and "passes that to" |
| `tests/cases.py:11` case plain-rerun | nothing expired, nothing published: every reached partition reruns full, in time order | "and otherwise rerun" and "otherwise `full`" and "Of the lines free to go next, the one whose partition ends first goes" |
| `tests/cases.py:20` case keep-edge | the keep boundary: a partition that ended exactly keep hours ago is gone | "while end <= now < end + keep, so an hourly partition 10 with a keep of 20 exists from hour 11 to hour 30 and is gone at hour 31" |
| `tests/cases.py:27` case keep-published | a published partition older than its keep exists and is read, not computed | "A published partition exists from the hour it ends, whatever its keep" |
| `tests/cases.py:35` case reach-bounded-by-now | a partition that has not ended by now is not reached and prints nothing | "every partition of a step that has ended by now" |
| `tests/cases.py:43` case reach-through-expired | the correction reaches a kept roll-up through hours that no longer exist | "whether or not the partitions in between still exist" |
| `tests/cases.py:52` case pinned-hold | a published reached partition is held; its only reader is held as same | "A published one is held as `pinned`" and "otherwise held as `same` when nothing it reads has changed" |
| `tests/cases.py:60` case pinned-part | a reader of a published reached partition and of a rerun is a part rerun | "The mode is `part` when anything it read does not agree" and "a held partition has not changed and does not agree" |
| `tests/cases.py:69` case pinned-window-same | a window reached only through a published partition is held as same, day by day | "otherwise held as `same` when nothing it reads has changed" |
| `tests/cases.py:77` case pinned-unreached | a published partition the correction does not reach gets no line and agrees | "Every reached partition of a step that exists gets exactly one line" and "A partition the correction does not reach has not changed and agrees" |
| `tests/cases.py:85` case same-disagrees | a partition held as same does not agree, so a rerun reading it is part | "a held partition has not changed and does not agree" |
| `tests/cases.py:96` case temp-window | a window reaching an expired partition computes it for the plan and prints it | "One that does not is computed for the plan from its own reads in the same way" and "A partition computed for a rerun prints `temp <dataset> <partition>`, and so does one computed for a partition printed that way" |
| `tests/cases.py:103` case temp-once | two readers of one expired partition: it is computed and printed once | "once however many computations read it" |
| `tests/cases.py:111` case temp-only-for-reruns | a held partition's window reaches an expired partition: nothing is printed for it, and it changes nothing | "one computed only for a held partition prints nothing" and "So has a partition computed for the plan when anything it read has changed" |
| `tests/cases.py:121` case lost-temps-unprinted | a lost partition's computed reads print only where a rerun also read them | "one computed only for a held partition prints nothing" |
| `tests/cases.py:130` case lost-source | an expired source partition cannot be computed, so its reader is held as lost | "A source partition that does not exist cannot be computed" and "held as `lost` when it cannot be computed" |
| `tests/cases.py:138` case lost-temp-chain | a computed partition that needs an expired source partition cannot be computed either | "and neither can anything that has to read one" |
| `tests/cases.py:145` case lost-before-same | lost is decided before same | "Any other is held as `lost` when it cannot be computed, otherwise held as `same`" |
| `tests/cases.py:155` case stand-use | a day with missing hours reads its roll-up, which reran and agrees: sub | "it reads the partition of r for that day in place of all 24 hours, provided that partition exists and agrees" and "otherwise `sub` when it read a roll-up in place of hours" |
| `tests/cases.py:164` case stand-any-hour | one missing hour is enough for the roll-up to stand in | "and any hour of that day does not exist" |
| `tests/cases.py:173` case stand-refused-published | a published roll-up the correction reached does not agree, so the hours are read and computed | "provided that partition exists and agrees. Otherwise it reads the hours." and "a held partition has not changed and does not agree" |
| `tests/cases.py:184` case stand-refused-part | a roll-up rerun as part does not agree and is refused; the reader does not wait for it | "A rerun has changed" and "either one agrees when everything it read agrees" and "provided that partition exists and agrees" |
| `tests/cases.py:194` case stand-in-temp | a partition computed for the plan reads the roll-up too, and follows the roll-up's rerun | "when any computation except those of r itself reads" and "the rerun of a roll-up it read in place of hours" |
| `tests/cases.py:204` case mode-part-over-sub | part outranks sub | "The mode is `part` when anything it read does not agree, otherwise `sub`" |
| `tests/cases.py:216` case order-after-roll-up | a reader declared before its roll-up follows the roll-up's rerun, and a free line declared between them goes first | "Each follows the lines of everything it read" and "Of the lines free to go next, the one whose partition ends first goes, and of two that end together, the one whose dataset is declared first" |
| `tests/cases.py:226` case holds-last | holds come after every run and temp, whatever their end | "The runs and temps come first" and "The holds follow, by the hour they end and then by declaration" |
| `tests/cases.py:235` case chain-published | a published partition in a self-reading chain stops every later partition from rerunning | "apart from its own previous partition" and "A published one is held as `pinned`" and "otherwise held as `same` when nothing it reads has changed" |
| `tests/cases.py:242` case chain-checkpoint | a published partition before the correction exists and ends the chain of computed partitions | "A published partition exists from the hour it ends, whatever its keep" and "A partition that exists is read as the plan leaves it" |
| `tests/cases.py:249` case chain-to-zero | a self-reading chain with nothing kept is computed back to hour 0 | "A read that falls before hour 0 reads nothing there" and "computed for the plan from its own reads in the same way" |
| `tests/cases.py:256` case prehistory | a window at day 1 reads only what lies at or after hour 0 | "A read that falls before hour 0 reads nothing there" |
| `tests/cases.py:263` case prev-cross | x-1 across grains: the day before, and the last hour of the day before | "the day before, for an hourly step reading a daily x, and the last hour of the day before, for a daily step reading an hourly x" |
| artifact `/app/plan/keep.py` | only the declared files are collected | "The files you may change are" and "Nothing else" |
| artifact `/app/plan/reach.py` | only the declared files are collected | "The files you may change are" and "a new file put beside those five is not collected" |
| artifact `/app/plan/look.py` | only the declared files are collected | "The files you may change are" and "Nothing else" |
| artifact `/app/plan/settle.py` | only the declared files are collected | "The files you may change are" and "Nothing else" |
| artifact `/app/plan/order.py` | only the declared files are collected | "The files you may change are" and "Nothing else" |
| `tests/test.sh:39` a 60 s clock | stage one, the whole graded set, runs under 60 seconds | "it has to get through inside 60 seconds" |
| `tests/test.sh:39` the memory of the run | the verifier container's 2048 MB (task.toml, [environment] memory_mb) | "with one CPU and 2048 MB of memory" |
| `tests/test.sh:39` one process | every pipeline is planned by one worker process, so state kept between pipelines is shared | "All of it is planned in one process" |
| `tests/seal/model.py:31-63` Pipe (R1) | the declarations: now, src, step, stand, pin, fix; one per line | "A pipeline file has one declaration per line" and "sets the current hour" and "declares a source dataset" |
| `tests/seal/model.py:49-55` Pipe (R1) | declaration order is kept as the tie-break position | "the one whose dataset is declared first" |
| `tests/seal/model.py:56-57` Pipe (R1) | stand names the daily roll-up of an hourly dataset | "says that the daily r reads only" |
| `tests/seal/model.py:58-60` Pipe (R1) | pin names published partitions | "names partitions of n that were published" |
| `tests/seal/model.py:61-62` Pipe (R1) | fix names the corrected source partition, which exists | "names the corrected partition, which belongs to a source and exists" |
| `tests/seal/model.py:66-75` read_spec (R2) | the four read forms | "Plain `x` reads the same partition of x" and "reads the w partitions of such an x ending with the one of the same number" |
| `tests/seal/model.py:78-86` span, ends (R3) | the span and end of an hourly and a daily partition | "Hourly partition h spans hours h to h+1, daily partition d spans hours 24d to 24d+24, and a partition ends where its span ends" |
| `tests/seal/model.py:93-94` declared (R2) | same: the same partition | "Plain `x` reads the same partition of x, which has the same grain as the step" |
| `tests/seal/model.py:95-96` declared (R2) | x/d: the 24 hours of the day | "In a daily step, `x/d` reads the 24 hours of its day from the hourly x" |
| `tests/seal/model.py:97-98` declared (R2) | x~w: w partitions ending with the same number | "reads the w partitions of such an x ending with the one of the same number" |
| `tests/seal/model.py:99-102` declared (R2) | x-1: the latest partition ending at or before this one starts | "reads the latest partition of x that ends at or before the partition of the step starts" |
| `tests/seal/model.py:103` declared (R4) | reads before hour 0 are dropped | "A read that falls before hour 0 reads nothing there" |
| `tests/seal/model.py:114-115` ended (R5) | a partition has ended when its end is at or before now | "every partition of a step that has ended by now" |
| `tests/seal/model.py:117-122` exists (R5) | exists while end <= now < end + keep, or once ended if published | "while end <= now < end + keep" and "A published partition exists from the hour it ends, whatever its keep" |
| `tests/seal/model.py:125-141` reach (R6) | the corrected partition and every ended step partition reading a reached one, through missing partitions too | "The correction reaches the corrected partition, and every partition of a step that has ended by now and whose reads name a partition the correction reaches, whether or not the partitions in between still exist" |
| `tests/seal/model.py:143-156` read_by (R6) | the inverse of each read form, so the walk follows the same four reads | "whose reads name a partition the correction reaches" |
| `tests/seal/model.py:162-163` stored (R7) | the corrected partition changed and agrees | "The corrected partition has changed and agrees" |
| `tests/seal/model.py:164-165` stored (R7) | an unreached partition, or a source, is unchanged and agrees | "A partition the correction does not reach has not changed and agrees" |
| `tests/seal/model.py:166-168` stored (R7) | a rerun changed, and agrees when its reads agreed | "A rerun has changed" and "either one agrees when everything it read agrees" |
| `tests/seal/model.py:169` stored (R7) | a held partition is unchanged and does not agree | "a held partition has not changed and does not agree" |
| `tests/seal/model.py:179-183` settle (R9) | a published partition that exists is held as pinned before anything else | "A published one is held as `pinned`" and "it is never rewritten" |
| `tests/seal/model.py:184-188` settle (R8) | a computation reads what its step declares, roll-ups aside | "Computing a partition, for a rerun or for the plan, reads what its step declares" |
| `tests/seal/model.py:189-190` settle (R8) | a partition that does not exist is a temp, or fails | "One that does not is computed for the plan from its own reads in the same way" |
| `tests/seal/model.py:191-192` settle (R9) | cannot be computed: held as lost | "Any other is held as `lost` when it cannot be computed" |
| `tests/seal/model.py:193-194` settle (R9) | nothing read changed: held as same | "otherwise held as `same` when nothing it reads has changed" |
| `tests/seal/model.py:195-202` settle (R10) | the run mode: part, then sub, then full | "The mode is `part` when anything it read does not agree, otherwise `sub` when it read a roll-up in place of hours, and otherwise `full`" |
| `tests/seal/model.py:209-211` stands_in (R11) | never for the roll-up's own computation | "when any computation except those of r itself reads" |
| `tests/seal/model.py:212-213` stands_in (R11) | only when some hour of the day does not exist | "and any hour of that day does not exist" |
| `tests/seal/model.py:214-218` stands_in (R11) | only when the roll-up's partition exists and agrees | "provided that partition exists and agrees" |
| `tests/seal/model.py:219-223` stands_in (R11) | in place of all 24 hours; the reader follows the roll-up's rerun | "in place of all 24 hours" and "the rerun of a roll-up it read in place of hours" |
| `tests/seal/model.py:228-234` take (R12) | a partition that exists is read as stored, after its rerun if it has one | "A partition that exists is read as the plan leaves it" |
| `tests/seal/model.py:235-237` take (R12) | a missing source partition cannot be computed | "A source partition that does not exist cannot be computed" |
| `tests/seal/model.py:238-241` take (R12) | a computation needing one that cannot be computed cannot be either | "and neither can anything that has to read one" |
| `tests/seal/model.py:242-245` take (R12) | a computed partition's flags pass to its reader, which follows it | "So has a partition computed for the plan when anything it read has changed" and "either one agrees when everything it read agrees" and "a partition computed for it" |
| `tests/seal/model.py:251-256` plan (R13) | every reached partition of a step that exists gets exactly one line | "Every reached partition of a step that exists gets exactly one line" |
| `tests/seal/model.py:258-266` plan (R13) | temps: what a rerun or a printed temp computed, and nothing else | "A partition computed for a rerun prints `temp <dataset> <partition>`, and so does one computed for a partition printed that way" and "one computed only for a held partition prints nothing" |
| `tests/seal/model.py:268-288` plan (R14) | each line after what it read; earliest end, then declaration | "Each follows the lines of everything it read" and "Of the lines free to go next, the one whose partition ends first goes, and of two that end together, the one whose dataset is declared first" |
| `tests/seal/model.py:281-284` plan (R14) | the run and temp line formats | "A rerun prints `run <dataset> <partition> <mode>`" and "partitions are printed by number" |
| `tests/seal/model.py:289-290` plan (R14) | the reads of a plan never form a cycle | "A step reads only datasets declared above it, apart from its own previous partition" |
| `tests/seal/model.py:292-295` plan (R15) | holds last, by end then declaration, and their format | "The holds follow, by the hour they end and then by declaration" and "Each hold is printed as `hold <dataset> <partition> <reason>`" |
| `tests/seal/model.py:107-111` Plan | wiring only: reach first, then the settle | "The correction reaches the corrected partition" |
| `tests/seal/model.py:298-301` expect | wiring only: a pipeline's lines to its plan | "takes a pipeline file and prints the plan" |

## Readings

| Reading | Sentence or published example that rules it out | Case that separates it |
|---|---|---|
| pins-expire | "A published partition exists from the hour it ends, whatever its keep" | keep-published (and chain-checkpoint) |
| keep-inclusive | "and is gone at hour 31" and "while end <= now < end + keep" | keep-edge |
| keep-from-start | "A partition exists from the hour it ends until its keep runs out" | keep-edge |
| reach-existing-only | "whether or not the partitions in between still exist", and the quoted "run ses 610 full" | reach-through-expired |
| reach-window-back | "reads the w partitions of such an x ending with the one of the same number" | temp-window (readingcheck names plain-rerun first) |
| reach-prev-same-day | "the day before, for an hourly step reading a daily x" | prev-cross |
| stand-any | "provided that partition exists and agrees" | stand-refused-published |
| stand-all-missing | "and any hour of that day does not exist" | stand-any-hour |
| stand-never | "it reads the partition of r for that day in place of all 24 hours" | stand-use |
| stand-runs-only | "when any computation except those of r itself reads" and "Computing a partition, for a rerun or for the plan" | stand-in-temp |
| no-temp | "One that does not is computed for the plan from its own reads in the same way" | temp-window |
| run-if-reached | "otherwise held as `same` when nothing it reads has changed" | pinned-hold |
| same-before-lost | "Any other is held as `lost` when it cannot be computed, otherwise held as `same`" | lost-before-same |
| sub-over-part | "The mode is `part` when anything it read does not agree, otherwise `sub`" | mode-part-over-sub |
| sub-through-temps | "otherwise `sub` when it read a roll-up in place of hours" and "One that does not is computed for the plan from its own reads in the same way" | stand-in-temp |
| temp-always-changed | "So has a partition computed for the plan when anything it read has changed" | temp-only-for-reruns |
| same-agrees | "a held partition has not changed and does not agree" | same-disagrees |
| pinned-agrees | "a held partition has not changed and does not agree" | pinned-part |
| closure | "A published one is held as `pinned`" and "otherwise held as `same` when nothing it reads has changed" | pinned-hold |
| temps-of-holds | "one computed only for a held partition prints nothing" | lost-temps-unprinted and temp-only-for-reruns |
| temp-per-reader | "once however many computations read it" | temp-once |
| order-static | "Each follows the lines of everything it read" and "the rerun of a roll-up it read in place of hours" | order-after-roll-up |
| order-fix-after-sort | "Of the lines free to go next, the one whose partition ends first goes" | order-after-roll-up |
| holds-interleaved | "The runs and temps come first" and "The holds follow" | holds-last |

## Shortcuts

| Strategy | Result |
|---|---|
| the shipped tree unchanged (nop) | scores 0 in the host trial: stage one runs out of the 60 second clock (exit 124), because the shipped reach indexes every partition of every step from hour 0 and the scale pipelines hold three years of hours, so no record is written and 31 of 33 tests error; run pipeline by pipeline with no clock it matches 7 of 30 enumerated plans (those where nothing reached has expired, is published or stands in) and 25 of 150 sampled generated ones: all 15 plain, 5 pins, 4 cross and 1 chain |
| constant: an empty plan for every pipeline (`cheat-const-nothing`) | scores 0; matches no enumerated plan and none of 150 sampled generated ones |
| constant: every reached partition held as same (`cheat-const-same`) | scores 0; matches 3 of 30 enumerated plans and none of 150 sampled generated ones |
| positional: every reached partition that exists reruns full in time order, published ones included (`cheat-closure`) | scores 0; matches 5 of 30 enumerated plans and 25 of 150 sampled generated ones, the plain family |
| the worked example replayed: every pipeline prints "run ses 610 full" (`cheat-replay-quoted`) | scores 0; matches no enumerated plan and none of 150 sampled generated ones |
| the frozen answers for every enumerated pipeline over the shipped planner (`cheat-forge-enumerated`) | scores 0; passes all 30 enumerated plans and matches 25 of 150 sampled generated ones, failing the rest |
| the previous revision of the reference | there is none: the reference was written once against the frozen contract, and `cheat-slow-every-hour` stands for the shipped reach structure kept under otherwise correct rules |

## Tolerances

| Tolerance or limit | Independent implementation | Measured |
|---|---|---|
| `tests/test.sh:39` a 60 s clock on stage one | `authoring/restate-hold-plan/variants/ok-recursive` and `authoring/restate-hold-plan/variants/ok-forward`, written apart from `solution/`, and the sealed model `tests/seal/model.py` | whole graded set 4.0 s and 5.9 s for the variants and 6.0 s for the reference (`authoring/restate-hold-plan/timing.py`), ten times inside 60 seconds; the exactly correct walk over every partition from hour 0 takes 171.7 s and the re-walk without a memo was still on its first scale pipeline at 430 s |
| memory: the 2048 MB of the verifier container | the same two variants | peak memory planning `environment/app_src/pipes/long.txt`: 73 MB for the reference, 57 MB and 60 MB for the two variants, 44, 35 and 37 MB on `deep.txt`; the index over every partition that the shipped planner builds is the only structure that approaches the limit |
