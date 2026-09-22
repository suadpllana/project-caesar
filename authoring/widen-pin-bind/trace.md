# Instruction trace: widen-pin-bind

Walked from the verifier toward the instruction (docs/INSTRUCTION-CONTRACT.md). Every graded
assertion below names the sentence that tells the agent about it, quoted from `instruction.md`.
Two rows grade the verifier against itself rather than the submission and say so.

Checked with `python tools/tracecheck.py widen-pin-bind`.

## Graded assertions

| Verifier site | What it grades | Instruction sentence |
|---|---|---|
| `tests/test_outputs.py:114` test_frozen_truth_matches_the_model | the sealed model still reproduces every frozen answer. It compares the verifier against itself, so it can only fail on a drifted model or on a submission that reached into the verifier's own copies, which is what this sentence forbids | "The rest of the tree is replaced by our own copy before a program is run, a new file put beside those six included" |
| `tests/test_outputs.py:124` test_hand_case | each enumerated program's printed lines, exactly, and that the program was not altered | "Nothing else is printed." |
| `tests/test_outputs.py:133` test_every_nonce_program_matches | the same, for every program generated from the seed drawn after the run | "has to get through inside 60 seconds" |
| `tests/test_outputs.py:152` test_every_family_is_represented | that the generated population still covers all ten families. It grades the verifier's generator rather than the binder, and fails when a submission has rewritten it, which is what this sentence forbids | "The rest of the tree is replaced by our own copy before a program is run, a new file put beside those six included" |
| artifact `/app/res/kind.py` | the file is collected and nothing else is | "The files you may change are" and "The rest of the tree is replaced by our own copy before a program is run, a new file put beside those six included" |
| artifact `/app/res/pick.py` | the file is collected and nothing else is | "The files you may change are" and "The rest of the tree is replaced by our own copy before a program is run, a new file put beside those six included" |
| artifact `/app/res/pin.py` | the file is collected and nothing else is | "The files you may change are" and "The rest of the tree is replaced by our own copy before a program is run, a new file put beside those six included" |
| artifact `/app/res/cost.py` | the file is collected and nothing else is | "The files you may change are" and "The rest of the tree is replaced by our own copy before a program is run, a new file put beside those six included" |
| artifact `/app/res/best.py` | the file is collected and nothing else is | "The files you may change are" and "The rest of the tree is replaced by our own copy before a program is run, a new file put beside those six included" |
| artifact `/app/res/walk.py` | the file is collected and nothing else is | "The files you may change are" and "The rest of the tree is replaced by our own copy before a program is run, a new file put beside those six included" |
| `tests/test.sh:35` a 60 s clock | the wall clock on the half that runs the submission, which is the execution limit | "has to get through inside 60 seconds" |
| `tests/cases.py` case one-only | a single survivor wins with nothing to beat | "A candidate left on its own survives and wins, having nothing to beat" |
| `tests/cases.py` case plain-best | an entry better at one slot and equal elsewhere is the winner, not an ambiguity | "The winner is the candidate that is no worse than every other surviving candidate at every one of those numbers and better than it at one of them" |
| `tests/cases.py` case cross-sum | two entries whose costs cross are ambiguous although their totals differ | "Where no candidate beats all the others the call is ambiguous" |
| `tests/cases.py` case cross-even | the same from the other side, with the totals equal | "Where no candidate beats all the others the call is ambiguous" |
| `tests/cases.py` case ret-decides | the result cost decides between entries that tie at every slot | "the steps from the kind the entry gives back to the kind the call was asked for" |
| `tests/cases.py` case ret-free | those same entries are ambiguous when the call is asked for nothing | "nothing when the call was asked for nothing" |
| `tests/cases.py` case nest-expect | a call in a slot binds by what that slot asks for, so it binds two ways | "What a slot asks for is what a call sitting in it is bound asking for" |
| `tests/cases.py` case nest-dead | a slot whose call has no binding puts that trial aside; another entry still takes the call | "so does a call in a slot that comes back ambiguous or with no binding" |
| `tests/cases.py` case nest-amb | an ambiguous call in an open slot puts that trial aside, and a plain entry survives | "so does a call in a slot that comes back ambiguous or with no binding" |
| `tests/cases.py` case path-short | the shorter of two chains is the number of steps, which makes the call ambiguous | "the number of steps between them is the length of the shortest such chain" |
| `tests/cases.py` case path-tally | the same read off the tally rather than off the winner | "where n adds up every number that every call of every winning trial that was kept was judged on" |
| `tests/cases.py` case open-lub | two slots standing at kinds that meet at one kind settle the entry there | "the kind every open slot rises to that itself rises to every other kind they all rise to" |
| `tests/cases.py` case open-none | two least common kinds side by side settle nothing | "Where there is no such kind, or the settled kind does not rise to the entry's bound, the trial is put aside" |
| `tests/cases.py` case open-first | the first open slot's kind is not the settled kind | "the kind every open slot rises to that itself rises to every other kind they all rise to" |
| `tests/cases.py` case bound-under | an entry settled below its bound is taken | "the settled kind does not rise to the entry's bound" |
| `tests/cases.py` case bound-over | an entry settled above its bound is put aside and a plain entry takes the call | "the settled kind does not rise to the entry's bound" |
| `tests/cases.py` case bound-none | a settled kind that does not reach the bound at all | "the settled kind does not rise to the entry's bound" |
| `tests/cases.py` case open-free | an open slot holding a call binds it asking for nothing | "binds those slots first, in slot order, each asking for nothing" |
| `tests/cases.py` case open-noslot | an open entry with no open slot is never taken | "open entry with no open slot is never taken" |
| `tests/cases.py` case arity | an entry of the same name taking a different number of slots is not a candidate | "The candidates of a call are the entries carrying its name that take exactly as many slots as the call has arguments" |
| `tests/cases.py` case no-entry | a name with no entry of that slot count has no binding | "where none survives the call has no binding" |
| `tests/cases.py` case val-norise | a value that does not rise to its slot puts the trial aside | "An argument that does not rise to what its slot asks for puts the trial aside" |
| `tests/cases.py` case pin-drop | an entry settled by a trial that then loses is not pinned, and the next expression shows it | "A trial that is put aside or beaten leaves none of its pins behind" |
| `tests/cases.py` case pin-inside | a pin made at one slot is in force at the slots after it, which drops the entry there | "A pin made while one slot was being bound stands for the slots bound after it in the same trial" |
| `tests/cases.py` case pin-holds | a pinned entry is not settled again and the kind it holds costs steps | "An entry that is already pinned is not settled again and its open slots ask for the kind it holds" |
| `tests/cases.py` case pin-order | the pins of the arguments are printed before the entry's own | "hands its own back, in the order they were made, with the pin of the winning entry itself last" |
| `tests/cases.py` case pin-slots | the open slots are bound before the others, so they pin first | "binds those slots first, in slot order, each asking for nothing" and "The remaining slots are bound after that, in slot order, each asking for the kind it is declared with" |
| `tests/cases.py` case amb-quiet | an expression with no binding prints one line and leaves no pin behind | "An expression that is ambiguous prints `res <ask> amb` and one with no binding prints `res <ask> none`, and nothing else" |
| `tests/cases.py` case memo-pins | one call reached twice under pins that differ gives two different answers | "Every candidate is tried on its own, against the pins standing when the call was reached" |
| `tests/cases.py` case memo-asks | the same call number in two expressions is not the same call | "Expressions are bound in the order they are written" |
| `tests/cases.py` case order-pre | the bind lines run outermost first and left to right | "prints `bind <ask> <call> <entry>` for every call it bound, the outermost first and then the arguments of each call left to right" |
| `tests/cases.py` case tally-ret | the tally carries the result costs as well as the slot costs | "where n adds up every number that every call of every winning trial that was kept was judged on" |
| `tests/seal/model.py:45-72` read | the program grammar: kinds, rise steps, entries, open entries with their bound, values and expressions, numbered in declaration order | "Entries are numbered from 0 in the order they are declared" |
| `tests/seal/model.py:74-94` tree | the expression grammar and the numbering of the calls inside one expression | "The calls inside one expression are numbered from 0 too" |
| `tests/seal/model.py:97-115` closure | the steps between two kinds as the shortest chain, and a kind rising to itself in none | "A kind rises to itself in no steps." |
| `tests/seal/model.py:117-137` front | the comparison between survivors, and ambiguity when no candidate beats the rest | "The winner is the candidate that is no worse than every other surviving candidate at every one of those numbers and better than it at one of them" |
| `tests/seal/model.py:150-156` Run.settle | the settled kind of an open entry as the single least common kind | "the kind every open slot rises to that itself rises to every other kind they all rise to" |
| `tests/seal/model.py:157-179` Run.call | candidates by name and slot count, and what a call with no survivor or no winner comes back as | "Where no candidate beats all the others the call is ambiguous" and "where none survives the call has no binding" |
| `tests/seal/model.py:180-212` Run.try_one, open slots | open slots bound first asking for nothing, the bound checked against the settled kind, an entry with no open slot dropped | "binds those slots first, in slot order, each asking for nothing" and "open entry with no open slot is never taken" |
| `tests/seal/model.py:213-233` Run.try_one, the other slots | the remaining slots asking for their own kinds, each costing the steps its argument had to rise, and a pin in force at the slots after it | "A slot costs the steps from the kind its argument stands at to the kind the slot asks for" and "A pin made while one slot was being bound stands for the slots bound after it in the same trial" |
| `tests/seal/model.py:234-242` Run.try_one, the last cost | the result cost against the kind the call was asked for, and the entry's own pin coming last | "puts the trial aside when it does not rise there" and "hands its own back, in the order they were made, with the pin of the winning entry itself last" |
| `tests/seal/model.py:243-262` expect | the printed lines of every expression in file order, the pins kept between them, and the tally | "keeps what its winning trial pinned before the next one starts" and "then `res <ask> <kind>` with the kind its outermost entry gives back" |
| `tests/seal/model.py:139-148` Run | holds the pins that stand between expressions and the tally that accumulates over them | "Expressions are numbered from 0 in the order they are written" |
| `tests/seal/model.py:36-43` Call | a call and its number inside its expression; no rule of its own | "every expression is a call, and every call has at least one argument" |

## Readings

Readings a competent solver might try, from the four clusters, from the model's prior about how
a call is bound, and from what the shipped tree does. Each was implemented as a cheat by
`authoring/widen-pin-bind/emit.py` and run against the reference over the enumerated set and a
generated sample, so the separating case below is measured rather than argued. The one reading
that turned out to be unobservable - an expression with no binding printing what its trials
bound - is ruled out by the frozen trace writer rather than by the submission, and was dropped
rather than shipped as a cheat that could not fail.

| Reading | Sentence or published example that rules it out | Case that separates it |
|---|---|---|
| `amb-tie` | "and better than it at one of them" | `nest-amb`, one of 3 enumerated programs it fails; it moves 24.0% of a generated sample |
| `arity-any` | "the entries carrying its name that take exactly as many slots as the call has arguments" | `arity`, one of 2 enumerated programs it fails; it moves 14.6% of a generated sample |
| `bind-post` | "the outermost first and then the arguments of each call left to right" | `order-pre`, one of 10 enumerated programs it fails; it moves 59.4% of a generated sample |
| `bound-flip` | "the settled kind does not rise to the entry's bound" | `bound-under`, one of 11 enumerated programs it fails; it moves 43.8% of a generated sample |
| `bound-skip` | "the settled kind does not rise to the entry's bound" | `bound-none`, one of 2 enumerated programs it fails; it moves 5.2% of a generated sample |
| `lex-first` | "no worse than every other surviving candidate at every one of those numbers" | `cross-sum`, one of 3 enumerated programs it fails; it moves 16.7% of a generated sample |
| `memo-flat` | "Every candidate is tried on its own, against the pins standing when the call was reached" | `memo-pins`, one of 1 enumerated programs it fails; it moves 12.5% of a generated sample |
| `memo-site` | "The calls inside one expression are numbered from 0 too" | `memo-asks`, one of 3 enumerated programs it fails; it moves 89.6% of a generated sample |
| `nest-bottom` | "What a slot asks for is what a call sitting in it is bound asking for" | `nest-expect`, one of 12 enumerated programs it fails; it moves 75.0% of a generated sample |
| `one-amb` | "A candidate left on its own survives and wins, having nothing to beat" | `one-only`, one of 21 enumerated programs it fails; it moves 87.5% of a generated sample |
| `open-first` | "the kind every open slot rises to that itself rises to every other kind they all rise to" | `open-first`, one of 2 enumerated programs it fails; it moves 5.2% of a generated sample |
| `open-high` | "the kind every open slot rises to that itself rises to every other kind they all rise to" | `open-lub`, one of 1 enumerated programs it fails; it moves 5.2% of a generated sample |
| `open-minimal` | "that itself rises to every other kind they all rise to" | `open-none`, one of 1 enumerated programs it fails; it moves 3.1% of a generated sample |
| `path-any` | "the number of steps between them is the length of the shortest such chain" | `path-short`, one of 2 enumerated programs it fails; it moves 9.4% of a generated sample |
| `path-long` | "the number of steps between them is the length of the shortest such chain" | `path-short`, one of 2 enumerated programs it fails; it moves 12.5% of a generated sample |
| `pin-blind` | "A pin made while one slot was being bound stands for the slots bound after it in the same trial" | `pin-inside`, one of 2 enumerated programs it fails; it moves 13.5% of a generated sample |
| `pin-eager` | "A trial that is put aside or beaten leaves none of its pins behind" | `pin-drop`, one of 3 enumerated programs it fails; it moves 30.2% of a generated sample |
| `pin-first` | "with the pin of the winning entry itself last" | `pin-order`, one of 2 enumerated programs it fails; it moves 8.3% of a generated sample |
| `pin-refresh` | "An entry that is already pinned is not settled again and its open slots ask for the kind it holds" | `pin-holds`, one of 3 enumerated programs it fails; it moves 30.2% of a generated sample |
| `ret-free` | "the steps from the kind the entry gives back to the kind the call was asked for" | `ret-decides`, one of 5 enumerated programs it fails; it moves 50.0% of a generated sample |
| `ret-nocheck` | "puts the trial aside when it does not rise there" | `ret-decides`, one of 7 enumerated programs it fails; it moves 54.2% of a generated sample |
| `slots-left` | "binds those slots first, in slot order, each asking for nothing" | `pin-slots`, one of 1 enumerated programs it fails; it moves 4.2% of a generated sample |
| `sum-lowest` | "The winner is the candidate that is no worse than every other surviving candidate at every one of those numbers and better than it at one of them" | `cross-sum`, one of 2 enumerated programs it fails; it moves 13.5% of a generated sample |
| `tally-slots` | "where n adds up every number that every call of every winning trial that was kept was judged on" | `tally-ret`, one of 3 enumerated programs it fails; it moves 24.0% of a generated sample |

## Shortcuts

Every strategy below was run through the real verifier. The fraction is how many of a
102-program sample (the 32 enumerated programs plus 70 generated ones) it reproduced exactly:
all-or-nothing grading turns a strategy that matches two in five into a 0, and the fraction is
what says whether the population is exercising the rule or the strategy is just lucky.

| Strategy | Result |
|---|---|
| the shipped tree unchanged (nop) | 0; reproduces 18 of 102 programs, 12 of the 32 enumerated |
| constant: no binding for every expression (`cheat-const-none.sh`) | 0; reproduces 8 of 102, 5 enumerated - the expressions that genuinely have none |
| the worked example's record replayed for every expression (`cheat-const-tiny.sh`) | 0; reproduces 1 of 102 |
| positional: always the first entry that fits (`cheat-pos-first.sh`) | 0; reproduces 43 of 102, 23 enumerated |
| positional: always the last entry that fits (`cheat-pos-last.sh`) | 0; reproduces 44 of 102, 22 enumerated |
| the frozen answers for all 32 enumerated programs, replayed (`cheat-forge-hand.sh`) | 0; reproduces all 32 enumerated and 6 of 70 generated |

## Tolerances

There is no numeric tolerance: every graded program is compared line for line. The one limit is
the wall clock on the half that runs the submission, and it is stated in the brief.

| Tolerance or limit | Independent implementation | Measured |
|---|---|---|
| `tests/test.sh:35` a 60 s clock on the graded set | `authoring/widen-pin-bind/variants/undo-log` and `authoring/widen-pin-bind/variants/front-set`, both written apart from the reference, and `tests/seal/model.py` | the 358-program set takes 0.23 s under undo-log, 0.46 s under front-set and 0.43 s under the reference, so the limit is 130 to 260 times the time a correct binder needs. `authoring/widen-pin-bind/slow/walk.py`, exactly correct with no memo, takes 330 s on one `deep` program alone and 8.0 to 9.3 s on each `wide` one |
