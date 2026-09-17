# Instruction trace: claim-cover-lift

Walked from the verifier toward the instruction (docs/INSTRUCTION-CONTRACT.md). Every
graded assertion, enumerated case, model rule, collected artifact and clock has a row and
the sentence it traces to. Built by `authoring/claim-cover-lift/make_trace.py`; checked
with `python tools/tracecheck.py claim-cover-lift`.

## Graded assertions

| Verifier site | What it grades | Instruction sentence |
|---|---|---|
| `tests/test_outputs.py:116` test_the_model_still_makes_the_frozen_answers | that the sealed model still reproduces the frozen answers before anything is judged by it | "every line it prints is compared with the line expected, in order" |
| `tests/test_outputs.py:126` test_enumerated_program | the trace of every enumerated program, line for line, against the frozen answers | "every line it prints is compared with the line expected, in order" |
| `tests/test_outputs.py:135` test_generated_program | the trace of every generated program against the sealed model | "The graded programs are generated after your container is gone" |
| `tests/test_outputs.py:154` test_every_family_was_run | that the population the worker ran is the one the grader asked for, so a shrunken exam fails | "Nothing else you write is read" |
| `tests/cases.py` case again-drop | a second acquire survives the first drop | "A claim granted to a job adds one acquire, so what a job holds on a node is the list of acquires granted to it there" |
| `tests/cases.py` case again-lower | a drop takes back the most recent acquire and what is left grants a reader | "A drop gives back the one added most recently and prints free" |
| `tests/cases.py` case busy-line | a line naming a job whose request is waiting does nothing | "A job ignores every line naming it while its own request is waiting, after it has ended, and after it has been stopped" |
| `tests/cases.py` case cover-ahead | a covered request is granted although an older request is waiting | "A request is granted at once, ahead of anything that would otherwise block it, when the asking job already holds a claim on that node or on its box in a mode that covers it" |
| `tests/cases.py` case cover-mode | a claim held in r does not cover a request in w | "a claim in w covers a request in either mode, and a claim in r covers a request in r" |
| `tests/cases.py` case cover-up-only | a claim on a slot does not cover a request for the box | "A claim on a slot covers nothing on its box" |
| `tests/cases.py` case drop-none | a drop naming a node the job does not hold prints nothing | "a drop naming a node the job does not hold prints nothing" |
| `tests/cases.py` case end-line | a line naming a finished job does nothing | "A job ignores every line naming it while its own request is waiting, after it has ended, and after it has been stopped" |
| `tests/cases.py` case end-order | end frees in node order, with numbers compared as numbers | "Nodes are put in order by box number first, a box before its own slots, then by slot number" |
| `tests/cases.py` case fair-queue | a compatible request waits behind an older conflicting one | "It is blocked by a granted claim of another job that conflicts with it, and by a waiting request of another job that conflicts with it and holds a smaller sequence number" |
| `tests/cases.py` case fam-box-slot | a claim on a box blocks another job's request for one of its slots | "A claim on a box conflicts with another job's claims on that box and on every slot of it" |
| `tests/cases.py` case fam-sibling | two jobs claiming different slots of one box are both granted at once | "claims on two different slots never conflict, and a job's own claims never conflict with its own request" |
| `tests/cases.py` case fam-slot-box | a claim on a slot blocks another job's request for its box | "a claim on a slot conflicts with another job's claims on that slot and on its box" |
| `tests/cases.py` case lift-covered | a job already covering the box does not lift | "A request for a slot is lifted when the asking job holds no claim covering it on that slot's box and already holds granted claims on four or more distinct slots of that box" |
| `tests/cases.py` case lift-few | a drop below four distinct slots means no lift | "A request for a slot is lifted when the asking job holds no claim covering it on that slot's box and already holds granted claims on four or more distinct slots of that box" |
| `tests/cases.py` case lift-floor | the fifth distinct slot of a box lifts the request to the box | "A request for a slot is lifted when the asking job holds no claim covering it on that slot's box and already holds granted claims on four or more distinct slots of that box" |
| `tests/cases.py` case lift-free-order | a granted lift frees in slot order, not in the order taken | "the job's acquires on every slot of that box are given back in slot order, each printing free, and then the request that caused the lift is granted" |
| `tests/cases.py` case lift-mode | a lift takes w because one of the claims it replaces is in w | "The request becomes a request for the box, in mode w if it or any of those claims is in w and in r otherwise" |
| `tests/cases.py` case lift-repeat | four acquires over three slots do not reach the floor | "A request for a slot is lifted when the asking job holds no claim covering it on that slot's box and already holds granted claims on four or more distinct slots of that box" |
| `tests/cases.py` case lift-two | two lifts in one box wait for each other and one job is stopped | "of every job lying on any cycle, the one holding the fewest acquires counted with repetition, and on a tie the one with the largest job number" |
| `tests/cases.py` case lift-wait | a lift that cannot be granted waits and keeps its slot claims | "A lifted request that waits keeps the job's slot claims until it is granted" |
| `tests/cases.py` case read-share | two readers share a slot and a writer waits behind them | "Two modes conflict when at least one of them is w" |
| `tests/cases.py` case ring-count | acquires are counted with repetition when the victim is chosen | "of every job lying on any cycle, the one holding the fewest acquires counted with repetition, and on a tie the one with the largest job number" |
| `tests/cases.py` case ring-fair | a cycle that runs through an older waiting request is found | "One job waits for another when that other blocks its waiting request, whether by a granted claim or by an older waiting request" |
| `tests/cases.py` case ring-tie | a tie on acquires goes to the larger job number | "of every job lying on any cycle, the one holding the fewest acquires counted with repetition, and on a tie the one with the largest job number" |
| `tests/cases.py` case ring-two | the job on the cycle with fewer acquires is stopped | "of every job lying on any cycle, the one holding the fewest acquires counted with repetition, and on a tie the one with the largest job number" |
| `tests/cases.py` case seq-across | grants owed in two boxes come out in one store-wide order | "sequence numbers come from one counter for the whole store rather than one per node" |
| `tests/cases.py` case show-format | a query lists jobs by number with every acquire as a sorted letter | "A show prints at and the node, then every job holding that node in job order, each followed by its acquires as mode letters sorted together" |
| `tests/cases.py` case show-none | a query on a node nobody holds prints the node alone | "A show prints at and the node, then every job holding that node in job order, each followed by its acquires as mode letters sorted together" |
| `tests/cases.py` case split-boxes | jobs working in different boxes never wait for each other | "claims on two different slots never conflict, and a job's own claims never conflict with its own request" |
| `tests/cases.py` case stop-line | a line naming a stopped job does nothing | "A job ignores every line naming it while its own request is waiting, after it has ended, and after it has been stopped" |
| `tests/cases.py` case sweep-chain | one release grants every request that becomes grantable | "the waiting request with the smallest sequence number that can now be granted is granted, and that repeats until no waiting request can be granted" |
| artifact `/app/hb/hold.py` | only the declared files are collected | "Six files are taken from your container" |
| artifact `/app/hb/fit.py` | only the declared files are collected | "Six files are taken from your container" |
| artifact `/app/hb/line.py` | only the declared files are collected | "Six files are taken from your container" |
| artifact `/app/hb/lift.py` | only the declared files are collected | "Six files are taken from your container" |
| artifact `/app/hb/knot.py` | only the declared files are collected | "Six files are taken from your container" |
| artifact `/app/hb/gate.py` | only the declared files are collected | "Six files are taken from your container" |
| `tests/test.sh:27` a 60 s clock | the whole graded set must finish inside it | "must finish within 60 seconds" |
| `tests/seal/model.py:38-42` | boxof: a slot name carries its box, so the family is a box and its slots | "It has two levels: boxes, named b1, b2 and so on, and slots inside them" |
| `tests/seal/model.py:43-49` | nkey: node order is box number, the box before its slots, then slot number, as numbers | "Nodes are put in order by box number first, a box before its own slots, then by slot number" |
| `tests/seal/model.py:50-53` | jkey: jobs are ordered by the number in the name | "Jobs are put in order by number the same way" |
| `tests/seal/model.py:54-55` | clash: two modes conflict when at least one is w | "Two modes conflict when at least one of them is w" |
| `tests/seal/model.py:58-66` | Ask: a waiting request keeps its job, node, mode, sequence number and lift trigger | "A request that is blocked prints wait and takes the next sequence number" |
| `tests/seal/model.py:67-80` | Engine: the state the operations act on | "The operations are `take <job> <node> <mode>`, `drop <job> <node>`, `end <job>`, `show <node>`, and `fill <job> <box> <count> <mode>`" |
| `tests/seal/model.py:84-92` | put: a take adds one acquire to what the job holds on that node | "A claim granted to a job adds one acquire, so what a job holds on a node is the list of acquires granted to it there" |
| `tests/seal/model.py:93-116` | take_off: a drop removes the acquire added most recently | "A drop gives back the one added most recently and prints free" |
| `tests/seal/model.py:117-119` | acquires: a job's acquires are counted with repetition | "of every job lying on any cycle, the one holding the fewest acquires counted with repetition, and on a tie the one with the largest job number" |
| `tests/seal/model.py:120-130` | free_all: everything a job holds is given back in node order, each printing free | "An end gives back every acquire the job holds in node order, each printing free, prints done, and then granting resumes" |
| `tests/seal/model.py:131-137` | covers: a claim on the node or its box in a covering mode grants at once | "A request is granted at once, ahead of anything that would otherwise block it, when the asking job already holds a claim on that node or on its box in a mode that covers it" |
| `tests/seal/model.py:131-137` | covers: w covers either mode, r covers r, and a slot claim covers nothing above it | "a claim in w covers a request in either mode, and a claim in r covers a request in r" |
| `tests/seal/model.py:138-149` | blocked_by: a conflicting granted claim of another job in the family blocks | "A claim on a box conflicts with another job's claims on that box and on every slot of it" |
| `tests/seal/model.py:150-163` | blocked_by: an older conflicting waiting request of another job blocks | "It is blocked by a granted claim of another job that conflicts with it, and by a waiting request of another job that conflicts with it and holds a smaller sequence number" |
| `tests/seal/model.py:164-171` | park: a blocked request prints wait and takes the next number from one counter | "sequence numbers come from one counter for the whole store rather than one per node" |
| `tests/seal/model.py:172-181` | unpark: a granted or cancelled request leaves the line | "the waiting request with the smallest sequence number that can now be granted is granted, and that repeats until no waiting request can be granted" |
| `tests/seal/model.py:182-188` | hand: a grant records the acquire and prints grant | "The events are `grant <job> <node> <mode>`, `wait <job> <node> <mode>`, `lift <job> <box> <mode>`, `free <job> <node>`, `stop <job>`, `done <job>`" |
| `tests/seal/model.py:189-196` | hand: a granted lift frees the box's slot claims in slot order, then grants its trigger | "the job's acquires on every slot of that box are given back in slot order, each printing free, and then the request that caused the lift is granted" |
| `tests/seal/model.py:197-203` | ready: the smallest numbered grantable request of a box | "the waiting request with the smallest sequence number that can now be granted is granted, and that repeats until no waiting request can be granted" |
| `tests/seal/model.py:204-221` | sweep: grants repeat in sequence order until nothing more can be granted | "the waiting request with the smallest sequence number that can now be granted is granted, and that repeats until no waiting request can be granted" |
| `tests/seal/model.py:222-227` | edges: a job waits for the jobs that block its waiting request | "One job waits for another when that other blocks its waiting request, whether by a granted claim or by an older waiting request" |
| `tests/seal/model.py:228-272` | tangle: every job lying on a cycle through the job that has just started waiting | "of every job lying on any cycle, the one holding the fewest acquires counted with repetition, and on a tie the one with the largest job number" |
| `tests/seal/model.py:273-282` | cut: stopping prints stop, drops the request and frees in node order | "Stopping prints stop, takes that job's waiting request out of the line, and gives back every acquire it holds in node order, each printing free" |
| `tests/seal/model.py:283-292` | settle: a victim is taken while any job still lies on a cycle | "Granting then resumes, and the check is made again, until no job lies on a cycle" |
| `tests/seal/model.py:293-300` | take: a job acts only when it is not waiting, stopped or finished | "A job ignores every line naming it while its own request is waiting, after it has ended, and after it has been stopped" |
| `tests/seal/model.py:301-308` | take: a slot request lifts at four distinct slots, in w if any of them is w | "The request becomes a request for the box, in mode w if it or any of those claims is in w and in r otherwise" |
| `tests/seal/model.py:309-313` | take: an unblocked request is granted, a blocked one waits and the check runs | "It is blocked by a granted claim of another job that conflicts with it, and by a waiting request of another job that conflicts with it and holds a smaller sequence number" |
| `tests/seal/model.py:314-320` | drop: a removed acquire prints free and granting resumes | "A drop gives back the one added most recently and prints free" |
| `tests/seal/model.py:321-328` | end: frees in node order, prints done, then granting resumes | "An end gives back every acquire the job holds in node order, each printing free, prints done, and then granting resumes" |
| `tests/seal/model.py:329-336` | show: the holders of a node, by job number, with sorted mode letters | "A show prints at and the node, then every job holding that node in job order, each followed by its acquires as mode letters sorted together" |
| `tests/seal/model.py:337-353` | expect: the operation names, and fill as a take of s1 to s<count> | "The operations are `take <job> <node> <mode>`, `drop <job> <node>`, `end <job>`, `show <node>`, and `fill <job> <box> <count> <mode>`" |

## Readings

| Reading | Sentence or published example that rules it out | Case that separates it |
|---|---|---|
| fit-node-only | "A claim on a box conflicts with another job's claims on that box and on every slot of it" | fam-box-slot |
| fit-slot-blind | "a claim on a slot conflicts with another job's claims on that slot and on its box" | fam-slot-box |
| fit-no-line | "It is blocked by a granted claim of another job that conflicts with it, and by a waiting request of another job that conflicts with it and holds a smaller sequence number" | fair-queue |
| cover-none | "A request is granted at once, ahead of anything that would otherwise block it, when the asking job already holds a claim on that node or on its box in a mode that covers it" | cover-ahead |
| cover-any-mode | "a claim in w covers a request in either mode, and a claim in r covers a request in r" | cover-mode |
| cover-downward | "A claim on a slot covers nothing on its box" | cover-up-only |
| cover-not-kept | "A claim granted to a job adds one acquire, so what a job holds on a node is the list of acquires granted to it there" | cover-ahead |
| hold-one-mode | "A claim granted to a job adds one acquire, so what a job holds on a node is the list of acquires granted to it there" | again-drop |
| drop-oldest | "A drop gives back the one added most recently and prints free" | again-lower |
| hold-ever-held | "A request for a slot is lifted when the asking job holds no claim covering it on that slot's box and already holds granted claims on four or more distinct slots of that box" | lift-few |
| order-by-text | "the numbers compare as numbers, so b10 comes after b2 and s12 after s2" | end-order |
| show-last-mode | "A show prints at and the node, then every job holding that node in job order, each followed by its acquires as mode letters sorted together" | show-format |
| show-text-order | "Jobs are put in order by number the same way" | show-format |
| sweep-per-box | "sequence numbers come from one counter for the whole store rather than one per node" | seq-across |
| end-no-sweep | "An end gives back every acquire the job holds in node order, each printing free, prints done, and then granting resumes" | seq-across |
| lift-give-up | "A lifted request that waits keeps the job's slot claims until it is granted" | lift-wait |
| lift-take-order | "the job's acquires on every slot of that box are given back in slot order, each printing free, and then the request that caused the lift is granted" | lift-free-order |
| lift-count-acquires | "A request for a slot is lifted when the asking job holds no claim covering it on that slot's box and already holds granted claims on four or more distinct slots of that box" | lift-repeat |
| lift-trigger-mode | "The request becomes a request for the box, in mode w if it or any of those claims is in w and in r otherwise" | lift-mode |
| lift-keeps-slots | "the job's acquires on every slot of that box are given back in slot order, each printing free, and then the request that caused the lift is granted" | lift-floor |
| knot-holders-only | "One job waits for another when that other blocks its waiting request, whether by a granted claim or by an older waiting request" | ring-fair |
| knot-first-found | "of every job lying on any cycle, the one holding the fewest acquires counted with repetition, and on a tie the one with the largest job number" | ring-two |
| knot-count-nodes | "of every job lying on any cycle, the one holding the fewest acquires counted with repetition, and on a tie the one with the largest job number" | ring-count |
| knot-tie-small | "of every job lying on any cycle, the one holding the fewest acquires counted with repetition, and on a tie the one with the largest job number" | ring-tie |
| knot-keeps-request | "Stopping prints stop, takes that job's waiting request out of the line, and gives back every acquire it holds in node order, each printing free" | ring-two |
| busy-acts | "A job ignores every line naming it while its own request is waiting, after it has ended, and after it has been stopped" | busy-line |
| stopped-acts | "A job ignores every line naming it while its own request is waiting, after it has ended, and after it has been stopped" | stop-line |

## Shortcuts

| Strategy | Result |
|---|---|
| the shipped tree unchanged (nop) | scores 0; matches 13 of the 32 enumerated programs and 7 of 48 generated ones |
| positional: every request granted at once, nothing ever waits | scores 0 as cheat-shortcut-grant-all; matches 9 of 32 and 0 of 48 |
| constant: the brief's own worked example replayed for every program | scores 0 as cheat-shortcut-replay-example; matches 0 of 32 and 0 of 48 |
| the previous revision of the reference | there is none that differs: the shipped tree is the engine the reference replaces, and it is the nop row above |
| an answer key for every enumerated program | scores 0 as cheat-forge-answer-key; passes all 32 enumerated programs and fails the generated population it could not have seen |

## Tolerances

| Tolerance or limit | Independent implementation | Measured |
|---|---|---|
| `tests/test.sh` the 60 s clock on the graded run | `authoring/claim-cover-lift/variants/jobmajor`, written apart from the reference | 4.1 s over the whole graded set against the 60 s limit, with the reference at 2.4 s and the three correct-but-walking readings at 90 s, 323 s and 639 s |
