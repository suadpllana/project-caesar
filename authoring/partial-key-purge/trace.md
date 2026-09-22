# Instruction trace: partial-key-purge

Walked from the verifier toward the instruction (docs/INSTRUCTION-CONTRACT.md). Cite the
instruction word for word in double quotes, four words or more. Write NOT STATED where it
says nothing, then write the sentence or stop grading it. Split each model row into one
row per rule it applies, citing its lines. Check with `python tools/tracecheck.py partial-key-purge`.

Walked 2026-09-22 from `tests/test.sh`, `tests/worker.py`, `tests/test_outputs.py`,
`tests/cases.py` and `tests/seal/model.py`. Every NOT STATED found on the way was fixed in the
instruction before this table was finished: the error-exit sentence was added after the walk
reached `tests/worker.py:49-51`, where a non-zero exit is recorded as a failure whatever the
output was, and the standard-library sentence was reworded when the walk reached
`tests/Dockerfile:8`, because the verifier image does carry pytest.

## Graded assertions

| Verifier site | What it grades | Instruction sentence |
|---|---|---|
| `tests/test_outputs.py:139` test_frozen_truth_matches_the_model | the sealed side agrees with itself (model reproduces gt.json); grades no agent behaviour | "the graded set is three scripts of that size and a little over three hundred small ones" |
| `tests/test_outputs.py:146` test_answers_belong_to_this_nonce | the nonce answers were written for this run's scripts; grades no agent behaviour | "the graded set is three scripts of that size and a little over three hundred small ones" |
| `tests/test_outputs.py:159` test_hand_case | every hand script's standard output equals its frozen answer, line for line | "`/app/run_db.py` takes a script and prints what it did"; "Nothing else may go to standard output" |
| `tests/test_outputs.py:169` test_every_nonce_script_matches | every generated script's output equals the model's, and the population has at least 300 scripts | "a little over three hundred small ones"; "Each runs in a fresh interpreter the way `run_db.py` runs here" |
| `tests/test_outputs.py:188` test_every_family_is_represented | the population has every family and three deep scripts | "the graded set is three scripts of that size" |
| `tests/cases.py:8` case audit-diamond | a row matching three revisions is removed once, under their common root: rev 1 removes 4 | "The counts and the ending are what `delete <table> <id>` of that one row would print" |
| `tests/cases.py:20` case audit-loop | two rows matching each other and an outside row survive its delete in the audit | "So rows that match only one another keep each other" |
| `tests/cases.py:34` case cascade-tree | ordinary simple cascades, a noaction document held while revisions remain | "the delete removes the rows it names and every row that loses a `cascade` reference, and nothing else" |
| `tests/cases.py:51` case clear-no-feedback | a row losing both a setnull and a cascade reference is removed, not cleared | "Clearing never changes what is removed" |
| `tests/cases.py:65` case fork-either | a row with two cascade references goes when either is lost | "every row that loses a `cascade` reference" |
| `tests/cases.py:82` case full-broken-by-clear | clearing one column of a full reference leaves it broken and refuses | "under `full` a row with some of them null but not all is broken" |
| `tests/cases.py:96` case multi-delete | several named rows in one statement, counted once each | "deletes those rows of one table as one statement" |
| `tests/cases.py:108` case mutual-keep | a mutual pair survives its outside support and falls to a delete of either member | "So rows that match only one another keep each other" |
| `tests/cases.py:122` case noaction-removed-anyway | a noaction row removed by the same delete does not refuse it | "That end state is the only place `noaction` is checked" |
| `tests/cases.py:139` case order-decl | the first declared failing reference is named even when its row id is larger | "the failing key or reference declared first in the script" |
| `tests/cases.py:153` case order-row | within one reference, the smallest failing id is named | "then the smallest id among the rows that fail it" |
| `tests/cases.py:166` case partial-all-go | a partial row goes only once every revision it matched is gone | "row loses a reference when it matched at least one row through it and every row it matched is removed" |
| `tests/cases.py:183` case partial-self | a revision based on its own document matches itself and survives | "row that matches itself keeps itself" |
| `tests/cases.py:195` case restrict-removed-anyway | restrict refuses although the orphaned hold is removed by the same delete | "The delete is refused if any row, removed or not, loses a `restrict` reference" |
| `tests/cases.py:212` case restrict-broken-by-clear | clearing a shared column leaves a full restrict reference half-null: refused, naming the restrict reference; a lost restrict row is named likewise | "A row fails a `restrict` reference by losing it, and fails any key or reference by breaking one of the end-state conditions above" |
| `tests/cases.py:231` case self-restrict | a row restricting itself refuses its own delete | "A row can match itself." |
| `tests/cases.py:242` case setnull-all | setnull with no list clears every column and leaves the reference inert | "with none listed it clears them all" |
| `tests/cases.py:253` case setnull-already-null | a row whose cleared column was already null counts as cleared; held counts are printed | "it counts as cleared even if they were null already" |
| `tests/cases.py:268` case setnull-key-column | clearing a key column refuses, naming the key | "holds a null in a column of a key" |
| `tests/cases.py:281` case setnull-list | only the listed column is cleared, and the cleared row still matches | "`setnull` may be followed by the reference columns it clears" |
| `tests/cases.py:294` case setnull-rematch-fails | a cleared partial row that matches no remaining revision refuses | "matches no remaining row through a reference that is not inert for it" |
| `tests/cases.py:308` case simple-null-inert | a simple reference with a null column is inert: never removed, never refused | "under `simple` it is inert for a row with any of them null" |
| `tests/cases.py:322` case tiny | the worked example: the third line is ok 3 0 | "It should be `ok 3 0`: the note on document `a` as a whole matched revisions 1 and 3" |
| `tests/cases.py:342` case two-setnull | two setnull references on one table, clearing overlapping columns | "has that reference's cleared columns set to null" |
| `tests/cases.py:378` case chain-1500 | a simple chain 1500 deep: cascades that recurse per row fail | "Each runs in a fresh interpreter the way `run_db.py` runs here" |
| artifact `/app/db/match.py` | only the declared files are collected | "The files you may change are `/app/db/match.py`, `/app/db/drop.py`, `/app/db/clear.py`, `/app/db/hold.py` and `/app/db/audit.py`" |
| artifact `/app/db/drop.py` | only the declared files are collected | "Everything else under `/app` is put back as shipped before grading" |
| artifact `/app/db/clear.py` | only the declared files are collected | "Everything else under `/app` is put back as shipped before grading" |
| artifact `/app/db/hold.py` | only the declared files are collected | "Everything else under `/app` is put back as shipped before grading" |
| artifact `/app/db/audit.py` | only the declared files are collected; the pristine driver calls `drop.delete` and `audit.audit` | "`run_db.py` will call `drop.delete` and `audit.audit` exactly as it does now" |
| `tests/test.sh:42` a 180 s clock | the whole graded set, one interpreter per script, inside 180 s | "The whole set has to finish inside 180 seconds" |
| `tests/test.sh:41` privilege drop, `tests/Dockerfile:8` image | the submitted code can rely on nothing beyond the standard library: the agent image has none, the verifier image only the grader's pytest pins | "no package outside the Python standard library can be relied on when it runs" |
| `tests/worker.py:49-51` exit status | a run that exits non-zero is a failure whatever it printed | "A run that ends in an error counts as wrong" |
| `tests/worker.py:39-40` output cap | a run whose standard output passes 256 MB is killed and fails; the frozen printer never writes more than a few MB, so only output that is not the driver's can reach it | "Nothing else may go to standard output" |
| `tests/worker.py:52-55` output encoding | output that is not UTF-8 fails; the frozen printer writes ASCII tokens only | "Nothing else may go to standard output" |
| `tests/seal/model.py:29` DB | the script grammar: tables, keys, references with mode, action and clear list, rows, statements | "paired column for column in the order written"; "`setnull` may be followed by the reference columns it clears; with none listed it clears them all" |
| `tests/seal/model.py:78-88` shape | inert when all referencing columns are null, or any under simple; broken under full when some but not all are null | "A reference is inert for a row whose referencing columns are all null"; "under `full` a row with some of them null but not all is broken" |
| `tests/seal/model.py:100-110` Index | a row matches every key row equal to it on its non-null referencing columns, itself included | "Otherwise the row matches every row of the key's table whose key columns equal its non-null referencing columns"; "A row can match itself." |
| `tests/seal/model.py:131-154` attempt | matching reads the store from before the statement; removal grows from the named rows through cascade references | "A delete judges every match on the store as it stood before the delete began" |
| `tests/seal/model.py:145-151` attempt | a pair loses its reference when the count of its surviving matches reaches zero | "row loses a reference when it matched at least one row through it and every row it matched is removed" |
| `tests/seal/model.py:152-154` attempt | only rows that lose a cascade reference are removed, so mutual and self matches never reach zero | "the delete removes the rows it names and every row that loses a `cascade` reference, and nothing else" |
| `tests/seal/model.py:159-162` attempt | any row that lost a restrict reference, removed or not, refuses | "The delete is refused if any row, removed or not, loses a `restrict` reference" |
| `tests/seal/model.py:163-171` attempt | a remaining row that lost a setnull reference has the listed columns nulled and counts as cleared, after the removed set is settled | "A row that is not removed but loses a `setnull` reference has that reference's cleared columns set to null" |
| `tests/seal/model.py:172-182` attempt | rows matching a row whose key was cleared are checked against its new values | "both rows taken with their values after clearing" |
| `tests/seal/model.py:183-205` attempt | end state: broken, no remaining match, null key column | "a remaining row is broken, holds a null in a column of a key, or matches no remaining row through a reference that is not inert for it" |
| `tests/seal/model.py:206-209` attempt | the first declared failing declaration, then its smallest failing id | "then the smallest id among the rows that fail it"; "A row fails a `restrict` reference by losing it" |
| `tests/seal/model.py:213` Tree | audit machinery only: ancestor tests over the ownership tree; grades the audit rule | "The counts and the ending are what `delete <table> <id>` of that one row would print" |
| `tests/seal/model.py:264` dominators | audit machinery only: which rows a lone delete removes | "The counts and the ending are what `delete <table> <id>` of that one row would print" |
| `tests/seal/model.py:319` loops | audit machinery only: loop members are kept by one another against outside deletes | "So rows that match only one another keep each other" |
| `tests/seal/model.py:367-374` audit | one line per row, tables in declaration order, ids ascending | "tables in declaration order, ids ascending within each" |
| `tests/seal/model.py:406-414` audit | rows matching themselves and loop members are kept against outside deletes | "row that matches itself keeps itself" |
| `tests/seal/model.py:487-540` audit | held when the lone delete would be refused; counts given even then | "`held` meaning it would be refused, and the counts are given even then" |
| `tests/seal/model.py:555-564` audit | each row's line is what its lone delete would print; the store is not changed | "An audit changes nothing" |
| `tests/seal/model.py:574-585` expect | ok line with removed (named included) and cleared counts; a refusal changes nothing | "A delete prints `ok <removed> <cleared>`, counting every row it removed, the named ones included, and every row it cleared"; "A refused delete changes nothing" |
| `tests/seal/model.py:576-577` expect | the refusal line | "`refused <name> <id>`: the failing key or reference declared first in the script" |
| `tests/seal/model.py:586-589` expect | dump lines in id order, - for null, nothing for an empty table | "`dump` prints `<table> <id> <value>...` for each row of the table in id order, with `-` for null, and prints nothing for an empty table" |
| `tests/seal/model.py:590-592` expect | audit lines | "`audit` prints `<table> <id> <removed> <cleared> ok`, or the same line ending in `held`, for every row" |

## Readings

| Reading | Sentence or published example that rules it out | Case that separates it |
|---|---|---|
| simple-for-all | "so under `partial` a null column matches anything"; the worked example "It should be `ok 3 0`: the note on document" | audit-diamond |
| full-half-null-accepted | "under `full` a row with some of them null but not all is broken" | full-broken-by-clear |
| row-by-row-clear-feeds-back | "Clearing never changes what is removed" | clear-no-feedback |
| reachability-frees-loops | "So rows that match only one another keep each other" | audit-loop |
| restrict-as-noaction | "The delete is refused if any row, removed or not, loses a `restrict` reference" | restrict-removed-anyway |
| restrict-only-by-losing | "fails any key or reference by breaking one of the end-state conditions above" | restrict-broken-by-clear |
| noaction-as-restrict | "That end state is the only place `noaction` is checked" | noaction-removed-anyway |
| setnull-clears-all | "`setnull` may be followed by the reference columns it clears" | full-broken-by-clear |
| key-null-allowed | "holds a null in a column of a key" | setnull-key-column |
| end-check-before-clearing | "both rows taken with their values after clearing" | setnull-all |
| no-self-match | "A row can match itself." | self-restrict |
| name-by-row-first | "the failing key or reference declared first in the script, then the smallest id among the rows that fail it" | order-decl |
| fork-needs-both | "every row that loses a `cascade` reference" | fork-either |
| named-not-counted | "counting every row it removed, the named ones included" | audit-diamond |
| cleared-only-if-changed | "it counts as cleared even if they were null already" | setnull-already-null |
| held-counts-zero | "`held` meaning it would be refused, and the counts are given even then" | cascade-tree |
| audit-sums-children | "The counts and the ending are what `delete <table> <id>` of that one row would print" | audit-diamond |
| audit-retained-set | "So rows that match only one another keep each other" | audit-loop |

## Shortcuts

| Strategy | Result |
|---|---|
| the shipped tree unchanged (nop) | 0 in the capped Docker trial; matches 4 of 25 hand scripts and 45 of 300 small nonce scripts, and cannot finish the deep family (recursion and a store copy per audited row) |
| constant: the most common value of every graded field | 0; every delete `ok 1 0`, every audit line `1 0 ok`: 0 of 25 hand scripts, 1 of 300 small nonce scripts (`cheat/cheat-constant.sh`) |
| positional: always the first candidate | 0; removing only the named rows matches 1 of 25 and 21 of 300 (`cheat/cheat-named-only.sh`); refusing every delete on the first declared reference and first named id matches 0 of 25 and 1 of 300 (`cheat/cheat-refuse-first.sh`) |
| the worked example's output replayed | 0; answering every delete with the corrected worked-example line `ok 3 0` matches 0 of 25 and 0 of 300 (`cheat/cheat-example-replayed.sh`) |
| the previous revision of the reference | there is none: the reference was written against the frozen contract and has not been revised; the nearest earlier behaviour is the shipped tree, scored above |

## Tolerances

| Tolerance or limit | Independent implementation | Measured |
|---|---|---|
| `tests/test.sh:42` a 180 s clock | `authoring/partial-key-purge/variants/chk/audit.py` (iterative dominators over reverse postorder, Euler-tour LCA, replay below 2000 rows) and the sealed model `tests/seal/model.py`, both written apart from the reference | capped container (1 CPU, 2 GB, Python 3.12), final images: whole graded run 63 s for the chk variant, 48 s for `authoring/partial-key-purge/variants/walk/audit.py` and 39 s for the reference, 2.9x, 3.8x and 4.6x under the clock; the per-row replay audit, correct everywhere, has a floor of 820 s for the three deep scripts on the host when written as tightly as Python allows (`authoring/partial-key-purge/time_naive.py`), 4.5x over |
