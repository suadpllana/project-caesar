# Instruction trace: lock-behind-escalate

Walked from the verifier toward the instruction (docs/INSTRUCTION-CONTRACT.md). The sealed
model is the test file here, because every graded token is `assert got == want` against it, so
it is split into one row per rule it applies. Checked with
`python tools/tracecheck.py lock-behind-escalate`.

## Graded assertions

| Verifier site | What it grades | Instruction sentence |
|---|---|---|
| `tests/test_outputs.py:119` test_frozen_truth_matches_the_model | the sealed side agrees with itself before it judges: the model still reproduces every frozen answer | the whole contract, whose printed form is "prints a line for each thing that happens" |
| `tests/test_outputs.py:129` test_hand_case | the thirty-seven enumerated scripts, line for line against the frozen answers, and that the script was not altered | "thirty-seven written by hand" |
| `tests/test_outputs.py:136` test_every_nonce_script_matches | the generated population, line for line against the model, and that no script was altered | "three scripts of each of those two shapes" and "three hundred and twenty smaller ones" |
| `tests/test_outputs.py:151` test_every_family_is_represented | that the population the run was graded on holds all ten families | "three hundred and twenty smaller ones, and thirty-seven written by hand" |
| `tests/cases.py:53` case conf-mode | shared with shared is compatible, anything with exclusive conflicts | "they are not both `s`" |
| `tests/cases.py:57` case conf-overlap | a table lock and a row lock of that table conflict both ways round | "a target overlaps itself, and a table overlaps every row of it" |
| `tests/cases.py:64` case plain-pass | a request on a row nobody has queued for is granted at once, whatever waits elsewhere | "not behind any earlier waiting request it conflicts with" |
| `tests/cases.py:68` case behind-writer | a reader waits behind a queued writer on its row although the holder is only a reader | "it is not behind any earlier waiting request it conflicts with; otherwise it waits" |
| `tests/cases.py:72` case behind-conflict | a reader passes a queued reader it does not conflict with | "any earlier waiting request it conflicts with" |
| `tests/cases.py:77` case cross-behind | a queued table request holds back a later row request on that table | "a table overlaps every row of it" and "any earlier waiting request it conflicts with" |
| `tests/cases.py:83` case skip-upgrade | a holder upgrading passes the queued writer that waits on its own lock | "It is not behind such a waiter when the transaction that made the earlier request is waiting, directly or through other waits, on the requester" |
| `tests/cases.py:86` case skip-two | two queued writers that both wait on the requester are both passed | "It is not behind such a waiter when the transaction that made the earlier request is waiting, directly or through other waits, on the requester" |
| `tests/cases.py:90` case skip-late | a queued request is granted in the settle of a later op when its blocker comes to wait on it | "After every op the manager settles" and "While some waiting request is grantable, the earliest of them is granted" |
| `tests/cases.py:94` case skip-soft-path | dependence runs through a waiter that is queued behind another waiter | "or with an earlier waiting request of the other" |
| `tests/cases.py:98` case soft-not-dead | a cycle that closes only through a queued request kills nobody | "there are transactions each waiting on a record the next one holds, around a cycle" |
| `tests/cases.py:102` case skip-chain | dependence runs through a holder that is itself waiting | "directly or through other waits, on the requester" |
| `tests/cases.py:109` case settle-earliest | of two requests freed by one commit the earlier is granted first | "the earliest of them is granted" |
| `tests/cases.py:113` case settle-order | a writer between two readers keeps the second reader behind it after the first is granted | "the earliest of them is granted" and "This goes on until nothing changes" |
| `tests/cases.py:120` case cover-same | a target already held in that mode or stronger records nothing, and the end count says so | "is granted at once and records nothing" |
| `tests/cases.py:123` case cover-table | rows under a table record are granted without a record | "or for a row of a table it holds in the requested mode or in `x`" |
| `tests/cases.py:126` case upgrade-place | shared to exclusive on one target is one record, raised in place | "when it is granted the record's mode becomes `x`" |
| `tests/cases.py:129` case subsume-s | a shared table grant releases shared rows and keeps exclusive ones | "in the same mode or a weaker one" |
| `tests/cases.py:132` case subsume-x | an exclusive table grant releases every row record on the table | "Once a table lock is granted, the row records the transaction holds on that table" |
| `tests/cases.py:137` case esc-trigger | K row records on one table escalate to a table lock | "if the transaction holds K or more row records on A it tries for A" |
| `tests/cases.py:140` case esc-mode | one exclusive row among them makes the table lock exclusive | "in `x` if any of those records is `x` and in `s` otherwise" |
| `tests/cases.py:143` case esc-holder-blocks | another transaction's row record refuses the escalation, and the escalator keeps its rows | "no record held by another transaction conflicts with it" and "Otherwise it is given up" |
| `tests/cases.py:146` case esc-holder-shared | another transaction's shared row does not refuse a shared escalation | "they are not both `s`" |
| `tests/cases.py:149` case esc-abandon | a refused escalation does not queue; the transaction goes on taking rows | "It never waits. It takes no sequence number" |
| `tests/cases.py:152` case esc-waiter-blocks | a queued writer that does not wait on the escalator refuses it | "The try is a request judged as if it had been made after every request that is waiting" |
| `tests/cases.py:156` case esc-waiter-depends | a queued writer that waits on the escalator does not refuse it | "The try is a request judged as if it had been made after every request that is waiting" and "directly or through other waits, on the requester" |
| `tests/cases.py:159` case esc-retry | a refused escalation is tried again at the next row grant on that table and not when a lock is released | "tried again only at its next row grant on A" |
| `tests/cases.py:162` case esc-count-drop | a dropped row no longer counts toward the threshold | "`drop` releases the record the transaction holds on exactly that target" and "holds K or more row records on A" |
| `tests/cases.py:164` case esc-count-cover | a covered row grant adds no record and counts for nothing, and a table held in `x` never escalates | "including one that recorded nothing" and "unless it already holds A in that mode or in `x`" |
| `tests/cases.py:166` case esc-under-shared | exclusive rows under a shared table record escalate to exclusive | "unless it already holds A in that mode or in `x`" |
| `tests/cases.py:171` case dead-fewest | the victim is the transaction on the cycle holding the fewest records, not the youngest | "the one holding the fewest records among all transactions on such cycles is killed" |
| `tests/cases.py:174` case dead-tie-recent | equal records: the transaction whose request is the most recent dies | "a tie going to the one whose waiting request is the most recent" |
| `tests/cases.py:177` case dead-then-grant | once the victim is gone the survivor's request is granted in the same settle | "releases them all, drops its request and is done" and "This goes on until nothing changes" |
| `tests/cases.py:183` case drop-none | dropping a lock that is not held changes nothing and prints nothing | "and does nothing when there is none" |
| `tests/cases.py:185` case drop-table | dropping a covered row does nothing, dropping the table record uncovers its rows for everyone | "`drop` releases the record the transaction holds on exactly that target" |
| `tests/cases.py:191` case order-first-line | transactions act in the order of their first line | "Transactions are ordered by their first line" |
| `tests/cases.py:194` case ordinary | no contention anywhere: every request is granted at once, nothing escalates, the counts are the records | "A request is granted only when no record held by another transaction conflicts with it" |
| artifact `/app/lm/held.py` | collected and laid over the pristine tree | "The files you may change are" |
| artifact `/app/lm/wait.py` | collected and laid over the pristine tree | "The files you may change are" |
| artifact `/app/lm/grant.py` | collected and laid over the pristine tree | "The files you may change are" |
| artifact `/app/lm/esc.py` | collected and laid over the pristine tree | "The files you may change are" |
| artifact `/app/lm/dead.py` | collected and laid over the pristine tree | "The files you may change are" |
| artifact `/app/lm/settle.py` | collected and laid over the pristine tree | "The files you may change are" |
| `tests/worker.py:40-44` the pristine overlay | nothing outside the six files can change what a script prints, a new file beside them included | "The rest of the tree is replaced by our own copy before a script is run, a new file put beside those six included" |
| `tests/test.sh:35` a 600 s clock | the whole graded set has to finish inside it, or the run scores 0 | "all of it has to get through inside 600 seconds" |
| `tests/seal/model.py:40-62` _parse | the script grammar: cfg first, then lock, drop and commit lines per transaction, transactions in order of first line | "`cfg K` opens the file and sets the escalation threshold" and "Transactions are ordered by their first line" |
| `tests/seal/model.py:65-66` _table | a row belongs to the table its name is written under | "or a row of one, written `<table>.<n>`" |
| `tests/seal/model.py:69-78` _State | a transaction's records, the waiting requests in sequence order, the sequence counter | "A transaction holds records. A record is one target in one mode, and a transaction holds at most one record per target" |
| `tests/seal/model.py:82-100` _State._index | the records and requests a lock can conflict with, by target and table | "a target overlaps itself, and a table overlaps every row of it" |
| `tests/seal/model.py:102-116` _State._holders | rule 1: what a held record conflicts with | "Two locks conflict when their targets overlap, they belong to different transactions, and they are not both `s`" |
| `tests/seal/model.py:118-119` _State._holder_blocks | a conflicting record held by another transaction blocks the request | "no record held by another transaction conflicts with it" |
| `tests/seal/model.py:121-136` _State._earlier | the earlier waiting requests the request conflicts with, earlier by sequence number | "Every `lock` op takes the next sequence number, so an earlier request is one made by an earlier `lock` op" |
| `tests/seal/model.py:138-146` _State._relation | what a waiting transaction waits on: holders of conflicting records and earlier conflicting waiters | "A waiting transaction waits on another when its request conflicts with a record the other holds, or with an earlier waiting request of the other" |
| `tests/seal/model.py:148-205` _State._closure | waiting through other waits: the transitive reach of every waiting transaction | "directly or through other waits, on the requester" |
| `tests/seal/model.py:207-215` _State._grantable | granted only with no holder conflict and no earlier conflicting waiter that does not depend on the requester | "A request is granted only when no record held by another transaction conflicts with it and it is not behind any earlier waiting request it conflicts with; otherwise it waits" and "It is not behind such a waiter when the transaction that made the earlier request is waiting, directly or through other waits, on the requester" |
| `tests/seal/model.py:219-225` _State._covered | the request records nothing when the target, or its table for a row, is held in that mode or in `x` | "A request for a target the transaction already holds in the requested mode or in `x`, or for a row of a table it holds in the requested mode or in `x`, is granted at once and records nothing" |
| `tests/seal/model.py:227-230` _State._take, the record | a new record, or an `s` record raised to `x` in place | "when it is granted the record's mode becomes `x`" |
| `tests/seal/model.py:231-234` _State._take, the subsuming | a table grant releases the rows it covers | "the row records the transaction holds on that table in the same mode or a weaker one are released" |
| `tests/seal/model.py:238-246` _State._escalate, the trigger | K or more row records on the table, the mode from those records, no try when the table is held in that mode or in `x` | "After any grant of a row of table A to a transaction, including one that recorded nothing, if the transaction holds K or more row records on A it tries for A, in `x` if any of those records is `x` and in `s` otherwise, unless it already holds A in that mode or in `x`" |
| `tests/seal/model.py:247-248` _State._escalate, the judgement | the try is judged with every waiting request counted as earlier and never queued | "The try is a request judged as if it had been made after every request that is waiting" and "It never waits. It takes no sequence number" |
| `tests/seal/model.py:249-250` _State._escalate, the taking | taken at once as a table grant, printing esc; otherwise nothing, until the next row grant there | "When it is grantable it is taken at once, as a table grant, and prints `esc`" and "Otherwise it is given up, and tried again only at its next row grant on A" |
| `tests/seal/model.py:252-256` _State._granted | the grant line, the record, and the escalation check after a row grant | "`grant T target mode` is printed when a request is granted, at once or later" and "an `esc` line follows the grant that brought it on" |
| `tests/seal/model.py:260-265` _State._victim, the cycle | a hard cycle: transactions each waiting on a record the next holds | "there are transactions each waiting on a record the next one holds, around a cycle" |
| `tests/seal/model.py:266-269` _State._victim, the choice | fewest records among every transaction on any such cycle, ties to the most recent request | "the one holding the fewest records among all transactions on such cycles is killed, a tie going to the one whose waiting request is the most recent" |
| `tests/seal/model.py:271-276` _State._finish | end or dead with the number of records released, everything released, the request dropped, the transaction done | "A killed transaction prints `dead` with its number of records, releases them all, drops its request and is done" and "`end T n` when T commits and `dead T n` when it is killed, where n is the number of records released" |
| `tests/seal/model.py:280-282` _State.lock, the number | every lock op takes the next sequence number | "Every `lock` op takes the next sequence number" |
| `tests/seal/model.py:283-286` _State.lock, covered | a covered request prints grant, records nothing, and still runs the escalation check for a row | "is granted at once and records nothing" and "including one that recorded nothing" |
| `tests/seal/model.py:287-291` _State.lock, granted or waiting | granted at once when grantable, otherwise the wait line and the queue | "otherwise it waits" and "`wait T target mode` when it first has to wait" |
| `tests/seal/model.py:293-294` _State.drop | the record on exactly that target goes, or nothing happens | "`drop` releases the record the transaction holds on exactly that target, and does nothing when there is none" |
| `tests/seal/model.py:296-297` _State.commit | every record released, the end line | "`commit` releases every record the transaction holds" |
| `tests/seal/model.py:299-315` _State.settle, the grants | the earliest grantable waiting request is granted, again and again | "While some waiting request is grantable, the earliest of them is granted" |
| `tests/seal/model.py:316-319` _State.settle, the victim | when nothing is grantable a hard cycle costs its victim, and the loop goes on | "When none is, and there are transactions each waiting on a record the next one holds, around a cycle" and "This goes on until nothing changes" |
| `tests/seal/model.py:321-322` _State.waiting | a transaction with a waiting request sits out its visits | "is not waiting for a lock and has an op left performs its next op" |
| `tests/seal/model.py:325-349` expect | rounds in order of first line, one op per visit, a settle after each, until nobody acts; only the five line kinds | "The driver is fixed and runs the transactions in rounds" and "A transaction granted a lock during a settle acts at its next visit" and "Nothing else is printed" |

## Readings

Every reading below is built by `authoring/lock-behind-escalate/emit.py`, measured by
`python tools/readingcheck.py lock-behind-escalate` and scored as a cheat. The table in
`readings.py` is assembled from `emit.py` at import, so the names are cited here by hand.

One further reading was written and turned out to be no reading at all: a request that waits
behind later conflicting waiters as well as earlier ones (`behind-any-seq`, retired). A later
conflicting waiter is itself behind the request, so it always waits on the requester and the
exception always applies; the reading agrees with the reference on every script, and a solver
who drops the word earlier from the behind rule is still correct.

| Reading | Sentence or published example that rules it out | Case that separates it |
|---|---|---|
| holders-only: a request waits for holders only, never behind an earlier waiter | "it is not behind any earlier waiting request it conflicts with; otherwise it waits" | behind-writer |
| behind-all: a request waits behind every earlier waiter, conflicting or not | "any earlier waiting request it conflicts with" | plain-pass |
| same-target-only: earlier waiters are looked for on the same target only | "a table overlaps every row of it" | cross-behind |
| no-skip: an earlier conflicting waiter always holds the request back | "It is not behind such a waiter when the transaction that made the earlier request is waiting, directly or through other waits, on the requester" | skip-upgrade |
| skip-hard-only: dependence follows held records only, never a queued request | "or with an earlier waiting request of the other" | skip-soft-path |
| skip-at-arrival: behind-or-not is decided when the request arrives and never again | "After every op the manager settles" and "While some waiting request is grantable, the earliest of them is granted" | skip-late |
| settle-latest-first: settling grants the most recent grantable request first | "the earliest of them is granted" | settle-earliest |
| cover-records: a row granted under a table record is recorded all the same | "is granted at once and records nothing" | cover-table |
| no-subsume: a table grant leaves the row records it covers in place | "Once a table lock is granted, the row records the transaction holds on that table" | subsume-x |
| drop-covered-table: dropping a covered row releases the table record instead | "`drop` releases the record the transaction holds on exactly that target, and does nothing when there is none" | drop-table |
| esc-queues: a refused escalation queues for the table lock like any request | "It never waits. It takes no sequence number" | esc-abandon |
| esc-holders-only: escalation asks the holders and never the waiting requests | "The try is a request judged as if it had been made after every request that is waiting" | esc-waiter-blocks |
| esc-always-shared: escalation always takes the table in shared mode | "in `x` if any of those records is `x` and in `s` otherwise" | esc-mode |
| esc-counts-grants: the threshold counts row grants, never records held | "if the transaction holds K or more row records on A" | esc-count-drop |
| esc-count-all: the threshold counts the transaction's rows on every table | "holds K or more row records on A" | esc-holder-blocks |
| esc-never: no escalation ever happens | "if the transaction holds K or more row records on A it tries for A" | esc-trigger |
| esc-retry-settle: a refused escalation is tried again whenever the manager settles | "tried again only at its next row grant on A" | esc-retry |
| victim-youngest: the victim is the youngest transaction on the cycle | "the one holding the fewest records among all transactions on such cycles is killed" | dead-fewest |
| victim-tie-earliest: equal records, the earlier request dies | "a tie going to the one whose waiting request is the most recent" | dead-tie-recent |
| soft-cycle-dead: a cycle through a queued request counts as a deadlock | "there are transactions each waiting on a record the next one holds, around a cycle" | soft-not-dead |

## Shortcuts

| Strategy | Result |
|---|---|
| the shipped tree unchanged (the nop) | reward 0 in the container; 26 of 40 graded assertions fail; on the host it is wrong on 220 of 320 sampled generated scripts and 26 of 37 hand scripts |
| constant: every request is granted the moment it is made, the most common line kind for every lock op (cheat-const-grant) | reward 0; fails 22 of 37 hand scripts and 90 of 96 sampled generated ones |
| positional: the youngest transaction on the cycle always dies (cheat-victim-youngest) | reward 0; fails dead-fewest and dead-tie-recent and 14 of 96 sampled generated scripts |
| the worked examples replayed: the frozen answers for every hand script keyed by script hash, over the shipped tree (cheat-forge-hand) | reward 0; passes all 37 hand scripts and fails 62 of 96 sampled generated ones it could not have seen |

## Tolerances

| Tolerance or limit | Independent implementation | Measured |
|---|---|---|
| `tests/test.sh:35` a 600 s clock on the whole graded set | `authoring/lock-behind-escalate/variants/ok-fix` and `authoring/lock-behind-escalate/variants/ok-flat`, both written apart from the reference, and `tests/seal/model.py` | per scale script on this machine: reference 3.3 s wide and 4.5 s deep, ok-fix 6.8 s and 7.5 s, ok-flat 5.2 s and 29.7 s, the model 16 s and 9 s; whole graded set for the reference 44 s in the container against 600 s; the search-per-pair implementation in `authoring/lock-behind-escalate/naive` takes 71 s on a wide script and over 300 s on one deep script (cheat-slow-search) |
| exactness: the trace is compared string for string, no tolerance | `tests/seal/model.py`, written from the frozen contract, not from the reference | 800 generated scripts plus the scale families agree between the reference, the model and both variants |
