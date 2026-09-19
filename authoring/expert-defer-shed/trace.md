# Instruction trace: expert-defer-shed

Walked from the verifier toward the instruction (docs/INSTRUCTION-CONTRACT.md). The sealed
model is the test file here, because every graded token is `assert got == want` against it, so
it is split into one row per rule it applies. Checked with
`python tools/tracecheck.py expert-defer-shed`.

## Graded assertions

| Verifier site | What it grades | Instruction sentence |
|---|---|---|
| `tests/test_outputs.py:116` test_frozen_truth_matches_the_model | the sealed side agrees with itself before it judges: the model still reproduces every frozen answer | the whole contract, whose printed form is "prints a line for each thing that happens" |
| `tests/test_outputs.py:126` test_hand_case | the thirty enumerated programs, line for line against the frozen answers, and that the program was not altered | "thirty written by hand" |
| `tests/test_outputs.py:135` test_every_nonce_program_matches | the generated population, line for line against the model, and that no program was altered | "The graded set is three programs of each of those two sizes" |
| `tests/test_outputs.py:154` test_every_family_is_represented | that the population the run was graded on holds all eleven families | "three hundred and sixty smaller ones" |
| artifact `/app/lay/gate.py` | collected and laid over the pristine tree | "The files you may change are" |
| artifact `/app/lay/cap.py` | collected and laid over the pristine tree | "The files you may change are" |
| artifact `/app/lay/buf.py` | collected and laid over the pristine tree | "The files you may change are" |
| artifact `/app/lay/back.py` | collected and laid over the pristine tree | "The files you may change are" |
| artifact `/app/lay/put.py` | collected and laid over the pristine tree | "The files you may change are" |
| artifact `/app/lay/trim.py` | collected and laid over the pristine tree | "The files you may change are" |
| artifact `/app/lay/tally.py` | collected and laid over the pristine tree | "The files you may change are" |
| `tests/worker.py:45` the pristine overlay | nothing outside the seven files can change what a program prints, a new file beside them included | "rest of the tree is replaced by our own copy before a program is run, a new file put beside those seven included" |
| `tests/test.sh:27` a 60 s clock | the whole graded set has to finish inside it, or the run scores 0 | "all of it has to get through inside 60 seconds" |
| `tests/seal/model.py:33` _parse | the step-file grammar: cfg once, then steps, microbatches and tokens, E scores each | "`cfg E B W F G` opens the file and sets the number of experts, the bank width, the want threshold, the capacity factor as a percentage and the bank share as a percentage" |
| `tests/seal/model.py:70` _step ranking | experts rank by gate score descending, a tie to the smaller index | "ranks the experts by gate score descending, a tie going to the smaller expert index" |
| `tests/seal/model.py:52-64` _want | the want list is the shortest prefix of the ranking reaching the threshold | "wants the shortest run of that ranking from the top whose scores add up to W or more" |
| `tests/seal/model.py:60-64` _want, the fall-through | a ranking that never reaches the threshold is wanted entire | "and the whole ranking when the whole ranking adds up to less than W" |
| `tests/seal/model.py:53-56` _want, the skip | an expert that refused the token is skipped when the list is worked out again | "is struck out of the ranking of that token for the rest of the step" |
| `tests/seal/model.py:74-80` _step capacity | C from the first microbatch's wanted places, the microbatch count and the expert count, rounded up | "C is F times the number of expert places the tokens of the first microbatch of the step want between them, times the number of microbatches in the step, over a hundred times the number of experts, rounded up" |
| `tests/seal/model.py:81` _step bank budget | Z from C, the bank width and the share, rounded up | "Z is G times C times the bank width over a hundred, rounded up" |
| `tests/seal/model.py:82` _step, the cap line | `cap` carries C and Z and is printed as the step begins | "`cap C Z` is printed as a step begins" |
| `tests/seal/model.py:96-99` low | the lowest free slot index of an expert, buffers numbered from 0 | "gets C slots numbered from 0" |
| `tests/seal/model.py:134-160` admit, the rank loop | a token takes its wanted experts in rank order at the lowest free slot | "takes the experts it wants in rank order, at the lowest free slot of each" |
| `tests/seal/model.py:138-142` admit, the stop | it stops at the first expert it cannot enter and holds a prefix | "stops at the first one it cannot enter, so what it holds is always a run of its want list from the top" |
| `tests/seal/model.py:109-116` frail | the candidate is the lowest-scoring occupant not yet displaced this step, ties to the larger slot | "the one with the lowest gate score at that expert, a tie going to the larger slot index" |
| `tests/seal/model.py:140` admit, the score test | it leaves only when the arrival's score there is strictly higher | "gives up its place when the arriving token scores strictly higher there" |
| `tests/seal/model.py:145-152` admit, the seize | the arrival takes the occupant's slot rather than any other | "The arrival takes that exact slot" |
| `tests/seal/model.py:118-131` strip | a token that loses a place loses every place further down its own want list | "loses every place it holds further down its own want list as well, and those slots are free from then on" |
| `tests/seal/model.py:127-130` strip, the queue | a token that loses rank zero is queued and prints def; one that keeps it is not | "A token that loses or never gets the first expert of its want list holds nothing and is queued for the next microbatch, printing `def` and its number" |
| `tests/seal/model.py:128` strip, the last microbatch | a loss in the last microbatch is held and prints nothing | "There is no next microbatch after the last one" |
| `tests/seal/model.py:161-163` admit, never placed | a token that never gets rank zero is queued on the same terms | "A token that keeps the first expert is never queued, whatever it lost after it" |
| `tests/seal/model.py:141` admit, the refusal | an expert that turned a token away is struck out as well, not only one that displaced it | "by being full with nobody in it that could be displaced or by taking its place" |
| `tests/seal/model.py:165-175` _step, the microbatch order | queued tokens first in the order they were queued, then the microbatch's own in token order | "the tokens queued by the microbatch before it go first, in the order they were queued, and then its own in token order" |
| `tests/seal/model.py:176-201` _step, the shed | banks in index order, weakest place first, ties to the larger expert then the larger slot | "the lowest-scoring place in it goes, a tie going to the larger expert index and then to the larger slot index" |
| `tests/seal/model.py:195-200` _step, the shed cascade | a shed place takes the token's later places with it, wherever they sit | "and with it every place its token holds further down the want list of that token, wherever those sit" |
| `tests/seal/model.py:180-183` _step, the recheck | a bank's load is read when the bank is reached, so an earlier cascade counts | "the banks are gone over in index order" and "Slots freed this way are not filled again" |
| `tests/seal/model.py:66-95` _step, per step | each step starts from empty buffers, queue, strike-outs and marks | "Each step starts over: empty buffers, an empty queue, nothing struck out and nobody marked as displaced" |
| `tests/seal/model.py:202-215` _step, the tok line | placements in want-list rank order, or none, with the residual | "`tok <token> <expert>:<slot> ... res <residual>` with its places in want-list rank order" |
| `tests/seal/model.py:206-211` _step, the residual | the residual sums the final want list's scores the token does not hold | "The residual is the sum of the gate scores it has at the experts of its want list, as that list finally stands, that it does not hold" |
| `tests/seal/model.py:216-218` _step, the bal line | demand as the final want lists stand against the places each expert kept | "n adds up over the experts the number of tokens whose final want list holds that expert, multiplied by the number of places that expert kept" |
| `tests/seal/model.py:219-224` _rank_of | the rank of a shed place on its own token's record; no token is graded twice for one slot | "with its places in want-list rank order" |
| `tests/seal/model.py:226-232` expect | one trace per file, steps in file order, and nothing else printed | "Nothing else is printed" |

## Readings

Every reading below is built by `authoring/expert-defer-shed/emit.py`, measured by
`python tools/readingcheck.py expert-defer-shed` and scored as a cheat.

| Reading | Sentence or published example that rules it out | Case that separates it |
|---|---|---|
| rank-tie-high: equal scores rank by the larger index | "a tie going to the smaller expert index" | rank-tie |
| want-drops-short: a ranking short of the threshold wants nothing | "the whole ranking when the whole ranking adds up to less than W" | want-short-of |
| cap-whole-step: buffers sized from every microbatch | "the tokens of the first microbatch of the step want between them" | cap-first-mb |
| cap-rounds-down: the buffer size rounds down | "over a hundred times the number of experts, rounded up" | cap-round-up |
| bank-rounds-down: the bank budget rounds down | "Z is G times C times the bank width over a hundred, rounded up" | bank-round-up |
| place-skips-full: a blocked rank is skipped and later ranks still placed | "stops at the first one it cannot enter" | place-prefix-stop |
| slot-never-reused: a freed slot is never filled again | "at the lowest free slot of each" and "those slots are free from then on" | place-lowest-free |
| no-displace: a full expert turns the arrival away | "An expert with no free slot is not closed" | disp-take-slot |
| disp-any-weakest: the weakest leaves whatever the arrival scores | "when the arriving token scores strictly higher there" | disp-equal-holds, disp-below-holds |
| disp-repeat: a token already displaced can be displaced again | "occupants that have not already been displaced in this step" | disp-once-only |
| disp-tie-low: equal occupants, the smaller slot goes | "a tie going to the larger slot index" | disp-tie-slot |
| disp-keeps-rest: only that placement goes | "loses every place it holds further down its own want list as well" | cont-later-ranks |
| defer-behind: queued tokens go after the microbatch's own | "go first, in the order they were queued" | defer-ahead |
| defer-any-short: every truncated token is queued | "A token that keeps the first expert is never queued, whatever it lost after it" | defer-keeps-prefix |
| defer-mid-too: any displaced token is queued | "A token that keeps the first expert is never queued" | cont-mid-rank |
| defer-prints-last: a last-microbatch loss prints def | "is left with nothing and prints nothing" | defer-last-mb |
| want-frozen: a queued token keeps the list it started with | "want list is worked out again over what is left, by the same rule, every time it is looked at" | strike-widens, strike-refusal |
| shed-one-only: a shed removes nothing behind it | "and with it every place its token holds further down the want list of that token" | shed-cascade |
| shed-banks-upfront: the over-budget banks are listed first | "the banks are gone over in index order" | shed-recheck |
| shed-tie-low: the smaller expert index sheds | "a tie going to the larger expert index and then to the larger slot index" | shed-tie |
| res-whole-ranking: the residual counts every expert | "the sum of the gate scores it has at the experts of its want list" | res-want-only |
| bal-over-placed: placements counted against themselves | "the number of tokens whose final want list holds that expert" | bal-final-wants |

## Shortcuts

| Strategy | Result |
|---|---|
| the shipped tree unchanged (the nop) | reward 0 in the container; 29 of 33 graded assertions fail |
| constant: one fixed output for every step (cheat-const-nothing) | reward 0; fails all 30 enumerated programs and all 108 sampled generated ones |
| positional: every token takes its top expert only (cheat-pos-top-only) | reward 0; fails 11 enumerated and 106 of 108 sampled generated programs |
| the worked example replayed: the frozen answers for every enumerated program (cheat-forge-hand) | reward 0; passes all 30 enumerated and fails on the generated population it could not have seen |
| the published dispatch: drop on overflow, no queue, no shed (the shipped tree) | reward 0, as the nop row above |

## Tolerances

| Tolerance or limit | Independent implementation | Measured |
|---|---|---|
| `tests/test.sh:27` a 60 s clock on the whole graded set | `authoring/expert-defer-shed/variants/ok-mask` and `authoring/expert-defer-shed/variants/ok-flat`, both written apart from the reference | 2.9 s and 3.0 s for the six scale programs, against 2.4 s for the reference and 101 s, 115 s and 491 s for the three exactly-correct scanning implementations in `authoring/expert-defer-shed/variants` terms (cheat-slow-weakest, cheat-slow-free, cheat-slow-shed) |
| exactness: the trace is compared string for string, no tolerance | `tests/seal/model.py`, written from the frozen contract, not from the reference | 276 programs including both scale families agree between the reference, the model and both variants |
