# Instruction trace: replay-match-drift

Walked from the verifier toward the instruction (docs/INSTRUCTION-CONTRACT.md). Every graded
assertion, every enumerated run file, every collected artifact, the clock and every rule the
sealed model applies has a row here with the sentence of `instruction.md` that tells the agent
about it. Re-run `python tools/tracecheck.py replay-match-drift` after any change to the brief,
to tests/, to the model, to the generator or to the environment.

## Graded assertions

| Verifier site | What it grades | Instruction sentence |
|---|---|---|
| `tests/test_outputs.py:120` test_the_model_still_reproduces_the_frozen_answers | the sealed model still reproduces every frozen answer, so a drifted model cannot redefine correct | "Every line of the printout but the last names the branch it belongs to" "a command issued prints `<b> go <kind> <i> <name>`, a result taken prints `<b> ok <kind> <i> <value>`" |
| `tests/test_outputs.py:130` test_hand_program | each enumerated run file's whole printout, line for line, against the frozen answers | "Every line of the printout but the last names the branch it belongs to" "Your engine is graded on run files you have not seen" |
| `tests/test_outputs.py:139` test_every_generated_program_matches | every generated run file's whole printout against the sealed model | "Your engine is graded on run files you have not seen" |
| `tests/test_outputs.py:158` test_every_family_is_represented | that the generated population still covers every family, so the exam cannot be shrunk | "Your engine is graded on run files you have not seen" |
| `tests/cases.py:10` case count-kind | a timer between two calls does not move the second call's count | "Commands are counted by kind, and the count of one kind is not moved by commands of any other" "Every count and every position here starts at zero" |
| `tests/cases.py:16` case count-same | one kind throughout, the ordinary side of the counting rule | "Commands are counted by kind, and the count of one kind is not moved by commands of any other" "The command at count `i` of its kind matches the `go` at position `i` among the `go` lines of that kind" |
| `tests/cases.py:21` case count-three | three kinds recorded in another order than the body issues them | "Commands are counted by kind, and the count of one kind is not moved by commands of any other" "`call` and `fire` issue one of kind `call`, `spawn` one of kind `child`, and `nap` one of kind `timer`" |
| `tests/cases.py:30` case name-drift | a recorded command under another name stops the run where it happens | "If that `go` carries another name the run stops there and prints `drift <kind> <i> <recorded name> <name asked for>`" |
| `tests/cases.py:36` case name-drift-kind | the same, on a kind whose own count is zero | "If that `go` carries another name the run stops there and prints `drift <kind> <i> <recorded name> <name asked for>`" "Commands are counted by kind, and the count of one kind is not moved by commands of any other" |
| `tests/cases.py:43` case pair-swap | two names of one kind answered in the opposite order | "the command at count `j` among the commands of that kind and name takes the `ok` at position `j` among the `ok` lines carrying that same kind and name" |
| `tests/cases.py:48` case pair-dup | one kind and name issued twice beside a third command | "the command at count `j` among the commands of that kind and name takes the `ok` at position `j` among the `ok` lines carrying that same kind and name" "a later `take` waits for the earliest command the branch has issued and not yet taken the result of" |
| `tests/cases.py:53` case pair-cross | one name used under two kinds, answered in the other order | "the command at count `j` among the commands of that kind and name takes the `ok` at position `j` among the `ok` lines carrying that same kind and name" |
| `tests/cases.py:58` case pair-order | answers in issue order, the ordinary side of the pairing rule | "the command at count `j` among the commands of that kind and name takes the `ok` at position `j` among the `ok` lines carrying that same kind and name" "`call`, `spawn` and `nap` then wait for that command's own result" |
| `tests/cases.py:65` case sched-mark | the branch whose result was recorded earlier runs first, whatever its number | "Otherwise the waiting branch whose mark is smallest goes, whatever its number and whatever order the branches started waiting in" "A branch that waits goes down with a mark, and the mark is the position in the history of the line that will release it" |
| `tests/cases.py:71` case sched-ready-first | a freshly forked branch runs before a waiting branch with a smaller mark | "A branch able to run without waiting for anything goes first, and among those the lowest numbered" "`fork` starts another branch at a label and keeps going itself; branches are numbered from 0 in the order they are forked" |
| `tests/cases.py:77` case sched-id | two branches able to run, taken lowest numbered first | "A branch able to run without waiting for anything goes first, and among those the lowest numbered" |
| `tests/cases.py:84` case sched-chain | a branch that resumes, issues again and goes down on a later mark | "A branch runs until it waits or ends" "For a command that is the line carrying its result" |
| `tests/cases.py:93` case take-first | a take reaches for the earliest command the branch has not taken | "a later `take` waits for the earliest command the branch has issued and not yet taken the result of" |
| `tests/cases.py:98` case take-none | a take with nothing untaken changes nothing | "A `take` with nothing untaken changes nothing" |
| `tests/cases.py:104` case sig-claim | two branches on one tag claim different lines as they go down | "For a `wait` it is the line of the signal the branch claims as it goes down, which is the earliest `sig` of that tag nobody has claimed yet" "`wait` waits for a signal with the tag it names" |
| `tests/cases.py:112` case sig-tags | several tags, each queued on its own | "For a `wait` it is the line of the signal the branch claims as it goes down, which is the earliest `sig` of that tag nobody has claimed yet" |
| `tests/cases.py:116` case sig-live | a signal taken after the live side opened | "A result the history does not carry, then or earlier, comes off the `r` lines in the order the branches take them, and is zero once those run out" "Every waiting branch can run again from that point, nothing waits again, and no command is matched against the history again however much of it is left" |
| `tests/cases.py:123` case edge-standstill | the history runs out mid-branch and the live side opens once | "When no branch can run and no waiting branch has a mark, the run has nothing left to replay. It prints `live`, once, before anything else it does" |
| `tests/cases.py:128` case edge-none | a body its history covers never prints the live line | "When no branch can run and no waiting branch has a mark, the run has nothing left to replay. It prints `live`, once, before anything else it does" |
| `tests/cases.py:133` case edge-empty | an empty history: the first command has nothing to wait for | "A branch waiting for something the history never recorded goes down with no mark at all" "When no branch can run and no waiting branch has a mark, the run has nothing left to replay. It prints `live`, once, before anything else it does" |
| `tests/cases.py:137` case edge-release-id | three branches released together, taken lowest numbered first | "Every waiting branch can run again from that point, nothing waits again, and no command is matched against the history again however much of it is left" "A branch able to run without waiting for anything goes first, and among those the lowest numbered" |
| `tests/cases.py:143` case edge-no-wait | nothing waits once the live side is open, so one branch runs on | "Every waiting branch can run again from that point, nothing waits again, and no command is matched against the history again however much of it is left" |
| `tests/cases.py:148` case edge-feed-out | results past the end of the value list are zero | "A result the history does not carry, then or earlier, comes off the `r` lines in the order the branches take them, and is zero once those run out" |
| `tests/cases.py:152` case edge-after-live-go | a command issued after the live side opened is not matched | "Every waiting branch can run again from that point, nothing waits again, and no command is matched against the history again however much of it is left" |
| `tests/cases.py:160` case edge-no-match-after | a kind with no recorded command at all | "A branch waiting for something the history never recorded goes down with no mark at all" |
| `tests/cases.py:168` case left-earliest | two recorded commands left over, the earliest named | "then it prints `drift left <kind> <i>` for the earliest such `go` in the history" |
| `tests/cases.py:173` case left-not-ok | a spare answer, signal or choice is not a failure | "Only `go` lines count for that. An `ok`, a `sig` or a `ch` that nobody took is not a failure" |
| `tests/cases.py:178` case left-unissued | a recorded command of a kind the body never issues | "then it prints `drift left <kind> <i>` for the earliest such `go` in the history" |
| `tests/cases.py:185` case left-after-live | the history is still owed a command after the live side opened | "then it prints `drift left <kind> <i>` for the earliest such `go` in the history" "Every waiting branch can run again from that point, nothing waits again, and no command is matched against the history again however much of it is left" |
| `tests/cases.py:192` case stop-mid | branch zero ends while another branch is still waiting | "Branch 0 ending ends the run, whatever the other branches are doing" "The run then prints `fin` and branch 0's accumulator" |
| `tests/cases.py:200` case ver-recorded | a recorded choice wins over the value the marker asks for | "`mark` takes the earliest `ch` of its own key that has not been taken" |
| `tests/cases.py:204` case ver-replay-zero | an unrecorded marker is zero while the run can still replay | "the value is zero while the run still has something to replay, and the marker's own second word once `live` has been printed" |
| `tests/cases.py:208` case ver-live-cur | an unrecorded marker takes the body's own value once live | "the value is zero while the run still has something to replay, and the marker's own second word once `live` has been printed" |
| `tests/cases.py:212` case ver-empty-zero | an empty history is still replaying until the run comes to a stop | "the value is zero while the run still has something to replay, and the marker's own second word once `live` has been printed" "When no branch can run and no waiting branch has a mark, the run has nothing left to replay. It prints `live`, once, before anything else it does" |
| `tests/cases.py:215` case ver-per-key | choices taken per key, in recorded order | "`mark` takes the earliest `ch` of its own key that has not been taken" |
| `tests/cases.py:219` case ver-branch | the marker's value decides which command the branch issues | "the value is zero while the run still has something to replay, and the marker's own second word once `live` has been printed" "Each branch has its own accumulator, starting at zero, and every result, signal and marker it takes goes into it" |
| `tests/cases.py:226` case over-steps | a body that runs past the step ceiling | "A body that executes more than 200000 ops prints `over` and nothing else" |
| `tests/cases.py:229` case parse-blank | blank lines in a run file are skipped by the grammar | "Blank lines are ignored" "Values are integers, and names, tags and keys are single words" |
| `tests/cases.py:233` case plain-ordinary | an everyday run file that an overconservative engine breaks | "A `b` line is one op of the workflow body, in the order the body runs them" "`call`, `spawn` and `nap` then wait for that command's own result" |
| artifact `/app/dur/tab.py` | collected for grading; nothing else is | "The files you may change are `/app/dur/tab.py`, `/app/dur/edge.py`, `/app/dur/pair.py`, `/app/dur/hold.py`, `/app/dur/sched.py`, `/app/dur/wake.py` and `/app/dur/ver.py`" "a new file put beside those seven is never read" |
| artifact `/app/dur/edge.py` | collected for grading; nothing else is | "The files you may change are `/app/dur/tab.py`, `/app/dur/edge.py`, `/app/dur/pair.py`, `/app/dur/hold.py`, `/app/dur/sched.py`, `/app/dur/wake.py` and `/app/dur/ver.py`" "a new file put beside those seven is never read" |
| artifact `/app/dur/pair.py` | collected for grading; nothing else is | "The files you may change are `/app/dur/tab.py`, `/app/dur/edge.py`, `/app/dur/pair.py`, `/app/dur/hold.py`, `/app/dur/sched.py`, `/app/dur/wake.py` and `/app/dur/ver.py`" "a new file put beside those seven is never read" |
| artifact `/app/dur/hold.py` | collected for grading; nothing else is | "The files you may change are `/app/dur/tab.py`, `/app/dur/edge.py`, `/app/dur/pair.py`, `/app/dur/hold.py`, `/app/dur/sched.py`, `/app/dur/wake.py` and `/app/dur/ver.py`" "a new file put beside those seven is never read" |
| artifact `/app/dur/sched.py` | collected for grading; nothing else is | "The files you may change are `/app/dur/tab.py`, `/app/dur/edge.py`, `/app/dur/pair.py`, `/app/dur/hold.py`, `/app/dur/sched.py`, `/app/dur/wake.py` and `/app/dur/ver.py`" "a new file put beside those seven is never read" |
| artifact `/app/dur/wake.py` | collected for grading; nothing else is | "The files you may change are `/app/dur/tab.py`, `/app/dur/edge.py`, `/app/dur/pair.py`, `/app/dur/hold.py`, `/app/dur/sched.py`, `/app/dur/wake.py` and `/app/dur/ver.py`" "a new file put beside those seven is never read" |
| artifact `/app/dur/ver.py` | collected for grading; nothing else is | "The files you may change are `/app/dur/tab.py`, `/app/dur/edge.py`, `/app/dur/pair.py`, `/app/dur/hold.py`, `/app/dur/sched.py`, `/app/dur/wake.py` and `/app/dur/ver.py`" "a new file put beside those seven is never read" |
| `tests/test.sh:34` a 60 s clock | the wall clock on the stage that runs the submitted engine | "All of the graded run files together have to finish inside 60 seconds of wall clock" "three carry twenty-four thousand commands on one branch against a history of forty-eight thousand lines" |
| `tests/seal/model.py:42-55` _split | the three line kinds of a run file | "A `b` line is one op of the workflow body, in the order the body runs them" "Blank lines are ignored" |
| `tests/seal/model.py:61-84` the history indexed | the three axes the rules count on | "Commands are counted by kind, and the count of one kind is not moved by commands of any other" "the command at count `j` among the commands of that kind and name takes the `ok` at position `j` among the `ok` lines carrying that same kind and name" "For a `wait` it is the line of the signal the branch claims as it goes down, which is the earliest `sig` of that tag nobody has claimed yet" |
| `tests/seal/model.py:106-110` leftover | the earliest recorded command no command matched | "then it prints `drift left <kind> <i>` for the earliest such `go` in the history" |
| `tests/seal/model.py:112-131` settle | what a branch is handed when it is woken, and where an unrecorded result comes from | "A result the history does not carry, then or earlier, comes off the `r` lines in the order the branches take them, and is zero once those run out" "a command issued prints `<b> go <kind> <i> <name>`, a result taken prints `<b> ok <kind> <i> <value>`" |
| `tests/seal/model.py:133-144` mark_for | the mark a waiting branch goes down with, and the signal it claims | "A branch that waits goes down with a mark, and the mark is the position in the history of the line that will release it" "For a command that is the line carrying its result" "For a `wait` it is the line of the signal the branch claims as it goes down, which is the earliest `sig` of that tag nobody has claimed yet" |
| `tests/seal/model.py:146-154` lay_down | a branch with no mark is set aside rather than queued | "A branch waiting for something the history never recorded goes down with no mark at all" |
| `tests/seal/model.py:158-177` the pick and the live side | ready before waiting, lowest number, smallest mark, and the standstill | "A branch able to run without waiting for anything goes first, and among those the lowest numbered" "Otherwise the waiting branch whose mark is smallest goes, whatever its number and whatever order the branches started waiting in" "When no branch can run and no waiting branch has a mark, the run has nothing left to replay. It prints `live`, once, before anything else it does" "Every waiting branch can run again from that point, nothing waits again, and no command is matched against the history again however much of it is left" |
| `tests/seal/model.py:187-215` issuing a command | the per-kind count, the name check and the answer pairing | "The command at count `i` of its kind matches the `go` at position `i` among the `go` lines of that kind" "If that `go` carries another name the run stops there and prints `drift <kind> <i> <recorded name> <name asked for>`" "the command at count `j` among the commands of that kind and name takes the `ok` at position `j` among the `ok` lines carrying that same kind and name" |
| `tests/seal/model.py:216-231` awaiting, taking and waiting | which result a branch waits for and what a take reaches for | "`call`, `spawn` and `nap` then wait for that command's own result" "a later `take` waits for the earliest command the branch has issued and not yet taken the result of" "A `take` with nothing untaken changes nothing" "`wait` waits for a signal with the tag it names" |
| `tests/seal/model.py:232-243` fork and the marker | a new branch, and what an unrecorded marker yields | "`fork` starts another branch at a label and keeps going itself; branches are numbered from 0 in the order they are forked" "`mark` takes the earliest `ch` of its own key that has not been taken" "the value is zero while the run still has something to replay, and the marker's own second word once `live` has been printed" |
| `tests/seal/model.py:244-262` the accumulator, the jumps and the end | what the accumulator holds and what ends the run | "Each branch has its own accumulator, starting at zero, and every result, signal and marker it takes goes into it" "Branch 0 ending ends the run, whatever the other branches are doing" "The run then prints `fin` and branch 0's accumulator" |
| `tests/seal/model.py:98-104` the step ceiling | a body past the ceiling ends over | "A body that executes more than 200000 ops prints `over` and nothing else" |

## Readings

Each wrong reading is a whole engine under `authoring/replay-match-drift/emit.py`, measured by
`python tools/readingcheck.py replay-match-drift`; all 21 are separated by the enumerated set.

| Reading | Sentence that rules it out | Case that separates it |
|---|---|---|
| sched-mark-first | "A branch able to run without waiting for anything goes first, and among those the lowest numbered" | sched-ready-first |
| sched-park-order | "Otherwise the waiting branch whose mark is smallest goes, whatever its number and whatever order the branches started waiting in" | plain-ordinary |
| sched-last-mark | "Otherwise the waiting branch whose mark is smallest goes, whatever its number and whatever order the branches started waiting in" | plain-ordinary |
| sched-ready-last | "A branch able to run without waiting for anything goes first, and among those the lowest numbered" | edge-no-wait |
| wake-no-claim | "For a `wait` it is the line of the signal the branch claims as it goes down, which is the earliest `sig` of that tag nobody has claimed yet" | sig-claim |
| wake-mark-is-go | "For a command that is the line carrying its result" | plain-ordinary |
| pair-kind-only | "the command at count `j` among the commands of that kind and name takes the `ok` at position `j` among the `ok` lines carrying that same kind and name" | pair-dup |
| pair-name-only | "the command at count `j` among the commands of that kind and name takes the `ok` at position `j` among the `ok` lines carrying that same kind and name" | pair-cross |
| pair-feed-at-issue | "A result the history does not carry, then or earlier, comes off the `r` lines in the order the branches take them, and is zero once those run out" | edge-no-wait |
| tab-flat-count | "Commands are counted by kind, and the count of one kind is not moved by commands of any other" | count-kind |
| edge-match-after-live | "Every waiting branch can run again from that point, nothing waits again, and no command is matched against the history again however much of it is left" | edge-after-live-go |
| left-latest | "then it prints `drift left <kind> <i>` for the earliest such `go` in the history" | left-earliest |
| left-counts-all | "Only `go` lines count for that. An `ok`, a `sig` or a `ch` that nobody took is not a failure" | left-not-ok |
| left-none | "then it prints `drift left <kind> <i>` for the earliest such `go` in the history" | left-after-live |
| hold-last | "a later `take` waits for the earliest command the branch has issued and not yet taken the result of" | pair-dup |
| ver-cur-replay | "the value is zero while the run still has something to replay, and the marker's own second word once `live` has been printed" | ver-branch |
| ver-zero-live | "the value is zero while the run still has something to replay, and the marker's own second word once `live` has been printed" | ver-live-cur |
| ver-key-blind | "`mark` takes the earliest `ch` of its own key that has not been taken" | ver-per-key |
| ver-stuck | "`mark` takes the earliest `ch` of its own key that has not been taken" | ver-per-key |
| const-zero | "a command issued prints `<b> go <kind> <i> <name>`, a result taken prints `<b> ok <kind> <i> <value>`" | count-kind |
| pos-first | "the command at count `j` among the commands of that kind and name takes the `ok` at position `j` among the `ok` lines carrying that same kind and name" | pair-dup |

## Shortcuts

| Strategy | Result |
|---|---|
| the shipped tree unchanged (the nop) | 0; the enumerated programs and the generated population both fail |
| `cheat-const-zero`, one fixed shape for every run file | 0; caught by `count-kind` |
| `cheat-pos-first`, always the first recorded answer of the pair | 0; caught by `pair-dup` |
| `cheat-forge-hand`, the enumerated histories recognised by fingerprint and settled correctly, the rest as shipped | 0; passes every enumerated program and fails the generated population |
| `cheat-forge-truth`, the frozen answers carried and handed back through a replaced trace writer | 0; the same, and `tools/forgecheck.py` names it as a carrier of ground truth |
| `cheat-slow-sched`, exactly correct and walks the branches for the one whose turn is next | 0; killed by the clock, not by an assertion |
| `cheat-slow-history`, exactly correct and walks the history for every lookup | 0; killed by the clock |

## Tolerances

There is no numeric tolerance: printouts are compared string for string. The only limit is the
wall clock, and it is validated against two implementations written apart from the reference.

| Tolerance or limit | Independent implementation | Measured |
|---|---|---|
| the 200000 op ceiling on the body (`tests/seal/model.py:39`) | `tests/seal/model.py`, written apart from `environment/app_src/dur/mach.py`, which is where the ceiling is enforced for the agent run | `over-steps` reaches it; no graded run file comes near, the longest body being 88000 ops |
| the 60 second wall clock on the stage that runs the submitted engine (`tests/test.sh:34`) | `authoring/replay-match-drift/variants/ok-sorted` and `authoring/replay-match-drift/variants/ok-array`, both written apart from the reference | the six scale run files take 2.6 s under the reference and 3.3 s and 2.5 s under the two variants, against the 60 s limit; the two readings that settle every rule the same way and walk instead of indexing take 137.8 s for the branch walk, while the history walk does not finish them at all, measured by `authoring/replay-match-drift/timing.py` |
