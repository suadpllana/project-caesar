# Instruction trace: pull-check-stale

Walked from the verifier toward the instruction (docs/INSTRUCTION-CONTRACT.md). Every graded
assertion, every enumerated case, every rule the sealed model applies and every condition in
`tests/test.sh` that can turn a run into a 0 has a row, with the sentence in `instruction.md`
that tells the agent about it. Checked with `python tools/tracecheck.py pull-check-stale`.

## Graded assertions

| Verifier site | What it grades | Instruction sentence |
|---|---|---|
| `tests/test_outputs.py:121` test_frozen_truth_matches_the_model | the sealed model still reproduces the frozen answers; grades nothing the agent wrote, and guards the rest of the file | "The graded set is thirty-three programs written by hand" |
| `tests/test_outputs.py:131` test_hand_case | every hand program's trace, line for line, and that the program text was not altered | "prints one line for each thing that happens" |
| `tests/test_outputs.py:140` test_every_nonce_program_matches | every generated program's trace, line for line | "three hundred and eight generated ones" |
| `tests/test_outputs.py:159` test_every_family_is_represented | that the generated population the submission was marked against is the whole one | "and the whole of it has to get through inside 60 seconds" |
| `tests/cases.py:17` case ord-stop-short | the walk stops at the first failed observation, so the pull after it never runs that step | "the first observation that no longer holds ends the taking; observations after that one are not taken at all" |
| `tests/cases.py:37` case ord-pull-first | a failing pull observation is reached first and runs its step, and the re-run reaches the read after it | "A pull observation is taken by bringing the step it names up to date and then comparing" |
| `tests/cases.py:57` case ord-flat-after-pull | the record is walked in the order the run made it, not cheap observations first | "the record is taken in the order it was made" |
| `tests/cases.py:75` case ord-nothing-moves | a record that still holds leaves its step alone and prints no run line | "A record whose observations all still hold leaves the step alone." |
| `tests/cases.py:96` case stuck-second-pull | a step that ran and was undone by another step's output is stuck, not run again | "unless that step has already run in this round, and then the request ends there and the step is reported stuck instead" |
| `tests/cases.py:119` case stuck-edit-midround | an edit between two requests of one round can leave a step that has already run stale | "are edits made from outside the service and `want <step>` is a request, all taken in the order they are written" |
| `tests/cases.py:132` case stuck-only-checked | the other side of the fence: a step only taken in this round runs rather than reporting stuck | "A step that has only been taken this round has not run." |
| `tests/cases.py:147` case stuck-checked-then-undone | a step found sound earlier in the round and undone afterwards runs, because it had not run | "A step that has only been taken this round has not run." |
| `tests/cases.py:171` case stuck-inside-run | a stuck under a running step cuts that run short and leaves it as if it had never run, and the line names the stale step rather than the one the request asked for | "A run cut short by a loop or by a stuck under it leaves its step as though it had never run" and "naming the step that had already run, which need not be the one the request asked for" |
| `tests/cases.py:190` case cut-value-holds | a step that re-runs and emits what it emitted before leaves what pulled it alone | "so a step that runs again and emits what it emitted before leaves the observation standing" |
| `tests/cases.py:206` case cut-value-moves | the other side: a value that does move breaks the pull observation | "A pull of a step observes the value that step emitted" |
| `tests/cases.py:224` case look-content-quiet | a look is undisturbed by a rewrite of the path it looked at | "A look at a path observes whether the path is there, and nothing about what is in it." |
| `tests/cases.py:239` case look-appear | a look that found nothing stops holding when the path appears | "A look at a path observes whether the path is there" |
| `tests/cases.py:253` case look-vanish | a look that found the path stops holding when the path is removed | "`put <path> <word>` and `cut <path>` are edits made from outside the service" |
| `tests/cases.py:269` case miss-dies | a read of an absent path ends the run with that reason | "the step is dead with the reason `missing <path>`" |
| `tests/cases.py:280` case miss-cached-in-round | a dead step pulled twice in one round runs once | "A step that is dead stays dead until one of the observations in the record it kept stops holding." |
| `tests/cases.py:296` case miss-revives | the recorded absence is what brings the dead step back when the path appears | "the observation of that absence is the last thing the record keeps" |
| `tests/cases.py:311` case dead-via-name | the reason names the step that was pulled, not the failure underneath it | "naming the step it pulled and not whatever lies under that" |
| `tests/cases.py:327` case dead-reason-changes | a dead pull observation holds whatever the step died of | "or that it was dead - never why it was dead" |
| `tests/cases.py:347` case bare-stale | reading a path a step writes sees the bytes standing there and does not run that step | "it observes the bytes standing at that path, and never brings that step up to date" |
| `tests/cases.py:367` case bare-fresh | the other side: a pull before the read makes the read see this round's bytes | "A pull brings the step it names up to date and yields that step's value" |
| `tests/cases.py:385` case out-clobber | an outside write over a step's output path breaks the observation of what it wrote | "it observes what that run wrote to its own output path, after the writing" |
| `tests/cases.py:398` case out-same-quiet | the other side: putting back the bytes already there disturbs nothing | "A run that ends with a value writes it to the step's own path" |
| `tests/cases.py:414` case loop-inner | the chain runs from where the repeated step first stands on the live chain | "the steps from where that step first stands on the chain through to the one doing the pulling, in order, and then that step again" |
| `tests/cases.py:433` case loop-self | a step that pulls itself is a chain of that step twice | "A step already on the live chain of pulls is a loop." |
| `tests/cases.py:444` case loop-leaves-nothing | a run cut short leaves nothing, the printed run line stays, and the next request in the round is unaffected | "while a run line already printed stays printed and everything that finished before the cut stands" |
| `tests/cases.py:467` case rec-replaced | a re-run's record replaces the old one rather than merging with it | "the observations its last run made, in the order it made them" |
| `tests/cases.py:520` case emit-mix-pulls | the emitted value takes what the pulls returned as well as what the reads found | "the digest `/app/eng/dig.py` makes of the words the reads yielded and the values the pulls yielded, in the order the run took them" |
| `tests/cases.py:535` case twin-a | one program's answer does not lean on the program run before it | "A program file describes one workspace and everything that happens to it." |
| `tests/cases.py:544` case twin-b | the twin of the above, differing only in a seeded word | "`seed <path> <word>` puts a word at a path before the first round." |
| `tests/cases.py:486` case dead-writes-nothing | a run that died left nothing at the path it would have written, so a step reading that path dies too | "a run that dies writes nothing" |
| `tests/cases.py:500` case loop-keeps-finished | a step that finished before the cut stands, and asking for it again in the same round runs nothing | "everything that finished before the cut stands" |
| `tests/cases.py:555` case diamond-small | the walk over a graph whose every level is reachable two ways, at a size the clock does not decide | "Two of the generated ones are pull graphs twenty-four and twenty-one levels deep in which every level is reachable two ways" |
| artifact `/app/eng/keep.py` | collected from the agent; nothing else is | "The files you may change are `/app/eng/keep.py`" |
| artifact `/app/eng/mark.py` | collected from the agent; nothing else is | "The files you may change are `/app/eng/keep.py`, `/app/eng/mark.py`" |
| artifact `/app/eng/hold.py` | collected from the agent; nothing else is | "`/app/eng/mark.py`, `/app/eng/hold.py`, `/app/eng/step.py` and `/app/eng/wake.py`" |
| artifact `/app/eng/step.py` | collected from the agent; nothing else is | "`/app/eng/hold.py`, `/app/eng/step.py` and `/app/eng/wake.py`. Nothing else." |
| artifact `/app/eng/wake.py` | collected from the agent; nothing else is | "and `/app/eng/wake.py`. Nothing else." |
| `tests/test.sh:36` a 60 s clock on the worker | the whole graded set must finish inside it; a timeout loses the record and scores 0 | "the whole of it has to get through inside 60 seconds" |
| `tests/worker.py:47` the overlay | only the five files are laid over the verifier's own copy, so a sixth file is never read | "The rest of the tree is replaced by our own copy before a program is run, a new file put beside those five included" |
| `tests/seal/model.py:69-126` parse | the program grammar: which directives exist, that every step ends with exactly one emit, that a pull and a want must name a declared step | "are that step's script in the order they are written, and `emit` is the last op of every step and the only one" |
| `tests/seal/model.py:149-155` write | a write only counts as a change to the workspace when the bytes move, which is what leaves earlier verdicts standing | "so a step that runs again and emits what it emitted before leaves the observation standing" |
| `tests/seal/model.py:156-161` erase | removing a path that is there is a change to the workspace | "`cut <path>` are edits made from outside the service" |
| `tests/seal/model.py:170-174` flat | a read or an output observation holds while the digest matches, a look while presence matches | "A look at a path observes whether the path is there, and nothing about what is in it." |
| `tests/seal/model.py:182-190` serve, the walk | the record is taken in order and the first failure ends it | "the first observation that no longer holds ends the taking" |
| `tests/seal/model.py:187-192` serve, the pull observation | a pull observation is taken by bringing that step up to date and comparing its value, or its deadness | "A pull observation is taken by bringing the step it names up to date and then comparing" |
| `tests/seal/model.py:198-200` serve, the verdict | a record that holds marks the step up to date at the version the workspace now carries | "A step whose record was last found to hold while the workspace was exactly as it is now needs nothing further." |
| `tests/seal/model.py:201-202` serve, stuck | a stale record on a step that has already run this round ends the request | "unless that step has already run in this round, and then the request ends there and the step is reported stuck instead" |
| `tests/seal/model.py:203-211` serve, the run | the run line is printed as the run begins, and a run cut short leaves nothing behind | "`run <name>` as a run begins." |
| `tests/seal/model.py:218-223` work, read | a read yields the word at the path, or ends the run with the absence recorded | "A read of a path that is not there ends the run: the step is dead with the reason `missing <path>`" |
| `tests/seal/model.py:224-225` work, look | a look records presence only and yields nothing | "A look yields nothing." |
| `tests/seal/model.py:226-233` work, pull | a pull yields the pulled step's value, or ends the run naming that step | "the step is dead with the reason `via <step>`" |
| `tests/seal/model.py:234-236` work, emit | the value is the word named, or the digest of the words read and the values pulled in order | "the word it names, or, when it names `*`, the digest" |
| `tests/seal/model.py:237-243` work, the output | a run that ends with a value writes it and observes what it wrote; a run that dies writes nothing | "A run that ends with a value writes it to the step's own path; a run that dies writes nothing." |
| `tests/seal/model.py:246-278` bring, the loop | a pull that reaches a step on the live chain ends the request with that chain | "A pull that reaches a step already on the live chain ends the request with that chain" |
| `tests/seal/model.py:280-284` settled | a step whose verdict was taken at the version the workspace still carries needs no walk | "A step whose record was last found to hold while the workspace was exactly as it is now needs nothing further." |
| `tests/seal/model.py:286-299` play | round numbering from one, the edits and the requests taken in the order written, and no step counted as run at the start of a round | "`round <n>` as each round opens, counting from one." |
| `tests/seal/model.py:291` play, the round reset | every round begins with no step having run in it | "Every round begins with no step having run in it." |
| `tests/seal/model.py:301-314` ask | the outcome line for a request: ok, err with either reason, stuck, or loop, and nothing else | "Then one line for each request: `ok <name> <value>`; or `err <name> missing <path>` or `err <name> via <step>` when the step is dead" |
| `tests/seal/model.py:55-57` of, `tests/seal/model.py:59-65` mix | the digest function the emitted value comes from, which the tree already carries and is used unchanged | "the digest `/app/eng/dig.py` makes of the words the reads yielded" |
| `tests/seal/model.py:316-327` trace, trace_file, expect | the trace is the printed lines and nothing else | "Nothing else is printed." |
| `tests/seal/model.py:128-131` tok, `tests/seal/model.py:39-52` Bad, Ring, Halt | program text that is not in the grammar is rejected before any grading; graded programs are all well formed | "A program file describes one workspace and everything that happens to it." |
| `tests/seal/model.py:136-147` Mdl, `tests/seal/model.py:163-168` hash_of, `tests/seal/model.py:176-179` wipe | internal state and its reset; no rule of its own beyond the ones above | "What the service keeps about a step is a record: the observations its last run made, in the order it made them." |

## Readings

| Reading | Sentence or published example that rules it out | Case that separates it |
|---|---|---|
| chk-all | "observations after that one are not taken at all" | diamond-small |
| chk-flat-first | "the record is taken in the order it was made" | ord-flat-after-pull |
| memo-round | "A step whose record was last found to hold while the workspace was exactly as it is now needs nothing further." | stuck-checked-then-undone |
| no-stuck | "the request ends there and the step is reported stuck instead" | stuck-edit-midround |
| stuck-on-check | "A step that has only been taken this round has not run." | stuck-checked-then-undone |
| look-as-read | "and nothing about what is in it" | look-content-quiet |
| look-blind | "A look at a path observes whether the path is there" | look-appear |
| fail-forget | "the observation of that absence is the last thing the record keeps" | miss-revives |
| fail-sticky | "A step that is dead stays dead until one of the observations in the record it kept stops holding." | dead-reason-changes |
| rec-merge | "the observations its last run made, in the order it made them" | rec-replaced |
| no-cutoff | "never that it ran, so a step that runs again and emits what it emitted before leaves the observation standing" | cut-value-holds |
| read-pulls | "it observes the bytes standing at that path, and never brings that step up to date" | bare-stale |
| no-out-mark | "it observes what that run wrote to its own output path, after the writing" | out-clobber |
| loop-from-root | "the steps from where that step first stands on the chain through to the one doing the pulling" | loop-inner |
| loop-no-close | "in order, and then that step again" | loop-inner |
| via-inner | "naming the step it pulled and not whatever lies under that" | dead-via-name |
| dead-reason-match | "never why it was dead" | dead-reason-changes |
| run-line-after | "`run <name>` as a run begins." and the worked example of `/app/progs/one.txt` | ord-nothing-moves |
| cut-tombstone | "`cut <path>` are edits made from outside the service" | look-vanish |
| emit-reads-only | "the words the reads yielded and the values the pulls yielded, in the order the run took them" | emit-mix-pulls |
| miss-no-mark | "the observation of that absence is the last thing the record keeps" | miss-revives |

Readings enumerated and then dropped because the published evidence does not separate them, so
they are correct variants rather than wrong readings: advancing the change count on every write
including one that moves no bytes (`authoring/pull-check-stale/variants/ok-loose`, scores 1);
recomputing a digest at every comparison instead of caching it (same variant); checking the live
chain after the verdict instead of before it (unreachable - a step on the chain never carries a
verdict taken at the current version). All twenty-one readings above were run as whole engines
over 112 generated programs before anything shipped: each moves between 1 and 77 of them, and
each is separated by the enumerated case named above (`tools/readingcheck.py`, clean).

## Shortcuts

| Strategy | Result |
|---|---|
| the shipped tree unchanged (nop) | 0. 15 of 33 hand programs wrong and 192 of 308 generated |
| constant: one fixed outcome for every request (`cheat-flat-one-answer.sh`) | 0. all 33 hand programs and all 308 generated wrong |
| constant: the first seeded word for every request (`cheat-flat-first-seed.sh`) | 0. all 33 hand programs and all 308 generated wrong |
| positional: every step run on every request (`cheat-flat-run-everything.sh`) | 0. all 33 hand programs and all 308 generated wrong |
| the worked example's trace replayed (`cheat-flat-replay-example.sh`) | 0. all 33 hand programs and all 308 generated wrong |
| the frozen answers carried and replayed (`cheat-forge-answer-key.sh`) | 0. reproduces 25 of the 33 hand programs and fails all 308 it could not have seen |

## Tolerances

| Tolerance or limit | Independent implementation | Measured |
|---|---|---|
| `tests/test.sh:36` a 60 s clock on the whole graded set | `authoring/pull-check-stale/variants/ok-flat`, written apart from the reference as an explicit-stack scheduler, and `authoring/pull-check-stale/variants/ok-loose`, which caches no digest at all | both get through all 341 programs in 0.1 s against the 60 s clock. The naive family it exists to stop, `authoring/pull-check-stale/variants/slow-nomemo` - identical traces, verdict not remembered - takes 217 s and 88 s on the two deep programs alone, so it loses the record. Reference: 0.07 s over the 308 generated programs, 0.003 s on each deep one |
| exact comparison, no numeric tolerance anywhere | `authoring/pull-check-stale/variants/ok-flat` and the sealed model, written apart from the reference | traces compared line for line as strings; two independent implementations agree on all 33 hand programs and 590 generated programs over seven seeds, with no mismatches |
