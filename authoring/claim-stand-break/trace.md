# Instruction trace: claim-stand-break

Walked from the verifier toward the instruction (docs/INSTRUCTION-CONTRACT.md). Every graded
assertion, every enumerated case, every rule of the sealed model and every condition of
`tests/test.sh` that can turn a run into a 0 has the sentence that tells the agent about it.
Checked with `python tools/tracecheck.py claim-stand-break`.

## Graded assertions

| Verifier site | What it grades | Instruction sentence |
|---|---|---|
| `tests/test_outputs.py` test_frozen_truth_matches_the_model | the sealed model still reproduces the frozen answers; nothing is graded when it does not | "takes a program and prints a line for each thing that happens" |
| `tests/test_outputs.py` test_hand_case | each enumerated program prints exactly the frozen line list, and the program was not altered | "Nothing else is printed" |
| `tests/test_outputs.py` test_every_nonce_program_matches | every generated program prints what the model says, all or nothing | "three hundred and sixty generated smaller ones" |
| `tests/test_outputs.py` test_every_family_is_represented | the generated population was not shrunk before it was run | "The graded set is thirty programs written by hand" |
| `tests/cases.py` case read-base | a read is answered from the rows the transaction opened against, not from the rows now | "A transaction is opened against the rows as they stand at that moment" |
| `tests/cases.py` case read-cover | a read sees the transaction own earlier changes | "under the transaction's own changes that were made before the read and have not been taken back" |
| `tests/cases.py` case read-del | a key the transaction took away reads as absent | "a key it has taken away is not" |
| `tests/cases.py` case span-order | a scan returns rows in key order and stops at the row limit | "returns the first n rows from lo to hi in key order" |
| `tests/cases.py` case span-short | a scan with fewer rows than it asked for returns all of them, and an empty one prints - | "all of them when fewer than n are there" |
| `tests/cases.py` case span-mine | a key the transaction made itself is one of its rows | "A key the transaction has made itself is one of its rows" |
| `tests/cases.py` case span-gone | a key the transaction took away does not use up the row limit | "a key it has taken away is not" |
| `tests/cases.py` case same-value | a rewrite with the value already held leaves a read standing (the everyday case) | "against the rows committed now, would return exactly what it returned" |
| `tests/cases.py` case same-claim | the same rewrite ends a change claim, which is judged by version | "no transaction that committed after this one opened has written its key" |
| `tests/cases.py` case win-past | a commit past the last row of a filled scan leaves it standing (the everyday case) | "it is the keys from lo up to the last row returned" |
| `tests/cases.py` case win-in | a commit inside what a filled scan was drawn from ends it | "it is the keys from lo up to the last row returned" |
| `tests/cases.py` case short-gap | an insert in the gap of a scan that came back short ends it | "for one that came back with fewer it is the whole of lo to hi" |
| `tests/cases.py` case over-after | a change made after a read does not cover that read when it is judged again | "under the transaction's own changes that were made before the read and have not been taken back" |
| `tests/cases.py` case off-cover | a rollback that uncovers a key a scan was answered over ends the scan, with no commit involved | "when a claim is made, after every commit that goes through, and after every rollback" |
| `tests/cases.py` case off-claim | a change the rollback took back claims nothing, so a later commit of that key is harmless | "A change that has been taken back claims nothing" |
| `tests/cases.py` case off-pos | a rollback takes changes back by position, so a key written before the mark keeps that value | "It takes them back by position, not by key" |
| `tests/cases.py` case off-twice | the mark survives its own rollback and can be rolled back to again | "The mark stays and can be rolled back to again" |
| `tests/cases.py` case off-keep | a read made after the mark is not taken back and still ends the transaction later | "Reads are not taken back" |
| `tests/cases.py` case back-again | a value moved and moved back leaves the reader dead from the first commit | "does not start standing again when the rows move back" |
| `tests/cases.py` case late-read | a read at a base the rows have moved past ends the transaction the moment it is made | "Claims are judged three times over" |
| `tests/cases.py` case late-put | a change on a key already written since the base ends the transaction at once | "no transaction that committed after this one opened has written its key" |
| `tests/cases.py` case low-index | one commit breaking two claims reports the lower index, not the one noticed first | "the lowest index among the claims that stopped standing at that moment" |
| `tests/cases.py` case one-dead | only the first break prints, and the seal reports that same index | "once for that transaction and never again" |
| `tests/cases.py` case dead-order | one commit killing three transactions prints them lowest transaction number first | "then the other open transactions are judged, lowest transaction number first" |
| `tests/cases.py` case dead-read | a dead transaction still answers reads, from its own base | "A dead transaction goes on taking ops and answering reads" |
| `tests/cases.py` case dead-none | a dead transaction applies nothing and reports the index it died at | "A dead one applies nothing" |
| `tests/cases.py` case drop-none | a dropped transaction applies nothing and prints nothing | "ends a transaction without applying anything" |
| `tests/cases.py` case apply-last | a commit applies the last standing change of each key and nothing a rollback took back | "the last standing change of each key it holds is applied to the rows" |
| `tests/cases.py` case look-rows | look prints the committed rows of a range in key order, and - for a range holding none | "prints the committed rows of a range" |
| `tests/cases.py` case calm | an ordinary program where nothing breaks: every transaction seals ok (the overcautious side) | "against the rows committed now, would return exactly what it returned" |
| artifact `/app/tx/rows.py` | only this file is collected from the agent for the rows | "The files you may change are" |
| artifact `/app/tx/hold.py` | only this file is collected for what a transaction holds | "The files you may change are" |
| artifact `/app/tx/view.py` | only this file is collected for answering a read | "The files you may change are" |
| artifact `/app/tx/cover.py` | only this file is collected for what a claim covers | "The files you may change are" |
| artifact `/app/tx/watch.py` | only this file is collected for the judging | "The files you may change are" |
| artifact `/app/tx/path.py` | only this file is collected for the op loop | "The files you may change are" |
| `tests/worker.py` pristine overlay | every other file is the verifier own copy, and a new file beside the six is never read | "a new file put beside those six included" |
| `tests/test.sh:35` a 60 s clock | the whole graded set has to run inside the limit; a correct engine that cannot is scored 0 | "all of it has to get through inside 60 seconds" |
| `tests/seal/model.py:63-76` Box.look, Box.moved | the value of a key as of a version, and whether any commit after a base wrote it | "no transaction that committed after this one opened has written its key" |
| `tests/seal/model.py:77-88` Box.apply | a commit stamps every change it carries, whatever value it writes | "whatever value that commit wrote" |
| `tests/seal/model.py:115-132` Act.add_change, Act.undo | claims are numbered in op order and a rollback takes changes back by position | "an op a rollback later takes back keeps its number" |
| `tests/seal/model.py:133-142` Act.cover | the cover of a read is the last change before it that has not been taken back | "under the transaction's own changes that were made before the read and have not been taken back" |
| `tests/seal/model.py:147-170` _value, _answer | what a get and a span return, in key order, up to the row limit | "returns the first n rows from lo to hi in key order" |
| `tests/seal/model.py:171-181` _shifted | standing judged by value for a read and by version for a change, at one key | "A change claim stands while it has not been taken back" |
| `tests/seal/model.py:182-193` _born | the whole test when a claim is made, over the base it was answered from | "Claims are judged three times over" |
| `tests/seal/model.py:194-218` _fell, _moved | the lowest index of the claims that stopped at that moment, reported once | "the lowest index among the claims that stopped standing at that moment" |
| `tests/seal/model.py:219-282` expect, seal branch | a commit applies the last standing change per key, prints, then the others are judged | "then the other open transactions are judged, lowest transaction number first" |
| `tests/seal/model.py:219-282` expect, read branch | a read prints its answer before the line its op may cause | "A read prints its answer before anything else its op causes" |
| `tests/seal/model.py:219-282` expect, quiet ops | put, del, mark, back and drop print nothing of their own | "a rollback and a drop print nothing themselves" |

## Readings

| Reading | Sentence or published example that rules it out | Case that separates it |
|---|---|---|
| `late-check`: claims are only looked at when the transaction seals | "when a claim is made, after every commit that goes through, and after every rollback" | back-again |
| `ver-read`: a read claim is judged by version like a change claim | "against the rows committed now, would return exactly what it returned" | same-value |
| `val-claim`: a change claim is judged by value like a read claim | "whatever value that commit wrote" | same-claim |
| `wide-cover`: a scan covers its whole range even when it filled its row limit | "it is the keys from lo up to the last row returned" | win-past |
| `row-cover`: a scan covers only the rows it returned | "for one that came back with fewer it is the whole of lo to hi" | short-gap |
| `all-cover`: a read is answered under every own change, not only the earlier ones | "under the transaction's own changes that were made before the read and have not been taken back" | over-after |
| `off-key`: a rollback takes back changes by key rather than by position | "It takes them back by position, not by key" | off-pos |
| `off-mark`: the mark is taken away by its own rollback | "The mark stays and can be rolled back to again" | off-twice |
| `off-read`: a rollback takes back the reads made after the mark too | "Reads are not taken back" | off-keep |
| `off-quiet`: nothing is looked at after a rollback | "when a claim is made, after every commit that goes through, and after every rollback" | off-cover |
| `off-claim-on`: a change that was taken back still claims its key | "A change that has been taken back claims nothing" | off-claim |
| `born-quiet`: a claim is not looked at when it is made | "Claims are judged three times over" | late-read |
| `born-read`: only a change is looked at when it is made, never a read | "Claims are judged three times over" | late-read |
| `first-seen`: the first claim noticed is reported rather than the lowest | "the lowest index among the claims that stopped standing at that moment" | low-index |
| `last-dead`: the death index is moved on by every later break | "once for that transaction and never again" | one-dead |
| `open-order`: the other transactions are judged in the order they opened | "then the other open transactions are judged, lowest transaction number first" | dead-order |
| `skip-index`: the ops a rollback took back are not counted in the numbering | "an op a rollback later takes back keeps its number" | off-cover |
| `no-stamp`: writing a key the value it already holds is not a write | "whatever value that commit wrote" | same-claim |
| `seal-apply`: a dead transaction still applies what it changed | "A dead one applies nothing" | dead-none |
| `drop-apply`: a dropped transaction still applies what it changed | "ends a transaction without applying anything" | drop-none |
| `look-gone`: look prints every key that ever held a row | "prints the committed rows of a range" | apply-last |
| `walk-limit`: the row limit counts the keys walked rather than the rows kept | "returns the first n rows from lo to hi in key order" | span-gone |
| `mine-hidden`: a scan does not show the keys the transaction itself made | "A key the transaction has made itself is one of its rows" | span-mine |
| `base-now`: a read is answered from the rows as they stand now | "A transaction is opened against the rows as they stand at that moment" | read-base |

## Shortcuts

| Strategy | Result |
|---|---|
| the shipped tree unchanged (nop) | 0. The shipped engine misses the death in `tiny.txt` and does not get through the two scale programs inside the clock; `cheat/` keeps every one of its readings separately |
| constant: nothing printed at all (`cheat-const-quiet.sh`) | 0, and it matches 0 of 396 programs - every program prints at least one line |
| constant: the most common line of each kind, empty rows and seal ok (`cheat-const-common.sh`) | 0, matching 2 of 396: two generated programs happen to hold nothing and never die |
| positional: every change lands at once and every transaction seals ok (`cheat-pos-apply-now.sh`) | 0, matching 3 of 396 |
| the worked example replayed for every program (`cheat-replay-worked.sh`) | 0, matching 1 of 396 - the worked example itself |
| the frozen answers to the enumerated programs, carried (`cheat-forge-hand.sh`) | 0: it passes all 30 hand cases and fails on the generated population it could not have seen |

## Tolerances

| Tolerance or limit | Independent implementation | Measured |
|---|---|---|
| `tests/test.sh:35` a 60 s clock on the whole graded set | `tests/seal/model.py` and the correct variants `authoring/claim-stand-break/variants/slow-walk`, `authoring/claim-stand-break/variants/slow-over` and `authoring/claim-stand-break/variants/slow-sort`, each written apart from the reference | reference 1.45 s in the verifier container over all 396 programs (41x headroom); the claim-driven variant 4.6 s, the cover-replaying variant 2.4 s, the sort-on-demand variant 0.9 s on the host; the scan-answering reading 362 s, which is what the clock rules out |
