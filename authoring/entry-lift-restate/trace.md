# Instruction trace: entry-lift-restate

Walked from the verifier toward the instruction (docs/INSTRUCTION-CONTRACT.md). Every graded
assertion, every enumerated case, every rule the sealed model applies, every collected file and
the wall clock, each against the sentence that tells the agent about it. Checked with
`python tools/tracecheck.py entry-lift-restate`.

## Graded assertions

| Verifier site | What it grades | Instruction sentence |
|---|---|---|
| `tests/test_outputs.py:114` test_frozen_truth_matches_the_model | the sealed side agrees with itself before it judges anything; grades nothing of the submission | not a rule about the submission, but it decides whether grading happens at all: the rules it re-checks are the ones every other row cites, headed by "A question is answered by settling the board from nothing" |
| `tests/test_outputs.py:124` test_hand_case | every enumerated program's trace, line for line, against the frozen answers | "A question is answered by settling the board from nothing, over the entries that stand above that question in the file" |
| `tests/test_outputs.py:133` test_every_nonce_program_matches | every generated program's trace against the sealed model, exactly | "The graded set is three journals of each of those two sizes" |
| `tests/test_outputs.py:152` test_every_family_is_represented | that the generated population covers all twelve families | "The graded set is three journals of each of those two sizes, three hundred and sixty smaller ones and thirty-eight written by hand" |
| `tests/cases.py:19` case climb-up | a name absent in a section is taken from the section it links to | "An empty one sends the reading on to the section this one links to and the same rule applies there" |
| `tests/cases.py:25` case clr-goes-on | an emptied slot leaves the climb free to go on | "`clr n` empties that slot" with "An empty one sends the reading on to the section this one links to" |
| `tests/cases.py:31` case cut-stops | a masked slot ends the reading where an emptied one would not | "A masked slot ends the reading with nothing found" |
| `tests/cases.py:37` case cut-then-set | writing into a masked slot leaves it holding a number | "it holds a number, or stands masked, or is empty" with "`set n v` puts v in the slot for name n" |
| `tests/cases.py:43` case climb-loop | a climb round two linked sections ends rather than running for ever | "So does one that comes to a section it has already been at" |
| `tests/cases.py:49` case climb-self | a section linked to itself ends the climb at once | "So does one that comes to a section it has already been at" |
| `tests/cases.py:56` case add-writes-here | a step reads through the climb and writes where the journal is | "`add n d` reads n from that section by the rule above and, when the reading finds a number, puts that number and d together in the slot for n there" |
| `tests/cases.py:62` case add-finds-none | a step over a name nothing holds does nothing at all | "When the reading finds nothing the entry does nothing" |
| `tests/cases.py:68` case add-after-clr | an emptied name is not a zero | "When the reading finds nothing the entry does nothing" |
| `tests/cases.py:74` case add-after-cut | a masked name is not a zero, and the mask is still standing after | "A masked slot ends the reading with nothing found" |
| `tests/cases.py:82` case sec-carries | an entry writes in the section a `sec` entry moved the journal into | "Each is applied in the section the walk is in when it is reached" |
| `tests/cases.py:88` case sec-starts-at-zero | a write before any `sec` entry lands in section 0 | "A pass begins from nothing: every slot empty, no section linked, the journal in section 0" |
| `tests/cases.py:95` case sec-resets-each-pass | the second pass of a settle starts in section 0, not where the first ended | "A pass begins from nothing: every slot empty, no section linked, the journal in section 0" |
| `tests/cases.py:101` case cut-then-clr | emptying a masked slot takes the mask off | "`clr n` empties that slot" with "it holds a number, or stands masked, or is empty" |
| `tests/cases.py:107` case later-entries-ignored | a question is answered over the entries above it only | "over the entries that stand above that question in the file" |
| `tests/cases.py:114` case gate-blocks-sec | a refused condition leaves the journal's section where it was | "and otherwise does nothing at all, a `sec` or `lnk` entry included" |
| `tests/cases.py:120` case gate-blocks-lnk | a refused condition links nothing | "and otherwise does nothing at all, a `sec` or `lnk` entry included" |
| `tests/cases.py:126` case gate-passes | the must-still-work side: a condition that is met fires, section entries included | "An entry written behind `if g w` is applied only when reading g from that section finds exactly w" |
| `tests/cases.py:132` case gate-reads-here | the condition climbs from the section the journal is in | "is applied only when reading g from that section finds exactly w" |
| `tests/cases.py:138` case gate-reads-sec | the condition is read in that section rather than in section 0 | "is applied only when reading g from that section finds exactly w" |
| `tests/cases.py:146` case once-wakes | a sleeping entry whose reading finds its number wakes, and the pass count says so | "the sleeping entry with the lowest number whose reading of g finds exactly w wakes and another pass runs" with "Passes are counted from one" |
| `tests/cases.py:152` case once-no-retest | a woken entry is applied again even after its own write ends its condition | "An entry that has woken is applied by the passes after it and is not read for again" |
| `tests/cases.py:159` case once-one-per-pass | one wake per pass, lowest number first, so waking one can keep another asleep for good | "the sleeping entry with the lowest number whose reading of g finds exactly w wakes and another pass runs" |
| `tests/cases.py:165` case once-two-passes | two entries waking one after the other give three passes | "Passes are counted from one" with "The pass count in either line is the one from the settle that answered that question" |
| `tests/cases.py:172` case once-sec-at-pos | the sleeping condition is read in the section its own place had | "That reading is taken in the section the walk was in at the place of that entry during the pass just finished" |
| `tests/cases.py:178` case once-sec-mirror | the same rule the other way round, where the condition is met | "That reading is taken in the section the walk was in at the place of that entry during the pass just finished" |
| `tests/cases.py:184` case once-reads-final | the sleeping condition is read over the finished board, writes made after its place included | "over the board that pass finished with" |
| `tests/cases.py:191` case once-resleeps | a settle after a withdrawal starts every sleeping entry asleep again | "every settle starts with all of them asleep however an earlier one ended" |
| `tests/cases.py:197` case once-lifted | a sleeping entry in a withdrawn change never wakes | "They write nothing and move the journal nowhere" |
| `tests/cases.py:205` case off-overwritten | withdrawing a change a later change wrote over leaves the board where it stood | "The second line comes out `get 0 4 - 1` and it should read `get 0 4 20 1`" with "A question is answered by settling the board from nothing" |
| `tests/cases.py:213` case off-uncovers | withdrawing the only write leaves the name standing at what is above it | "A question is answered by settling the board from nothing, over the entries that stand above that question in the file" |
| `tests/cases.py:221` case mask-lifted | the late one: a reading that found nothing where a mask stood finds once the mask goes, and the sleeping entry it decides wakes on the pass after | "A masked slot ends the reading with nothing found" with "every settle starts with all of them asleep however an earlier one ended" |
| `tests/cases.py:234` case off-moves-writes | a withdrawn change's section entry moves the journal nowhere, so later writes land elsewhere | "They write nothing and move the journal nowhere" |
| `tests/cases.py:241` case off-unlinks | a withdrawn change's link entry links nothing, so the climb stops | "The entries of a withdrawn change take no part in any pass" |
| `tests/cases.py:247` case off-twice | withdrawing twice and putting back twice are each the same as once | "Withdrawing a change already withdrawn changes nothing, and so does putting back one that already stands" |
| `tests/cases.py:256` case all-shape | the three counts and the three runs of detail lines, in order of section and then of name | "held counts the slots holding a number, masked the slots standing masked and linked the sections linking somewhere" with "Each of the three runs goes in order of section and then of name" |
| `tests/cases.py:263` case all-empty | an empty board prints its counts and no detail lines at all | "Nothing else is printed" |
| `tests/cases.py:270` case plain-run | the everyday case: brackets, a step, an emptied name and four readings, with nothing exotic | "A question is answered by settling the board from nothing" |
| artifact `/app/cf/book.py` | only the declared files are collected | "The files you may change are `/app/cf/book.py`, `/app/cf/sect.py`, `/app/cf/step.py`, `/app/cf/gate.py`, `/app/cf/wake.py`, `/app/cf/walk.py` and `/app/cf/tell.py`" |
| artifact `/app/cf/sect.py` | only the declared files are collected | "The files you may change are `/app/cf/book.py`, `/app/cf/sect.py`, `/app/cf/step.py`, `/app/cf/gate.py`, `/app/cf/wake.py`, `/app/cf/walk.py` and `/app/cf/tell.py`" |
| artifact `/app/cf/step.py` | only the declared files are collected | "The files you may change are `/app/cf/book.py`, `/app/cf/sect.py`, `/app/cf/step.py`, `/app/cf/gate.py`, `/app/cf/wake.py`, `/app/cf/walk.py` and `/app/cf/tell.py`" |
| artifact `/app/cf/gate.py` | only the declared files are collected | "The files you may change are `/app/cf/book.py`, `/app/cf/sect.py`, `/app/cf/step.py`, `/app/cf/gate.py`, `/app/cf/wake.py`, `/app/cf/walk.py` and `/app/cf/tell.py`" |
| artifact `/app/cf/wake.py` | only the declared files are collected | "The files you may change are `/app/cf/book.py`, `/app/cf/sect.py`, `/app/cf/step.py`, `/app/cf/gate.py`, `/app/cf/wake.py`, `/app/cf/walk.py` and `/app/cf/tell.py`" |
| artifact `/app/cf/walk.py` | only the declared files are collected | "The files you may change are `/app/cf/book.py`, `/app/cf/sect.py`, `/app/cf/step.py`, `/app/cf/gate.py`, `/app/cf/wake.py`, `/app/cf/walk.py` and `/app/cf/tell.py`" |
| artifact `/app/cf/tell.py` | only the declared files are collected | "The files you may change are `/app/cf/book.py`, `/app/cf/sect.py`, `/app/cf/step.py`, `/app/cf/gate.py`, `/app/cf/wake.py`, `/app/cf/walk.py` and `/app/cf/tell.py`" |
| `tests/worker.py:47` nothing else is collected | a file put beside the seven is never taken from the agent | "a new file put beside those seven included" |
| `tests/worker.py:45` the pristine overlay | the driver, the reader, the trace writer and the sample programs are the verifier's own | "The rest of the tree is replaced by our own copy before a program is run" |
| `tests/test.sh:15` a 60 s clock on the graded run | the whole graded set must finish inside it | "all of it has to get through inside 60 seconds" |
| `tests/seal/model.py:48-78` read_program | entry lines are numbered from 0 in order, and `open`, `shut`, `off`, `back`, `get`, `all` take no number | "Entry lines are numbered from 0 in the order they appear" |
| `tests/seal/model.py:56-61` read_program, brackets | a bracket is a change, a bare entry is a change of its own, both numbered from 0 as they open | "changes are numbered from 0 in the order they are opened, counting a bracket and a bare entry alike" |
| `tests/seal/model.py:65-70` read_program, guards | an entry may carry `if g w` or `once g w` ahead of it | "Any entry may be written behind `if g w` or behind `once g w`" |
| `tests/seal/model.py:39-45` Row | an entry holds its kind, its two numbers, its condition and the change that owns it | "An entry line makes one change" |
| `tests/seal/model.py:83-113` Slots | each key keeps the ordered positions that wrote it, which is an implementation choice and grades nothing on its own | "A question is answered by settling the board from nothing" |
| `tests/seal/model.py:144-152` Sealed._look, the local slot | a reading takes the number in that section's slot for the name | "Reading a name in a section takes the number the slot for it there holds" |
| `tests/seal/model.py:155-156` Sealed._look, a mask | a masked slot ends the reading with nothing found | "A masked slot ends the reading with nothing found" |
| `tests/seal/model.py:157-160` Sealed._look, the link | an empty slot sends the reading to the section this one links to; one linking nowhere ends it | "A reading that comes to a section linking nowhere ends with nothing found" |
| `tests/seal/model.py:145-147` Sealed._look, the revisit | a reading that arrives where it has been ends with nothing found | "So does one that comes to a section it has already been at" |
| `tests/seal/model.py:162-164` Sealed.secat | the section an entry acts in is the one the last firing `sec` entry before it moved to, and 0 before any | "A pass begins from nothing: every slot empty, no section linked, the journal in section 0" |
| `tests/seal/model.py:168-172` Sealed.awake | a withdrawn entry is out, and a `once` entry is out until it has woken in this settle | "The entries of a withdrawn change take no part in any pass" |
| `tests/seal/model.py:181-182` Sealed.figure, the condition | an entry behind `if g w` fires only when the reading of g from its section finds exactly w | "An entry written behind `if g w` is applied only when reading g from that section finds exactly w" |
| `tests/seal/model.py:183-186` Sealed.figure, `sec` and `lnk` | a refused condition leaves the journal's section and the chain alone | "and otherwise does nothing at all, a `sec` or `lnk` entry included" |
| `tests/seal/model.py:188-192` Sealed.figure, `add` | a step reads through the climb, writes into the section the walk carries, and does nothing when the reading finds nothing | "puts that number and d together in the slot for n there" with "When the reading finds nothing the entry does nothing" |
| `tests/seal/model.py:193-194` Sealed.figure, `set`, `clr`, `cut` | a write holds a number, an empty leaves the slot empty, a cut masks it | "`set n v` puts v in the slot for name n, `clr n` empties that slot, `cut n` masks it" |
| `tests/seal/model.py:261-283` Sealed.settle, the pass loop | the board is worked out again from nothing for every question, passes counted from one | "A question is answered by settling the board from nothing" with "Passes are counted from one" |
| `tests/seal/model.py:262-264` Sealed.settle, the sleepers | every settle starts every `once` entry asleep, whatever the last one woke | "every settle starts with all of them asleep however an earlier one ended" |
| `tests/seal/model.py:272-279` Sealed.settle, the wake | the lowest-numbered sleeping entry whose reading finds its number wakes, one per pass, read in its own section over the finished board | "the sleeping entry with the lowest number whose reading of g finds exactly w wakes and another pass runs" with "That reading is taken in the section the walk was in at the place of that entry during the pass just finished, over the board that pass finished with" |
| `tests/seal/model.py:281-283` Sealed.settle, no retest | a woken entry is applied by the later passes without being read for again | "An entry that has woken is applied by the passes after it and is not read for again" |
| `tests/seal/model.py:285-299` Sealed.whole | the board is the last write of every slot, split into held, masked and linked | "held counts the slots holding a number, masked the slots standing masked and linked the sections linking somewhere" |
| `tests/seal/model.py:302-339` expect, the questions | `get` prints its section, name, value and pass count with a dash for nothing found; `all` prints the counts and the three runs | "with `-` in place of the value when the reading finds nothing" |
| `tests/seal/model.py:315-322` expect, withdrawal | `off` takes a change out and `back` puts it in, and doing either twice changes nothing | "Withdrawing a change already withdrawn changes nothing, and so does putting back one that already stands" |
| `tests/seal/model.py:330-338` expect, the detail lines | the held run, then the masked run, then the linked run, each in order of section and then of name | "Each of the three runs goes in order of section and then of name" |

## Readings

| Reading | Sentence or published example that rules it out | Case that separates it |
|---|---|---|
| climb-past-mask | "A masked slot ends the reading with nothing found" | cut-stops |
| climb-stops-empty | "An empty one sends the reading on to the section this one links to and the same rule applies there" | clr-goes-on |
| climb-no-guard | "So does one that comes to a section it has already been at" | climb-self, and the clock on the worker, since the reading does not end |
| add-takes-zero | "When the reading finds nothing the entry does nothing" | add-finds-none |
| add-reads-local | "`add n d` reads n from that section by the rule above" | add-writes-here |
| add-writes-found | "puts that number and d together in the slot for n there" | add-writes-here |
| set-keeps-mask | "it holds a number, or stands masked, or is empty" | cut-then-set |
| clr-keeps-mask | "`clr n` empties that slot" | cut-then-clr |
| gate-moves-sec | "and otherwise does nothing at all, a `sec` or `lnk` entry included" | gate-blocks-sec |
| gate-moves-lnk | "and otherwise does nothing at all, a `sec` or `lnk` entry included" | gate-blocks-lnk |
| gate-reads-zero | "is applied only when reading g from that section finds exactly w" | gate-reads-sec |
| gate-reads-local | "reading g from that section" reads by the climbing rule, since "the same rule applies there" | gate-reads-here |
| once-all-at-once | "the sleeping entry with the lowest number whose reading of g finds exactly w wakes and another pass runs" | once-one-per-pass |
| once-highest-first | "the sleeping entry with the lowest number whose reading of g finds exactly w wakes" | once-one-per-pass |
| once-retested | "An entry that has woken is applied by the passes after it and is not read for again" | once-no-retest |
| once-keeps-awake | "every settle starts with all of them asleep however an earlier one ended" | once-resleeps |
| once-wakes-lifted | "They write nothing and move the journal nowhere" | once-lifted |
| once-sec-at-end | "That reading is taken in the section the walk was in at the place of that entry during the pass just finished" | once-sec-mirror, once-sec-at-pos |
| once-sec-zero | "taken in the section the walk was in at the place of that entry" | once-sec-mirror |
| once-reads-at-pos | "over the board that pass finished with" | once-reads-final |
| lift-keeps-sec | "They write nothing and move the journal nowhere" | off-moves-writes |
| lift-keeps-lnk | "The entries of a withdrawn change take no part in any pass" | off-unlinks |
| off-toggles | "Withdrawing a change already withdrawn changes nothing" | off-twice |
| settle-whole-file | "over the entries that stand above that question in the file" | later-entries-ignored |
| all-counts-masked | "held counts the slots holding a number, masked the slots standing masked" | all-shape |
| all-masked-first | "`v <section> <name> <value>` for every slot holding a number, then `m <section> <name>` for every masked slot" | all-shape |
| all-sorts-by-name | "Each of the three runs goes in order of section and then of name" | all-shape |
| get-zero-for-nothing | "with `-` in place of the value when the reading finds nothing" | add-finds-none |
| passes-from-zero | "Passes are counted from one" | once-wakes |
| passes-flat | "the sleeping entry with the lowest number whose reading of g finds exactly w wakes and another pass runs" | once-wakes, once-two-passes |
| withdrawal is the undo of what the change wrote | ruled out by the published example: "The second line comes out `get 0 4 - 1` and it should read `get 0 4 20 1`" | off-overwritten, and the shipped tree scores it as the nop |
| an entry is reopened only when a value it read moves, never when a mask it stopped at goes | "A masked slot ends the reading with nothing found" leaves the reading resting on the mask as much as on a value | mask-lifted |
| a lifted change's writes are kept and only its later effects dropped | "The entries of a withdrawn change take no part in any pass" | off-uncovers |

## Shortcuts

| Strategy | Result |
|---|---|
| the shipped tree unchanged (nop) | 0. The container trial scores it 0 with 19 of 40 graded assertions failing; on the host it settles 21 of the 38 enumerated programs and fails the rest |
| constant: the commonest value of every graded field in the frozen answers (`cheat-const-common`) | 0. It settles 4 of 38 enumerated programs and 2% of a sampled generated population |
| positional: the last plain write to that exact slot, ignoring the climb, the conditions and withdrawal (`cheat-pos-last-write`) | 0. It settles 7 of 38 enumerated programs and none of the sampled generated population |
| the worked example's output replayed, and the frozen answers carried for every enumerated program (`cheat-forge-hand`) | 0. It settles all 38 enumerated programs and fails 98% of the sampled generated population, which is what the nonce seed is for |

## Tolerances

| Tolerance or limit | Independent implementation | Measured |
|---|---|---|
| `tests/test.sh:15` a 60 s clock on the graded run, stated as "all of it has to get through inside 60 seconds" | `authoring/entry-lift-restate/variants/ok-flat` and `authoring/entry-lift-restate/variants/ok-coarse`, both written apart from the reference, and `tests/seal/model.py`, written apart from all three | the six scale programs take 1.93 s under ok-flat and 2.33 s under ok-coarse on the authoring host, and the whole graded set takes 3.11 s inside the verifier container under 1 CPU and 2048 MB, against the 60 s clock. The same six programs take 70.1 s and 75.7 s each under `authoring/entry-lift-restate/naive.py`, which is exactly correct |
| there is no numeric tolerance anywhere | the trace is compared string for string against `tests/seal/model.py` | 404 graded programs, reference and model identical on every one |
