# Instruction trace: lock-cover-wake

Walked from the verifier toward the instruction (docs/INSTRUCTION-CONTRACT.md). Every graded
assertion, every enumerated case, every rule the sealed model applies and every condition in
`tests/test.sh` that can turn a run into a 0, each with the sentence of `instruction.md` that
tells the agent about it. Checked with `python tools/tracecheck.py lock-cover-wake`.

## Graded assertions

| Verifier site | What it grades | Instruction sentence |
|---|---|---|
| `tests/test_outputs.py:118` test_frozen_truth_matches_the_model | the sealed side agrees with itself before it judges; it grades nothing the agent wrote, and what it pins is the behaviour the brief promises | "takes a script and prints a line for each thing that happens" |
| `tests/test_outputs.py:128` test_hand_case | every enumerated script prints exactly the frozen lines, in order | "prints a line for each thing that happens" |
| `tests/test_outputs.py:137` test_every_nonce_script_matches | every generated script prints exactly what the model prints | "The graded set is three scripts of each of those two sizes" |
| `tests/test_outputs.py:156` test_every_family_is_represented | the population the worker ran is the one the grader generated | "The graded set is three scripts of each of those two sizes" |
| `tests/cases.py:49` case plain | slack everywhere: every request granted at once, nothing queued, felled, raised or covered | "A new request is granted at once when nothing is queued on that resource and no other transaction holds a mode conflicting with it" |
| `tests/cases.py:65` case cov-own | a mode already held on that same resource takes no lock and is counted | "A request for a mode the transaction already covers takes no lock and prints nothing" |
| `tests/cases.py:73` case cov-table | a row under a table lock strong enough for it takes no lock | "for a row, by the lock it holds on that row's table" |
| `tests/cases.py:81` case cov-six | SIX covers a row in S and does not cover a row in X | "SIX covers IS, IX and S; X covers every mode" |
| `tests/cases.py:89` case cov-not | IX covers neither a row in S nor a row in X, so both are taken | "IX and S each cover IS and cover nothing of each other" |
| `tests/cases.py:98` case int-first | a row request takes the intention on its table first | "A row in S needs IS on its table and a row in X needs IX" |
| `tests/cases.py:103` case int-wait | a queued intention request carries the row request and makes it on the grant | "the row request goes into the queue with it and is made at the moment the table request is granted" |
| `tests/cases.py:111` case int-drop | a felled transaction loses the row request its intention request was carrying | "loses the request it was waiting for and the row request that request was carrying" |
| `tests/cases.py:124` case conv-cover | a conversion goes to the cover of the two modes | "to the cover of the mode it holds there and the mode it asks for" |
| `tests/cases.py:130` case conv-self | a conversion is tested against the other holders only | "tested against what the other transactions hold, never against its own" |
| `tests/cases.py:136` case conv-jump | a conversion passes queued new requests | "so it passes queued new requests" |
| `tests/cases.py:146` case conv-behind | a conversion waits behind a queued conversion | "A conversion is granted at once when no conversion is queued on that resource" |
| `tests/cases.py:157` case new-behind | a compatible new request waits behind a queued request | "A new request is granted at once when nothing is queued on that resource" |
| `tests/cases.py:168` case fell-young | an older requester fells a younger holder and takes the lock | "It takes the transactions holding a conflicting mode on that resource in begin order and fells each one it began before the standing of" |
| `tests/cases.py:175` case fell-older | a younger requester queues rather than felling | "fells each one it began before the standing of" |
| `tests/cases.py:182` case fell-order | several conflicting holders are felled in begin order, not in the order the entry holds them | "holding a conflicting mode on that resource in begin order" |
| `tests/cases.py:193` case fell-shield | a holder with an older waiter on another entry it holds is not felled | "every transaction with a request waiting on a resource that holder holds" |
| `tests/cases.py:205` case fell-queued | a request blocked only by the queue fells all the same, then queues | "Before it settles for waiting, a request that cannot be granted fells" |
| `tests/cases.py:214` case fell-skip | the entry being asked for does not shield its own holder | "other than the one being asked for" |
| `tests/cases.py:225` case age-beg | age is begin order, not the transaction number | "One transaction is older than another when it began first; the numbers they are given say nothing about that" |
| `tests/cases.py:234` case wake-oldest | one commit frees two entries and the earlier-begun head is granted first | "taking the one whose transaction began earliest first" |
| `tests/cases.py:245` case wake-cont | the row request a granted head was carrying joins the queue behind a waiting one | "and is made at the moment the table request is granted, against the lock table as it stands then" |
| `tests/cases.py:256` case wake-nofell | a waiting head that reaches the front fells nobody | "granted because no other transaction holds a conflicting mode; it fells nobody" |
| `tests/cases.py:269` case sub-covered | a table grant releases the rows that mode covers and only those | "releases the rows of that table that the granted mode covers, and only those" |
| `tests/cases.py:277` case sub-none | a grant to IX releases no rows at all | "releases the rows of that table that the granted mode covers, and only those" |
| `tests/cases.py:283` case sub-tally | rows released by subsumption are gone from the count the limit is read from | "A row grant that leaves the transaction holding E or more row locks on that table" |
| `tests/cases.py:294` case esc-fires | the limit raises the table lock and the rows go with it | "raises its table lock, once" |
| `tests/cases.py:301` case esc-mode | one row in X makes the raise go to X rather than S | "with S when every one of those row locks is S, and with X otherwise" |
| `tests/cases.py:308` case esc-drop | a raise the table is held against is abandoned and prints nothing | "a raise that cannot be granted prints nothing" |
| `tests/cases.py:317` case esc-again | the next row grant at the limit tries the raise again | "is tried again at the next row grant that leaves the transaction at the limit" |
| `tests/cases.py:328` case esc-nofell | a raise fells nobody however old the transaction raising is | "It never joins the queue and it fells nobody" |
| `tests/cases.py:337` case esc-nocount | covered requests never count toward the limit | "A request for a mode the transaction already covers takes no lock and prints nothing" |
| `tests/cases.py:348` case pass-wait | a command for a waiting transaction is passed over | "A command naming a transaction that is waiting is passed over" |
| `tests/cases.py:358` case pass-cut | a command for a felled transaction is passed over | "So is one naming a transaction that has been felled or has committed" |
| `tests/cases.py:367` case pass-done | a command for a committed transaction is passed over | "naming a transaction that has been felled or has committed" |
| `tests/cases.py:377` case rep-order | locks are reported in acquisition order, a retaken one at the end | "a conversion leaving a resource where it is and a resource taken again after being released going to the end" |
| `tests/cases.py:386` case rep-res | queues are reported in resource order, a table ahead of its own rows | "those resources in ascending order with a table ahead of its own rows" |
| `tests/cases.py:398` case rep-state | the four state words | "`run`, `wait`, `cut` for felled or `done` for committed" |
| `tests/cases.py` case plan-tiny | the sample script the brief quotes a line of, graded exactly as it ships | "The line for transaction 41 comes out `tx 41 run`, and it should read `tx 41 wait`" |
| `tests/cases.py` case plan-pair | the second sample script, graded exactly as it ships | "`/app/plans` holds four scripts" |
| artifact `/app/lk/mode.py` | only the declared files are collected | "The files you may change are `/app/lk/mode.py`" |
| artifact `/app/lk/ent.py` | only the declared files are collected | "The files you may change are `/app/lk/mode.py`, `/app/lk/ent.py`, `/app/lk/txn.py`, `/app/lk/ask.py`, `/app/lk/wake.py`, `/app/lk/lift.py` and `/app/lk/tell.py`" |
| artifact `/app/lk/txn.py` | only the declared files are collected | "The files you may change are `/app/lk/mode.py`, `/app/lk/ent.py`, `/app/lk/txn.py`, `/app/lk/ask.py`, `/app/lk/wake.py`, `/app/lk/lift.py` and `/app/lk/tell.py`" |
| artifact `/app/lk/ask.py` | only the declared files are collected | "The files you may change are `/app/lk/mode.py`, `/app/lk/ent.py`, `/app/lk/txn.py`, `/app/lk/ask.py`, `/app/lk/wake.py`, `/app/lk/lift.py` and `/app/lk/tell.py`" |
| artifact `/app/lk/wake.py` | only the declared files are collected | "The files you may change are `/app/lk/mode.py`, `/app/lk/ent.py`, `/app/lk/txn.py`, `/app/lk/ask.py`, `/app/lk/wake.py`, `/app/lk/lift.py` and `/app/lk/tell.py`" |
| artifact `/app/lk/lift.py` | only the declared files are collected | "The files you may change are `/app/lk/mode.py`, `/app/lk/ent.py`, `/app/lk/txn.py`, `/app/lk/ask.py`, `/app/lk/wake.py`, `/app/lk/lift.py` and `/app/lk/tell.py`" |
| artifact `/app/lk/tell.py` | only the declared files are collected | "The files you may change are `/app/lk/mode.py`, `/app/lk/ent.py`, `/app/lk/txn.py`, `/app/lk/ask.py`, `/app/lk/wake.py`, `/app/lk/lift.py` and `/app/lk/tell.py`" |
| a new file beside the seven is never collected | the route-around guard | "a new file put beside those seven included" |
| `tests/worker.py:59` the engine is reached as `lk.ask.Engine` and `lk.tell.report` | required entry points | "builds `lk.ask.Engine` on the list the lines go into, calls its `step` once for each command in order" |
| `tests/test.sh:35` a 60 s clock | the whole graded set must run inside 60 seconds | "all of it has to get through inside 60 seconds" |
| `tests/seal/model.py:54` strong | one mode covers another exactly when the lattice says so | "IX and S each cover IS and cover nothing of each other; SIX covers IS, IX and S; X covers every mode" |
| `tests/seal/model.py:59` join | the cover of two modes is the weakest covering both | "The cover of two modes is the weakest mode covering both, so IX with S is SIX" |
| `tests/seal/model.py:71` cut | a resource is a table or `<table>.<row>` | "A resource is a table, written as a number, or a row of one, written `<table>.<row>`" |
| `tests/seal/model.py:96` Run.clash | two modes on one resource conflict per the matrix | "Two modes held on one resource by different transactions conflict unless one of them is IS and the other is anything but X, or both are IX, or both are S" |
| `tests/seal/model.py:103` Run.head | the queue holds conversions ahead of new requests, each in request order | "conversions ahead of new requests and each of the two in the order the requests were made" |
| `tests/seal/model.py:110` Run.requeue | the earliest begin waiting on an entry is what its holders stand under | "the earliest begin among the holder itself and every transaction with a request waiting on a resource that holder holds" |
| `tests/seal/model.py:142` Run.stand | the standing leaves out the entry being asked for | "other than the one being asked for" |
| `tests/seal/model.py:155` Run.step (cfg) | `cfg E` sets the row limit | "`cfg E` sets the row limit used below" |
| `tests/seal/model.py:155` Run.step (beg) | begin order is the order the `beg` commands appear | "One transaction is older than another when it began first" |
| `tests/seal/model.py:155` Run.step (req, com) | a command for a waiting, felled or committed transaction is passed over | "A command naming a transaction that is waiting is passed over" |
| `tests/seal/model.py:155` Run.step (com) | a commit releases every lock the transaction holds | "asks for a lock and `com t` commits" |
| `tests/seal/model.py:179` Run.want (own lock) | a mode already covered on that resource takes no lock and is counted | "It is covered by the lock that transaction holds on the resource asked for" |
| `tests/seal/model.py:179` Run.want (table lock) | a row covered by its table's lock takes no lock and is counted | "or, for a row, by the lock it holds on that row's table" |
| `tests/seal/model.py:179` Run.want (intention) | the intention request is made first and carries the row request | "That table request is made first, and when it cannot be granted at once the row request goes into the queue with it" |
| `tests/seal/model.py:197` Run.offer (class) | a request by a holder is a conversion to the cover of the two modes | "A request by a transaction that already holds the resource is a conversion, to the cover of the mode it holds there and the mode it asks for" |
| `tests/seal/model.py:197` Run.offer (felling) | conflicting holders are felled in begin order against their standing | "It takes the transactions holding a conflicting mode on that resource in begin order and fells each one it began before the standing of" |
| `tests/seal/model.py:197` Run.offer (retry) | the request is tried again after the fellings | "The request is then tried again" |
| `tests/seal/model.py:197` Run.offer (queue) | a request that is not granted joins its class in request order and prints `wt` | "`wt <transaction> <resource> <mode>` whenever a request joins the queue" |
| `tests/seal/model.py:224` Run.open | no-bypass for a new request, conversions past new requests only | "A new request is granted at once when nothing is queued on that resource and no other transaction holds a mode conflicting with it" |
| `tests/seal/model.py:232` Run.give (grant) | a grant prints `gr` with the mode now held | "`gr <transaction> <resource> <mode>` is printed for every grant, carrying the mode the transaction holds once it is done" |
| `tests/seal/model.py:232` Run.give (subsumption) | a table grant releases the rows that mode covers and only those, silently | "A grant of a table lock releases the rows of that table that the granted mode covers, and only those" |
| `tests/seal/model.py:232` Run.give (acquisition order) | a conversion keeps its place, a retaken resource goes to the end | "a conversion leaving a resource where it is and a resource taken again after being released going to the end" |
| `tests/seal/model.py:232` Run.give (continuation) | the carried row request is made at the moment the intention is granted | "and is made at the moment the table request is granted, against the lock table as it stands then" |
| `tests/seal/model.py:253` Run.bigger (limit) | the raise fires on a row grant that leaves the transaction at E rows | "A row grant that leaves the transaction holding E or more row locks on that table raises its table lock, once" |
| `tests/seal/model.py:253` Run.bigger (mode) | the raise goes to the cover with S when every row lock is S, X otherwise | "with S when every one of those row locks is S, and with X otherwise" |
| `tests/seal/model.py:253` Run.bigger (no queue, no fell) | a raise never queues and never fells | "It never joins the queue and it fells nobody" |
| `tests/seal/model.py:253` Run.bigger (abandon, retry) | a raise that cannot be granted is silent and retried | "a raise that cannot be granted prints nothing and is tried again at the next row grant that leaves the transaction at the limit" |
| `tests/seal/model.py:253` Run.bigger (line) | a granted raise prints `es` | "A raise that is granted prints `es <transaction> <table> <mode>`" |
| `tests/seal/model.py:274` Run.strike | a felled transaction gives up everything and prints `wd` | "gives up every lock it holds, loses the request it was waiting for and the row request that request was carrying" |
| `tests/seal/model.py:290` Run.loose | releases print nothing and free the resource for anyone | "Released rows are free for anyone" |
| `tests/seal/model.py:307` Run.stir | a change puts the entry back among the waiting heads | "Whenever the lock table changes the engine goes back over the resources with a request waiting" |
| `tests/seal/model.py:314` Run.drain (order) | the earliest-begun waiting head goes first | "taking the one whose transaction began earliest first" |
| `tests/seal/model.py:314` Run.drain (restart) | a grant or a felling starts the pass again | "A grant and a felling are both changes, so the pass starts again after either" |
| `tests/seal/model.py:314` Run.drain (no felling) | a waiting head fells nobody | "A request granted this way is granted because no other transaction holds a conflicting mode; it fells nobody" |
| `tests/seal/model.py:335` Run.report (transactions) | every transaction in begin order with its state and its locks | "every transaction prints in begin order `tx <transaction> <state> <resource>:<mode> ...`" |
| `tests/seal/model.py:335` Run.report (queues) | every waiting resource in resource order, entries in queue order | "Then every resource with a request waiting prints `q <resource> <transaction>:<mode> ...` in queue order" |
| `tests/seal/model.py:335` Run.report (count) | the covered count is last and nothing else is printed | "Last is `cov <n>` with the number of requests that took no lock. Nothing else is printed" |
| `tests/seal/model.py:353` expect | a script is its commands in order | "A script is one run of a workload" |

## Readings

Each was implemented as a cheat from the reference and run against the enumerated set and a
shaped generated population (`authoring/lock-cover-wake/cheat_report.py`, 0 findings: every one
is failed by the case named for it).

| Reading | Sentence or published example that rules it out | Case that separates it |
|---|---|---|
| cov-none: every request takes a lock | "A request for a mode the transaction already covers takes no lock and prints nothing" | cov-table |
| cov-own-only: only the resource's own lock covers | "or, for a row, by the lock it holds on that row's table" | cov-table |
| cov-six-x: SIX covers a row in X | "SIX covers IS, IX and S; X covers every mode" | cov-six |
| cov-x-not-s: X does not cover a row in S | "X covers every mode" | cov-own |
| int-now: the row request is made at once | "That table request is made first, and when it cannot be granted at once the row request goes into the queue with it" | int-wait |
| int-keeps: felling leaves the victim's queued request standing | "loses the request it was waiting for and the row request that request was carrying" | int-drop |
| conv-group: a conversion is tested against its own lock | "tested against what the other transactions hold, never against its own" | conv-self |
| conv-fifo: one queue, conversions among the rest | "conversions ahead of new requests and each of the two in the order the requests were made" | conv-behind |
| conv-waits: a conversion waits behind queued new requests | "so it passes queued new requests" | conv-jump |
| new-jump: a new request passes queued new requests | "A new request is granted at once when nothing is queued on that resource" | new-behind |
| fell-raw: every younger conflicting holder is felled | "fells each one it began before the standing of" | fell-shield |
| fell-id: age is the transaction number | "the numbers they are given say nothing about that" | age-beg |
| fell-none: a request that cannot be granted always waits | "Before it settles for waiting, a request that cannot be granted fells" | fell-young |
| fell-held-order: holders are felled in the order the entry holds them | "holding a conflicting mode on that resource in begin order" | fell-order |
| fell-head: a waiting head fells what is in its way | "granted because no other transaction holds a conflicting mode; it fells nobody" | wake-nofell |
| fell-self-shield: the entry asked for counts toward the standing | "other than the one being asked for" | fell-skip |
| wake-entry: each freed entry is drained before the next | "taking the one whose transaction began earliest first" | wake-oldest |
| wake-young: the latest-begun head goes first | "taking the one whose transaction began earliest first" | wake-oldest |
| wake-snap: the waiting heads are listed once and worked through | "A grant and a felling are both changes, so the pass starts again after either" | fell-queued |
| sub-all: a table grant releases every row of that table | "releases the rows of that table that the granted mode covers, and only those" | sub-covered |
| sub-keep: a table grant releases nothing | "A grant of a table lock releases the rows of that table that the granted mode covers" | sub-covered |
| esc-ever: the count is every row lock ever taken | "leaves the transaction holding E or more row locks on that table" | sub-tally |
| esc-counts-cov: covered requests count toward the limit | "A request for a mode the transaction already covers takes no lock and prints nothing" | esc-nocount |
| esc-over: the raise waits for one row past the limit | "E or more row locks on that table" | esc-fires |
| esc-queues: a blocked raise joins the queue | "It never joins the queue and it fells nobody" | esc-drop |
| esc-fells: a blocked raise fells | "It never joins the queue and it fells nobody" | esc-nofell |
| esc-mode-s: the raise always goes to S | "with S when every one of those row locks is S, and with X otherwise" | esc-mode |
| pass-runs: a waiting transaction goes on taking commands | "A command naming a transaction that is waiting is passed over" | pass-wait |
| rep-sorted: a transaction's locks are reported in resource order | "resources are in the order that transaction first took a lock on each of them" | rep-order |
| rep-strings: queues are reported in the string order of the names | "those resources in ascending order with a table ahead of its own rows" | rep-res |
| rep-run: a waiting transaction is reported as running | "`run`, `wait`, `cut` for felled or `done` for committed" | rep-state |

## Shortcuts

| Strategy | Result |
|---|---|
| the shipped tree unchanged (nop) | 0 - the shipped engine differs from the reference on 25 of 38 enumerated scripts and 38 of 40 generated ones |
| constant: one fixed output for every script (`cheat-const-nothing`) | 0 - fails all 38 enumerated scripts and 120 of 120 generated |
| positional: every request granted the moment it is made (`cheat-pos-grant-all`) | 0 - fails 19 of 38 enumerated scripts and 112 of 120 generated |
| the worked example's output replayed (`cheat-forge-hand`, the frozen answers keyed by script) | 0 - passes all 38 enumerated scripts and fails all 120 generated ones, which it could not have seen |

## Tolerances

| Tolerance or limit | Independent implementation | Measured |
|---|---|---|
| `tests/test.sh:35` a 60 s clock on the whole graded set | `authoring/lock-cover-wake/variants/ok-flat` and `ok-lazy`, written apart from the reference, and the sealed model `tests/seal/model.py` | reference 13.4 s for the whole set; ok-flat and ok-lazy within a fifth of it; the three correct-but-slow readings at 400 s, 240 s and 138 s (`authoring/lock-cover-wake/timing.py`) |
| exact comparison, no tolerance | `tests/seal/model.py`, written apart from the reference, decides every generated script and reproduces `gt.json` byte for byte | 0 differences over 106 generated scripts and 400 random ones (`authoring/lock-cover-wake/agree.py`, `authoring/lock-cover-wake/fuzz.py`) |
| the three correct-but-slow readings the clock is there for | `authoring/lock-cover-wake/slow/wake`, `authoring/lock-cover-wake/slow/tally`, `authoring/lock-cover-wake/slow/stand`, each the reference with one computation walked rather than kept | over 400 s, 80 s and 46 s per script against the same scripts the reference does in 0.21 s and 3.6 s |
