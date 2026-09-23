# Instruction trace: partial-key-purge

Walked from the verifier toward the instruction (docs/INSTRUCTION-CONTRACT.md). Cite the
instruction word for word in double quotes, four words or more. Write NOT STATED where it
says nothing, then write the sentence or stop grading it. Split each model row into one
row per rule it applies, citing its lines. Check with `python tools/tracecheck.py partial-key-purge`.

Walked 2026-09-22 from `tests/test.sh`, `tests/worker.py`, `tests/test_outputs.py`,
`tests/cases.py` and `tests/seal/model.py`, and walked again from the top on 2026-09-23 after
the easiness recovery rebuilt the model, the reference and the brief (merge revisions
referenced, rounds and the fifteen-round limit, refusal names in audit lines). Every NOT
STATED found on either walk was fixed in the instruction before its table was finished. The
second walk found three: that a row with two cascade references goes when it loses either
(written as "loses any of its"), what a self-matching merge row does now that "a row that
matches itself keeps itself" is no longer true for it (rewritten as a statement about the
self-matching reference), and which references a row removed too deep fails (a sentence was
added to the list of how rows fail).

## Graded assertions

| Verifier site | What it grades | Instruction sentence |
|---|---|---|
| `tests/test_outputs.py:145` test_frozen_truth_matches_the_model | the sealed side agrees with itself (model reproduces gt.json); grades no agent behaviour | "the graded set is three scripts of that size and nearly four hundred small ones" |
| `tests/test_outputs.py:152` test_answers_belong_to_this_nonce | the nonce answers were written for this run's scripts; grades no agent behaviour | "the graded set is three scripts of that size and nearly four hundred small ones" |
| `tests/test_outputs.py:165` test_hand_case | every hand script's standard output equals its frozen answer, line for line | "`/app/run_db.py` takes a script and prints what it did"; "Nothing else may go to standard output" |
| `tests/test_outputs.py:175` test_every_nonce_script_matches | every generated script's output equals the model's, and the population has at least 300 scripts | "nearly four hundred small ones"; "Each runs in a fresh interpreter the way `run_db.py` runs here" |
| `tests/test_outputs.py:194` test_every_family_is_represented | the population has every family and three deep scripts | "the graded set is three scripts of that size" |
| `tests/cases.py:10` case audit-diamond | a row matching three revisions is removed once, under their common root: rev 1 removes 4 | "The counts and the ending are what `delete <table> <id>` of that one row would print" |
| `tests/cases.py:22` case audit-loop | two rows matching each other and an outside row survive its delete in the audit | "So rows that match only one another keep each other" |
| `tests/cases.py:365` case audit-names | audit lines carry the refusal each lone delete would print, the smallest failing hold id varying by row, counts kept | "or the same counts followed by `refused <name> <id>`, for every row"; "when it would be refused the counts are still those of every row it would remove and clear if it went ahead" |
| `tests/cases.py:36` case cascade-tree | ordinary simple cascades, a noaction document held while revisions remain | "the delete removes the rows it names and every row that loses any of its `cascade` references, and nothing else" |
| `tests/cases.py:53` case clear-no-feedback | a row losing both a setnull and a cascade reference is removed, not cleared | "Clearing never changes what is removed" |
| `tests/cases.py:383` case depth-both-refs | a merge removed in round 16 fails both cascade references it lost; the merged-from one, declared first, names the refusal | "fails a `cascade` reference by losing it when the row goes in round 16 or later"; "the failing key or reference declared first in the script" |
| `tests/cases.py:426` case depth-limit | a cascade of exactly fifteen rounds is accepted and one that reaches round 16 is refused, naming the note removed there | "A delete that would remove a row in round 16 or later is refused"; "The rows the delete names go in round 0" |
| `tests/cases.py:456` case depth-merge-shortcut | a merge shortens a twenty-revision cascade to twelve rounds, so the delete of its root is accepted while its child's is refused | "or the earliest such round when it lost more than one"; "goes one round after the last of the rows it matched through that reference" |
| `tests/cases.py:67` case fork-either | a row with two cascade references goes when either is lost | "every row that loses any of its `cascade` references" |
| `tests/cases.py:84` case full-broken-by-clear | clearing one column of a full reference leaves it broken and refuses | "under `full` a row with some of them null but not all is broken" |
| `tests/cases.py:484` case merge-either | a merge revision, which later revisions are based on, goes with either parent's line | "every row that loses any of its `cascade` references" |
| `tests/cases.py:502` case merge-self | a merge whose merged-from reference matches itself goes when its base is deleted; one with no base keeps itself | "A reference through which a row matches itself is never what removes it" |
| `tests/cases.py:519` case merge-wild-side | a merge from a whole document goes only when every revision of it goes | "row loses a reference when it matched at least one row through it and every row it matched is removed" |
| `tests/cases.py:98` case multi-delete | several named rows in one statement, counted once each | "deletes those rows of one table as one statement" |
| `tests/cases.py:110` case mutual-keep | a mutual pair survives its outside support and falls to a delete of either member | "So rows that match only one another keep each other" |
| `tests/cases.py:124` case noaction-removed-anyway | a noaction row removed by the same delete does not refuse it | "That end state is the only place `noaction` is checked" |
| `tests/cases.py:532` case or-loop-broken | a loop through a merge member unravels when the member's outside parent is deleted, while a loop without one keeps itself | "every row that loses any of its `cascade` references"; "So rows that match only one another keep each other" |
| `tests/cases.py:141` case order-decl | the first declared failing reference is named even when its row id is larger | "the failing key or reference declared first in the script" |
| `tests/cases.py:155` case order-row | within one reference, the smallest failing id is named | "then the smallest id among the rows that fail it" |
| `tests/cases.py:168` case partial-all-go | a partial row goes only once every revision it matched is gone | "row loses a reference when it matched at least one row through it and every row it matched is removed" |
| `tests/cases.py:185` case partial-self | a revision based on its own document matches itself and survives | "A reference through which a row matches itself is never what removes it" |
| `tests/cases.py:197` case restrict-removed-anyway | restrict refuses although the orphaned hold is removed by the same delete | "The delete is refused if any row, removed or not, loses a `restrict` reference" |
| `tests/cases.py:214` case restrict-broken-by-clear | clearing a shared column leaves a full restrict reference half-null: refused, naming the restrict reference; a lost restrict row is named likewise | "A row fails a `restrict` reference by losing it"; "fails any key or reference by breaking one of the end-state conditions above" |
| `tests/cases.py:233` case self-restrict | a row restricting itself refuses its own delete | "A row can match itself." |
| `tests/cases.py:244` case setnull-all | setnull with no list clears every column and leaves the reference inert | "with none listed it clears them all" |
| `tests/cases.py:255` case setnull-already-null | a row whose cleared column was already null counts as cleared; refused lines keep their counts | "It counts as cleared even if they were null already" |
| `tests/cases.py:270` case setnull-key-column | clearing a key column refuses, naming the key | "holds a null in a column of a key" |
| `tests/cases.py:283` case setnull-list | only the listed column is cleared, and the cleared row still matches | "`setnull` may be followed by the reference columns it clears" |
| `tests/cases.py:296` case setnull-rematch-fails | a cleared partial row that matches no remaining revision refuses | "matches no remaining row through a reference that is not inert for it" |
| `tests/cases.py:310` case simple-null-inert | a simple reference with a null column is inert: never removed, never refused | "under `simple` it is inert for a row with any of them null" |
| `tests/cases.py:324` case tiny | the worked example: the third line is ok 3 0 | "It should be `ok 3 0`: the note on document `a` as a whole matched revisions 1 and 3" |
| `tests/cases.py:344` case two-setnull | two setnull references on one table, clearing overlapping columns | "has that reference's cleared columns set to null" |
| `tests/cases.py:561` case chain-1500 | a simple chain 1500 deep: cascades that recurse per row fail, and the deletes are refused past round 15 | "Each runs in a fresh interpreter the way `run_db.py` runs here"; "A delete that would remove a row in round 16 or later is refused" |
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
| `tests/seal/model.py:34` DB | the script grammar: tables, keys, references with mode, action and clear list, rows, statements | "paired column for column in the order written"; "`setnull` may be followed by the reference columns it clears; with none listed it clears them all" |
| `tests/seal/model.py:81-92` shape | inert when all referencing columns are null, or any under simple; broken under full when some but not all are null | "A reference is inert for a row whose referencing columns are all null"; "under `full` a row with some of them null but not all is broken" |
| `tests/seal/model.py:94-131` Index | a row matches every key row equal to it on its non-null referencing columns, itself included | "Otherwise the row matches every row of the key's table whose key columns equal its non-null referencing columns"; "A row can match itself." |
| `tests/seal/model.py:137-168` attempt | matching reads the store from before the statement; removal grows from the named rows, a whole round at a time | "A delete judges every match on the store as it stood before the delete began"; "The rows the delete names go in round 0" |
| `tests/seal/model.py:157-164` attempt | a pair loses its reference when the count of its surviving matches reaches zero | "row loses a reference when it matched at least one row through it and every row it matched is removed" |
| `tests/seal/model.py:165-167` attempt | a row goes in the round after the first of its cascade references to run out, so a row with two goes with either, and loops and self-matches never reach zero on their own | "every row that loses any of its `cascade` references"; "or the earliest such round when it lost more than one"; "A reference through which a row matches itself is never what removes it" |
| `tests/seal/model.py:173-176` attempt | any row that lost a restrict reference, removed or not, refuses | "The delete is refused if any row, removed or not, loses a `restrict` reference" |
| `tests/seal/model.py:134` LIMIT, `tests/seal/model.py:177-178` attempt | a row removed after round fifteen fails every cascade reference it lost | "A delete that would remove a row in round 16 or later is refused, because the real database refuses a cascade that deep"; "fails a `cascade` reference by losing it when the row goes in round 16 or later" |
| `tests/seal/model.py:179-187` attempt | a remaining row that lost a setnull reference has the listed columns nulled and counts as cleared, after the removed set is settled | "A row that is not removed but loses a `setnull` reference has that reference's cleared columns set to null" |
| `tests/seal/model.py:188-198` attempt | rows matching a row whose key was cleared are checked against its new values | "both rows taken with their values after clearing" |
| `tests/seal/model.py:199-221` attempt | end state: broken, no remaining match, null key column | "a remaining row is broken, holds a null in a column of a key, or matches no remaining row through a reference that is not inert for it" |
| `tests/seal/model.py:222-225` attempt | the first declared failing declaration, then its smallest failing id | "then the smallest id among the rows that fail it"; "A row fails a `restrict` reference by losing it" |
| `tests/seal/model.py:229` components | audit machinery only: loops of cascade matches, settled after what they depend on | "So rows that match only one another keep each other" |
| `tests/seal/model.py:273` columns | audit machinery only: counts summed over every row a lone delete removes or clears | "The counts and the ending are what `delete <table> <id>` of that one row would print" |
| `tests/seal/model.py:333-354` audit | the rows each lone delete removes: a row goes with the deleters common to all matches of any one cascade reference; loops grown from each row alone | "every row that loses any of its `cascade` references"; "So rows that match only one another keep each other" |
| `tests/seal/model.py:356-387` audit | the rows each lone delete removes within fifteen rounds, from bounded forward deletes | "A delete that would remove a row in round 16 or later is refused" |
| `tests/seal/model.py:389-399` audit | removed and cleared counts per row, given whether or not the delete would be refused | "when it would be refused the counts are still those of every row it would remove and clear if it went ahead" |
| `tests/seal/model.py:401-449` audit | every way a lone delete can make a row fail: restrict losses, rows removed too deep, and the end state for each set of setnull references that fire | "fails any key or reference by breaking one of the end-state conditions above"; "both rows taken with their values after clearing" |
| `tests/seal/model.py:450-468` audit | each row's refusal is the first failure reaching it in declaration then id order; one line per row, tables in declaration order, ids ascending | "the failing key or reference declared first in the script"; "tables in declaration order, ids ascending within each" |
| `tests/seal/model.py:471-488` expect | ok line with removed (named included) and cleared counts; a refusal changes nothing | "delete prints `ok <removed> <cleared>`, counting every row it removed, the named ones included, and every row it cleared"; "A refused delete changes nothing" |
| `tests/seal/model.py:479-480` expect | the refusal line | "`refused <name> <id>`: the failing key or reference declared first in the script" |
| `tests/seal/model.py:489-492` expect | dump lines in id order, - for null, nothing for an empty table | "`dump` prints `<table> <id> <value>...` for each row of the table in id order, with `-` for null, and prints nothing for an empty table" |
| `tests/seal/model.py:493-496` expect | audit lines, the store unchanged | "`audit` prints `<table> <id> <removed> <cleared> ok`, or the same counts followed by `refused <name> <id>`, for every row"; "An audit changes nothing" |

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
| end-check-before-clearing | "both rows taken with their values after clearing" | restrict-broken-by-clear |
| no-self-match | "A row can match itself." | self-restrict |
| name-by-row-first | "the failing key or reference declared first in the script, then the smallest id among the rows that fail it" | order-decl |
| fork-needs-both | "every row that loses any of its `cascade` references" | merge-either |
| named-not-counted | "counting every row it removed, the named ones included" | audit-diamond |
| cleared-only-if-changed | "It counts as cleared even if they were null already" | setnull-already-null |
| held-counts-zero | "when it would be refused the counts are still those of every row it would remove and clear if it went ahead" | audit-names |
| audit-sums-children | "The counts and the ending are what `delete <table> <id>` of that one row would print" | audit-diamond |
| audit-retained-set | "So rows that match only one another keep each other" | audit-loop |
| descendant-reach | "row loses a reference when it matched at least one row through it and every row it matched is removed" | merge-wild-side |
| loops-always-keep | "every row that loses any of its `cascade` references" | or-loop-broken |
| rounds-longest-path | "or the earliest such round when it lost more than one" | depth-merge-shortcut |
| depth-at-fifteen | "A delete that would remove a row in round 16 or later is refused" | depth-limit |
| no-depth-limit | "the real database refuses a cascade that deep" | depth-limit |
| depth-fails-first-ref-only | "fails a `cascade` reference by losing it when the row goes in round 16 or later" | depth-both-refs |
| tree-audit | "every row that loses any of its `cascade` references"; "The counts and the ending are what `delete <table> <id>` of that one row would print" | merge-either |

## Shortcuts

| Strategy | Result |
|---|---|
| the shipped tree unchanged (nop) | 0; matches 7 of 33 hand scripts and 50 of 360 small nonce scripts, and cannot finish the deep family (recursion and a store copy per audited row) |
| constant: the most common value of every graded field | 0; every delete `ok 1 0`, every audit line `1 0 ok`: 0 of 33 hand scripts, 3 of 360 small nonce scripts (`cheat/cheat-constant.sh`) |
| positional: always the first candidate | 0; removing only the named rows matches 1 of 33 and 24 of 360 (`cheat/cheat-named-only.sh`); refusing every delete on the first declared reference and first named id matches 0 of 33 and 0 of 360 (`cheat/cheat-refuse-first.sh`) |
| the worked example's output replayed | 0; answering every delete with the corrected worked-example line `ok 3 0` matches 0 of 33 and 0 of 360 (`cheat/cheat-example-replayed.sh`) |
| the previous revision of the reference | 0; the reference the easiness probe solved, with its ownership-tree audit, is kept as `cheat/cheat-tree-audit.sh` and fails the hand case merge-either |

## Tolerances

| Tolerance or limit | Independent implementation | Measured |
|---|---|---|
| `tests/test.sh:42` a 180 s clock | `authoring/partial-key-purge/variants/chk/audit.py` (a worklist over the whole store, capped round maps) and `authoring/partial-key-purge/variants/walk/audit.py` (Kosaraju components, bounded forward deletes), written apart from the reference, and the sealed model `tests/seal/model.py` | capped container (1 CPU, 2 GB, Python 3.12): whole graded run 51 s for the reference, 3.5x under the clock; the variants' timings are recorded in STATE.md; the per-row replay audit, correct everywhere, has a floor of 2,402 s for the three deep scripts on the host when written as tightly as Python allows (`authoring/partial-key-purge/time_naive.py`), 13x over |
| `tests/seal/model.py:134` the fifteen-round limit | `authoring/partial-key-purge/brute.py` counts rounds straight from their definition; the chk variant keeps capped round maps and the walk variant runs bounded forward deletes | all agree on 480 generated scripts including the depth family, whose lone deletes run 0 to 40 rounds; the hand case depth-limit fences both sides (fifteen rounds accepted, sixteen refused) |
