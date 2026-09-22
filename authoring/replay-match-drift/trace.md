# Instruction trace: replay-match-drift

Walked from the verifier toward the instruction (docs/INSTRUCTION-CONTRACT.md). Every graded
assertion, every enumerated run file, every collected artifact, the clock and every rule the
sealed model applies has a row here with the sentence of `instruction.md` that tells the agent
about it. Re-run `python tools/tracecheck.py replay-match-drift` after any change to the brief,
to tests/, to the model, to the generator or to the environment.

## Graded assertions

| Verifier site | What it grades | Instruction sentence |
|---|---|---|
| `tests/test_outputs.py:117` test_the_model_still_reproduces_the_frozen_answers | the sealed model still reproduces every frozen answer, so a drifted model cannot redefine correct | "Commands are counted by kind, from zero, and the count of one kind is not moved by commands of any other" "Every command issued prints `go <kind> <i> <name>` and every result taken prints `ok <kind> <i> <value>`, with `i` the command's own count within its kind" |
| `tests/test_outputs.py:127` test_hand_program | each enumerated run file's whole trace, line for line, against the frozen answers | "Every command issued prints `go <kind> <i> <name>` and every result taken prints `ok <kind> <i> <value>`, with `i` the command's own count within its kind" "Your engine is graded on run files you have not seen" |
| `tests/test_outputs.py:136` test_every_generated_program_matches | every generated run file's whole trace against the sealed model | "Your engine is graded on run files you have not seen" |
| `tests/test_outputs.py:155` test_every_family_is_represented | that the generated population still covers every family, so the exam cannot be shrunk | "Your engine is graded on run files you have not seen" |
| `tests/cases.py:10` case kind-count | a timer between two calls does not move the second call's count | "Commands are counted by kind, from zero, and the count of one kind is not moved by commands of any other" "The command at count `i` of its kind matches the `go` at position `i` among the `go` lines of that kind" "Every count and every position here starts at zero" |
| `tests/cases.py:16` case kind-count-same | one kind throughout, the ordinary side of the counting rule | "Commands are counted by kind, from zero, and the count of one kind is not moved by commands of any other" "The command at count `i` of its kind matches the `go` at position `i` among the `go` lines of that kind" |
| `tests/cases.py:22` case kind-count-three | three kinds recorded in another order than the body issues them | "Commands are counted by kind, from zero, and the count of one kind is not moved by commands of any other" "`call` and `fire` issue a command of kind `call`, `spawn` and `open` of kind `child`, `nap` of kind `timer`" |
| `tests/cases.py:31` case name-check | a recorded command under another name stops the run where it happens | "If that `go` carries another name the run stops there and prints `drift <kind> <i> <recorded name> <name asked for>`" |
| `tests/cases.py:37` case name-check-kind | the same, on a kind whose own count is zero | "If that `go` carries another name the run stops there and prints `drift <kind> <i> <recorded name> <name asked for>`" "Commands are counted by kind, from zero, and the count of one kind is not moved by commands of any other" |
| `tests/cases.py:44` case pair-name | two names of one kind answered in the opposite order | "the command at count `j` among the commands of that kind and name takes the `ok` at position `j` among the `ok` lines carrying that same kind and name" |
| `tests/cases.py:49` case pair-dup | one kind and name issued twice beside a third command | "the command at count `j` among the commands of that kind and name takes the `ok` at position `j` among the `ok` lines carrying that same kind and name" |
| `tests/cases.py:54` case pair-kind-name | one name used under two kinds, answered in the other order | "the command at count `j` among the commands of that kind and name takes the `ok` at position `j` among the `ok` lines carrying that same kind and name" |
| `tests/cases.py:59` case pair-order | answers in issue order, the ordinary side of the pairing rule | "the command at count `j` among the commands of that kind and name takes the `ok` at position `j` among the `ok` lines carrying that same kind and name" |
| `tests/cases.py:66` case edge-once | the boundary line printed once with three live commands after it | "A command whose kind has no `go` left at its count opens the live side" "`live` is printed once for the whole run, before that command's own line" "A command on the live side takes the next `r` value instead, in the order the live commands were issued, and zero once the `r` lines run out" |
| `tests/cases.py:71` case edge-global | the boundary opened on one kind leaves another kind's record unmatched | "no command issued after it looks at the history for a `go`, whatever its kind" "A body that reaches `fin` while the history still holds a `go` that no command matched prints `drift left <kind> <i>` for the earliest such `go` in the history" |
| `tests/cases.py:76` case edge-none | a body that matches its history never prints the boundary line | "A command whose kind has no `go` left at its count opens the live side" "`live` is printed once for the whole run, before that command's own line" |
| `tests/cases.py:81` case edge-empty | an empty history: the first command opens the boundary | "A command whose kind has no `go` left at its count opens the live side" "A command on the live side takes the next `r` value instead, in the order the live commands were issued, and zero once the `r` lines run out" |
| `tests/cases.py:85` case edge-feed-out | live commands past the end of the value list take zero | "A command on the live side takes the next `r` value instead, in the order the live commands were issued, and zero once the `r` lines run out" |
| `tests/cases.py:91` case left-earliest | two recorded commands left over, the earliest named | "A body that reaches `fin` while the history still holds a `go` that no command matched prints `drift left <kind> <i>` for the earliest such `go` in the history" |
| `tests/cases.py:96` case left-not-sig | a recorded signal nobody waited for is not a failure | "an `ok`, a `sig` or a `ch` that nobody took is not a failure" |
| `tests/cases.py:100` case left-not-ok | a spare answer and a spare choice are not failures either | "an `ok`, a `sig` or a `ch` that nobody took is not a failure" |
| `tests/cases.py:104` case left-skip-hold | a run that stopped short makes no leftover check | "A run that stopped short never makes the check" "A result that is needed and has no answer stops the run: it prints `hold <kind> <i>` naming that command" |
| `tests/cases.py:110` case left-after-live | leftovers are still owed after the boundary was opened | "no command issued after it looks at the history for a `go`, whatever its kind" "A body that reaches `fin` while the history still holds a `go` that no command matched prints `drift left <kind> <i>` for the earliest such `go` in the history" |
| `tests/cases.py:118` case join-first | join takes the command issued earliest, not the one answered earliest | "`join` takes the result of the outstanding command that was issued earliest" |
| `tests/cases.py:123` case race-answered | race takes the command answered earliest on the same history | "`race` takes the result of the outstanding command whose answer arrives earliest" |
| `tests/cases.py:128` case race-live-after | a live command loses a race to a recorded answer | "answer counts as having arrived after every recorded answer" "`race` takes the result of the outstanding command whose answer arrives earliest" |
| `tests/cases.py:133` case feed-order | two live commands take the values in the order they were issued | "A command on the live side takes the next `r` value instead, in the order the live commands were issued, and zero once the `r` lines run out" |
| `tests/cases.py:137` case race-none | a race where nothing outstanding has an answer names the earliest issued | "an outstanding command with no answer at all is never taken by a race" "A `join`, or a `race` where no outstanding command has an answer, names the outstanding command issued earliest" |
| `tests/cases.py:141` case hold-cmd | a recorded command with no recorded answer stops the run | "A result that is needed and has no answer stops the run: it prints `hold <kind> <i>` naming that command" |
| `tests/cases.py:146` case hold-none | a join with nothing outstanding | "nothing outstanding at all it prints `hold none` instead" |
| `tests/cases.py:152` case sig-tag | two tags recorded in one order and waited for in the other | "`wait` takes the earliest `sig` of its own tag that has not been taken, wherever that line sits in the history and whichever side of the boundary the run is on" |
| `tests/cases.py:156` case sig-hold | a wait with no recorded signal of its tag | "With none of that tag left it stops the run and prints `hold sig <tag>`" |
| `tests/cases.py:160` case sig-after-live | a signal taken after the boundary was opened | "`wait` takes the earliest `sig` of its own tag that has not been taken, wherever that line sits in the history and whichever side of the boundary the run is on" |
| `tests/cases.py:167` case ver-recorded | a recorded choice wins over the value the marker asks for | "`mark` takes the earliest `ch` of its own key that has not been taken" |
| `tests/cases.py:171` case ver-replay-zero | an unrecorded marker is zero while the run is still replaying | "the value is zero while the run is still replaying, and the marker's own second word once the run has gone live" |
| `tests/cases.py:175` case ver-live-cur | an unrecorded marker takes the body's own value once live | "the value is zero while the run is still replaying, and the marker's own second word once the run has gone live" |
| `tests/cases.py:179` case ver-empty-zero | an empty history is still replaying until a command opens the boundary | "the value is zero while the run is still replaying, and the marker's own second word once the run has gone live" "A command whose kind has no `go` left at its count opens the live side" |
| `tests/cases.py:182` case ver-per-key | choices taken per key, in recorded order | "`mark` takes the earliest `ch` of its own key that has not been taken" |
| `tests/cases.py:186` case ver-branch | the marker's value decides which arm runs and therefore which command is issued | "the value is zero while the run is still replaying, and the marker's own second word once the run has gone live" "The accumulator starts at zero, every result taken and every marker and signal goes into it, `jz` jumps when it is zero and `jnz` when it is not" "`lab` marks a place and does nothing else" |
| `tests/cases.py:193` case over-steps | a body that runs past the step ceiling | "A body that executes more than 200000 ops prints `over` and nothing else" |
| `tests/cases.py:198` case parse-blank | blank lines in a run file are skipped by the grammar | "Blank lines are ignored" "Values are integers. Names, tags and keys are single words" |
| `tests/cases.py:203` case plain-ordinary | an everyday run file that an overconservative engine breaks | "A `b` line is one op of the workflow body, in the order the body runs them" "`call`, `spawn` and `nap` take the answer of the command they issue" |
| artifact `/app/dur/tab.py` | collected for grading; nothing else is | "The files you may change are `/app/dur/tab.py`, `/app/dur/edge.py`, `/app/dur/pair.py`, `/app/dur/pend.py`, `/app/dur/sigq.py` and `/app/dur/ver.py`" "a new file put beside those six is never read" |
| artifact `/app/dur/edge.py` | collected for grading; nothing else is | "The files you may change are `/app/dur/tab.py`, `/app/dur/edge.py`, `/app/dur/pair.py`, `/app/dur/pend.py`, `/app/dur/sigq.py` and `/app/dur/ver.py`" "a new file put beside those six is never read" |
| artifact `/app/dur/pair.py` | collected for grading; nothing else is | "The files you may change are `/app/dur/tab.py`, `/app/dur/edge.py`, `/app/dur/pair.py`, `/app/dur/pend.py`, `/app/dur/sigq.py` and `/app/dur/ver.py`" "a new file put beside those six is never read" |
| artifact `/app/dur/pend.py` | collected for grading; nothing else is | "The files you may change are `/app/dur/tab.py`, `/app/dur/edge.py`, `/app/dur/pair.py`, `/app/dur/pend.py`, `/app/dur/sigq.py` and `/app/dur/ver.py`" "a new file put beside those six is never read" |
| artifact `/app/dur/sigq.py` | collected for grading; nothing else is | "The files you may change are `/app/dur/tab.py`, `/app/dur/edge.py`, `/app/dur/pair.py`, `/app/dur/pend.py`, `/app/dur/sigq.py` and `/app/dur/ver.py`" "a new file put beside those six is never read" |
| artifact `/app/dur/ver.py` | collected for grading; nothing else is | "The files you may change are `/app/dur/tab.py`, `/app/dur/edge.py`, `/app/dur/pair.py`, `/app/dur/pend.py`, `/app/dur/sigq.py` and `/app/dur/ver.py`" "a new file put beside those six is never read" |
| `tests/test.sh:34` a 60 s clock | the wall clock on the stage that runs the submitted engine | "All of the graded run files together have to finish inside 60 seconds of wall clock" "three carry thirty thousand commands against a history of sixty thousand lines" |
| `tests/seal/model.py:60-79` the log indexed | the two axes the rules count on: `go` per kind, `ok` per kind and name | "Commands are counted by kind, from zero, and the count of one kind is not moved by commands of any other" "the command at count `j` among the commands of that kind and name takes the `ok` at position `j` among the `ok` lines carrying that same kind and name" |
| `tests/seal/model.py:100-104` leftover | the earliest recorded command no command matched | "A body that reaches `fin` while the history still holds a `go` that no command matched prints `drift left <kind> <i>` for the earliest such `go` in the history" |
| `tests/seal/model.py:106-110` the step ceiling | a body past the ceiling ends over | "A body that executes more than 200000 ops prints `over` and nothing else" |
| `tests/seal/model.py:115-119` the per-kind count | the count a command is matched on | "Commands are counted by kind, from zero, and the count of one kind is not moved by commands of any other" |
| `tests/seal/model.py:120-127` the boundary | one crossing for the run, printed once | "A command whose kind has no `go` left at its count opens the live side" "`live` is printed once for the whole run, before that command's own line" "no command issued after it looks at the history for a `go`, whatever its kind" |
| `tests/seal/model.py:128-131` the name check | a recorded command under another name | "If that `go` carries another name the run stops there and prints `drift <kind> <i> <recorded name> <name asked for>`" |
| `tests/seal/model.py:132-140` the answer pairing | the counter on kind and name together | "the command at count `j` among the commands of that kind and name takes the `ok` at position `j` among the `ok` lines carrying that same kind and name" |
| `tests/seal/model.py:141-145` the live answer | the value list, and where a live answer ranks | "A command on the live side takes the next `r` value instead, in the order the live commands were issued, and zero once the `r` lines run out" "answer counts as having arrived after every recorded answer" |
| `tests/seal/model.py:146-154` printing and outstanding | the go and ok lines, and what is left outstanding | "Every command issued prints `go <kind> <i> <name>` and every result taken prints `ok <kind> <i> <value>`, with `i` the command's own count within its kind" "`call`, `spawn` and `nap` take the answer of the command they issue" |
| `tests/seal/model.py:156-177` join and race | the two orders over the outstanding set, and what stops the run | "`join` takes the result of the outstanding command that was issued earliest" "`race` takes the result of the outstanding command whose answer arrives earliest" "an outstanding command with no answer at all is never taken by a race" "nothing outstanding at all it prints `hold none` instead" "A result that is needed and has no answer stops the run: it prints `hold <kind> <i>` naming that command" |
| `tests/seal/model.py:179-188` signals | the per-tag queue and the stop | "`wait` takes the earliest `sig` of its own tag that has not been taken, wherever that line sits in the history and whichever side of the boundary the run is on" "With none of that tag left it stops the run and prints `hold sig <tag>`" |
| `tests/seal/model.py:190-200` markers | the recorded choice and the default on each side of the boundary | "`mark` takes the earliest `ch` of its own key that has not been taken" "the value is zero while the run is still replaying, and the marker's own second word once the run has gone live" |
| `tests/seal/model.py:202-213` the accumulator and the jumps | what the accumulator holds and what the jumps test | "The accumulator starts at zero, every result taken and every marker and signal goes into it, `jz` jumps when it is zero and `jnz` when it is not" |
| `tests/seal/model.py:215-220` the end of the body | the leftover check, then the result | "A body that reaches `fin` while the history still holds a `go` that no command matched prints `drift left <kind> <i>` for the earliest such `go` in the history" "A run that stopped short never makes the check" "with nothing left over prints `fin <accumulator>`" |

## Readings

Each wrong reading is a whole engine under `authoring/replay-match-drift/emit.py`, measured by
`python tools/readingcheck.py replay-match-drift`; all 23 are separated by the enumerated set.

| Reading | Sentence that rules it out | Case that separates it |
|---|---|---|
| flat-count | "Commands are counted by kind, from zero, and the count of one kind is not moved by commands of any other" | kind-count |
| slot-by-name | "The command at count `i` of its kind matches the `go` at position `i` among the `go` lines of that kind" | pair-dup |
| kind-answer | "the command at count `j` among the commands of that kind and name takes the `ok` at position `j` among the `ok` lines carrying that same kind and name" | join-first |
| name-answer | "the command at count `j` among the commands of that kind and name takes the `ok` at position `j` among the `ok` lines carrying that same kind and name" | pair-kind-name |
| pair-kind-counter | "the command at count `j` among the commands of that kind and name takes the `ok` at position `j` among the `ok` lines carrying that same kind and name" | edge-none |
| edge-per-kind | "no command issued after it looks at the history for a `go`, whatever its kind" | edge-empty |
| edge-each-time | "`live` is printed once for the whole run, before that command's own line" | edge-empty |
| edge-log-empty | "A command whose kind has no `go` left at its count opens the live side" | edge-global |
| left-latest | "A body that reaches `fin` while the history still holds a `go` that no command matched prints `drift left <kind> <i>` for the earliest such `go` in the history" | left-earliest |
| left-counts-all | "an `ok`, a `sig` or a `ch` that nobody took is not a failure" | left-not-sig |
| race-issued | "`race` takes the result of the outstanding command whose answer arrives earliest" | race-answered |
| race-latest | "`race` takes the result of the outstanding command whose answer arrives earliest" | race-answered |
| join-answered | "`join` takes the result of the outstanding command that was issued earliest" | join-first |
| race-live-first | "answer counts as having arrived after every recorded answer" | race-live-after |
| hold-as-live | "A result that is needed and has no answer stops the run: it prints `hold <kind> <i>` naming that command" | hold-cmd |
| sig-one-queue | "`wait` takes the earliest `sig` of its own tag that has not been taken, wherever that line sits in the history and whichever side of the boundary the run is on" | sig-tag |
| sig-stuck | "`wait` takes the earliest `sig` of its own tag that has not been taken, wherever that line sits in the history and whichever side of the boundary the run is on" | sig-tag |
| ver-cur-replay | "the value is zero while the run is still replaying, and the marker's own second word once the run has gone live" | ver-branch |
| ver-zero-live | "the value is zero while the run is still replaying, and the marker's own second word once the run has gone live" | ver-live-cur |
| ver-key-blind | "`mark` takes the earliest `ch` of its own key that has not been taken" | ver-per-key |
| ver-stuck | "`mark` takes the earliest `ch` of its own key that has not been taken" | ver-per-key |
| const-zero | "Every command issued prints `go <kind> <i> <name>` and every result taken prints `ok <kind> <i> <value>`, with `i` the command's own count within its kind" | edge-feed-out |
| pos-first | "the command at count `j` among the commands of that kind and name takes the `ok` at position `j` among the `ok` lines carrying that same kind and name" | pair-dup |

## Shortcuts

| Strategy | Result |
|---|---|
| the shipped tree unchanged (the nop) | 0; 15 of the 37 enumerated programs fail, and the generated population |
| `cheat-const-zero`, one fixed shape for every run file | 0; moves 100 per cent of the generated set, caught by `edge-feed-out` |
| `cheat-pos-first`, always the first recorded answer of the pair | 0; moves 34 per cent, caught by `pair-dup` |
| `cheat-forge-hand`, the 37 enumerated histories recognised by fingerprint and settled correctly, the rest as shipped | 0; passes all 37 enumerated programs and fails the generated population |
| `cheat-slow-scan`, exactly correct and walks the history for every lookup | 0; killed by the clock, not by an assertion |
| `cheat-slow-answers`, exactly correct with the commands indexed and the answers walked for | 0; killed by the clock |

## Tolerances

There is no numeric tolerance: traces are compared string for string. The only limit is the
wall clock, and it is validated against two implementations written apart from the reference.

| Tolerance or limit | Independent implementation | Measured |
|---|---|---|
| the 200000 op ceiling on the body (`tests/seal/model.py:31`) | `tests/seal/model.py`, written apart from `environment/app_src/dur/mach.py`, which is where the ceiling is enforced for the agent run | `over-steps` reaches it; no graded run file comes near it, the longest body being 44000 ops |
| the 60 second wall clock on the stage that runs the submitted engine (`tests/test.sh:34`) | `authoring/replay-match-drift/variants/ok-deque` and `authoring/replay-match-drift/variants/ok-flat`, both written apart from the reference | the six scale run files take 1.0 s under each variant and 0.9 s under the reference, against the 60 s limit; the two readings that settle every rule the same way and walk the history take 306.4 s with every lookup walked and 153.2 s with only the answers walked, measured by `authoring/replay-match-drift/timing.py` |
