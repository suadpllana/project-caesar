# Instruction trace: link-clear-round

Walked from the verifier toward the instruction (docs/INSTRUCTION-CONTRACT.md). Every quote is
word for word from `tasks/link-clear-round/instruction.md`. Checked with
`python tools/tracecheck.py link-clear-round`.

## Graded assertions

| Verifier site | What it grades | Instruction sentence |
|---|---|---|
| `tests/test_outputs.py:120` test_frozen_truth_matches_the_model | the sealed model still reproduces the frozen answers; it is the seal on the answers the rows below are compared with, not an assertion about the submission | "Every line is graded" |
| `tests/test_outputs.py:130` test_hand_case | every enumerated program's whole trace, line for line | "Every line is graded" |
| `tests/test_outputs.py:139` test_every_nonce_program_matches | every generated program's whole trace, line for line | "The programs are built after your container is gone, so the four in `/app/progs` are examples and not the exam" |
| `tests/test_outputs.py:158` test_every_family_is_represented | that the generated population was not shrunk; it guards the nonce population against a rewritten `per` | "The programs are built after your container is gone" |
| `tests/cases.py:40` case match-plain | a link takes the rows holding the key, and neither the empty column nor the dangling one | "An empty column holds no key and is never one of them" |
| `tests/cases.py:52` case out-deep-first | a removal prints its groups deepest first | "deepest group first when the change takes a row out" |
| `tests/cases.py:63` case group-longest | a row reached by a short chain and a longer one sits at the longer one | "A row's group is the greatest number of links on any chain by which the change reached that row" |
| `tests/cases.py:75` case group-order-table | inside a group, table declaration order comes before key order | "Inside a group they go by table, in the order the tables are declared" |
| `tests/cases.py:86` case group-order-key | inside one table of one group, key order | "then by the key the row had when the change began" |
| `tests/cases.py:95` case group-order-col | two columns of one row print in column order | "then by the key the row had when the change began, then by column" |
| `tests/cases.py:106` case drop-over-clear | a row taken out prints no clear line for the column another link reached | "A row taken out takes nothing else: a column another link would have written or emptied is left alone" |
| `tests/cases.py:118` case drop-first-link | two links taking one row out: the line names the earlier-declared one | "or both take that row out, the one declared first decides" |
| `tests/cases.py:130` case col-first-link | two links on one column: the earlier-declared one decides, though the other reached it first | "Where two links act on one column of a row" |
| `tests/cases.py:142` case clear-stays | nothing carries on from a row that was only cleared | "Nothing carries on from a row that was only cleared" |
| `tests/cases.py:155` case mov-shallow-first | a re-key prints its groups the other way up | "shallowest group first when it gives one a new key" |
| `tests/cases.py:166` case follow-key-carries | a follow onto a key column re-keys that row and carries on | "where that column is the row's own key the change carries on from that row as well" |
| `tests/cases.py:177` case follow-plain-stops | a follow onto any other column stops there | "`follow` writes the parent row's new key into that column" |
| `tests/cases.py:188` case move-and-clear | a row re-keyed and cleared in one change: both lines name the old key | "Every line names that same key, whatever the row is keyed by when the line is written" |
| `tests/cases.py:200` case kind-picks-action | the same link acts by `goes` for a removal and by `moves` for a re-key | "its `goes` when the change takes a row out and its `moves` when the change gives a row a new key" |
| `tests/cases.py:209` case clash-held | a key another row holds stops a re-key, and nothing is applied | "A key that is already held stops a change that would give a row a key another row of that table holds" |
| `tests/cases.py:216` case clash-noop | a row given the key it already has is not a clash | "a key another row of that table holds" |
| `tests/cases.py:223` case bar-on-removed-row | a restrict fires on a row the change itself would have removed | "That row may well be one this change would itself have taken out" |
| `tests/cases.py:232` case bar-quiet | a restrict link with nothing pointing through it does not fire | "when a row of its child table held, in that column, the key of a row this change carries" |
| `tests/cases.py:241` case bar-pick-first | which restrict is reported: link order, then key | "naming the first such row by the order the links are declared and then by key" |
| `tests/cases.py:253` case bar-nothing-applied | a change stopped by a restrict applies nothing, and the next change sees that | "Nothing else is printed and nothing is applied" |
| `tests/cases.py:267` case wait-after-change | a deferred link is answered from the store the change leaves | "A `wait` link is answered from the store the change leaves behind" |
| `tests/cases.py:275` case wait-child-removed | a row the change removed cannot be the one a deferred link complains about | "It stops the change when a row that is still there holds" |
| `tests/cases.py:284` case wait-dangle-stands | a pointer that was already dangling stops nothing | "a key its parent table held when the change began and does not hold now" |
| `tests/cases.py:293` case wait-pick-first | which deferred hit is reported: link order, then key | "the first such row by the order the links are declared and then by key" |
| `tests/cases.py:305` case wait-undone | a change stopped by a deferred link is walked back, and the next change finds the store as it was | "so that the next change finds the store exactly as this one found it" |
| `tests/cases.py:317` case undo-cols | the walk-back puts emptied columns and moved keys back too | "Rows, emptied columns and moved keys all go back" |
| `tests/cases.py:334` case none-missing | a change naming a key that is not there prints one line and does nothing | "A change naming a key its table does not hold prints `none <table> <key>` and does nothing" |
| `tests/cases.py:341` case ordinary-quiet | a change with nothing to cascade prints only its own line, and no check fires | "A change carries the row it names" |
| artifact `/app/keep/hit.py` | only the declared files are collected | "The files you may change are `/app/keep/hit.py`" |
| artifact `/app/keep/reach.py` | only the declared files are collected | "`/app/keep/hit.py`, `/app/keep/reach.py`, `/app/keep/meld.py`, `/app/keep/halt.py`" |
| artifact `/app/keep/meld.py` | only the declared files are collected | "`/app/keep/reach.py`, `/app/keep/meld.py`, `/app/keep/halt.py`, `/app/keep/lay.py`" |
| artifact `/app/keep/halt.py` | only the declared files are collected | "`/app/keep/meld.py`, `/app/keep/halt.py`, `/app/keep/lay.py` and `/app/keep/undo.py`" |
| artifact `/app/keep/lay.py` | only the declared files are collected | "`/app/keep/halt.py`, `/app/keep/lay.py` and `/app/keep/undo.py`. Nothing else" |
| artifact `/app/keep/undo.py` | only the declared files are collected | "and `/app/keep/undo.py`. Nothing else" |
| `tests/test.sh:35` a 45 s clock | the whole graded set must be through in 45 seconds | "The graded set has to be through inside 45 seconds altogether" |
| `tests/seal/model.py:27-50` _parse | the op set and the column order of a table, the first column being its key | "A `tab` line declares a table and names its columns, the first of which is its key" |
| `tests/seal/model.py:31-35` _parse link line | the field order of a link line and its two actions | "`link <name> <child> <col> <parent> <goes> <moves>`" |
| `tests/seal/model.py:21-25` _val | `-` is an empty column and every other value is a whole number | "its values whole numbers, with `-` for an empty column" |
| `tests/seal/model.py:67-81` Run.put | the store is rows by key; how the lookup beside it is held is an implementation choice and changes no line | "A `put` line adds a row, its values whole numbers" |
| `tests/seal/model.py:83-88` Run.kids | a link matches the child rows whose column holds one of the given keys, empty never | "A link acts on the rows of its child table whose column holds the key of a row the change carries" |
| `tests/seal/model.py:90-102` Run.undo | every slot the change touched goes back to what it held | "so that the next change finds the store exactly as this one found it" |
| `tests/seal/model.py:108-109` _reach seed | the changed row is what the change carries, with its new key for a re-key | "A change carries the row it names" |
| `tests/seal/model.py:124` _reach act | which of the two actions a link uses | "its `goes` when the change takes a row out and its `moves` when the change gives a row a new key" |
| `tests/seal/model.py:125-126` _reach wait skipped | a deferred link does nothing during the reach | "`bar` and `wait` leave the row alone" |
| `tests/seal/model.py:127` _reach match | matching reads the store as it stood when the change began | "A change works out everything it is going to do against the store as it stood when it began" |
| `tests/seal/model.py:128-130` _reach bars | a restrict link records the row rather than acting on it | "A `bar` link stops it when a row of its child table held, in that column, the key of a row this change carries" |
| `tests/seal/model.py:133-134` _reach group | a row's group is the greatest chain length reaching it | "A row's group is the greatest number of links on any chain by which the change reached that row" |
| `tests/seal/model.py:135-137` _reach drop carries | a removed row carries the change on | "`drop` takes the row out, and the change carries on from it" |
| `tests/seal/model.py:138-142` _reach follow on a key | a follow onto a key column carries on, with the earliest link's value | "where that column is the row's own key the change carries on from that row as well" |
| `tests/seal/model.py:151-155` _melt drop | the earliest-declared link names a removal, and a removal wins the row | "or both take that row out, the one declared first decides" |
| `tests/seal/model.py:156-157` _melt column | the earliest-declared link decides a column | "Where two links act on one column of a row, or both take that row out, the one declared first decides" |
| `tests/seal/model.py:158-162` _melt origin | the changed row's own effect, which no link names | "or `-` for the row the change itself names" |
| `tests/seal/model.py:176-178` expect none | a key that is not there | "A change naming a key its table does not hold prints `none <table> <key>` and does nothing" |
| `tests/seal/model.py:180-183` expect bar | the restrict stops the change, reported by link order then key, before anything is applied | "naming the first such row by the order the links are declared and then by key" |
| `tests/seal/model.py:185-195` expect clash | a key already held, the smallest by table order then key, nothing applied | "It prints `clash <table> <key>`, the smallest such key by table order and then by key" |
| `tests/seal/model.py:180-195` expect bar before clash | a restrict is reported ahead of a key already held | "A `bar` is reported ahead of a key that is already held" |
| `tests/seal/model.py:199-200` expect drop line | a removed row prints one line and no column line | "A row taken out prints `drop <table> <key> <link>`" |
| `tests/seal/model.py:204` expect order | group direction by change kind, then table, key and column | "The lines come out group by group, deepest group first when the change takes a row out and shallowest group first when it gives one a new key" |
| `tests/seal/model.py:207-213` expect drop applied | a removed row goes, and the line names the key it began with | "Every line names that same key" |
| `tests/seal/model.py:218-220` expect clear line | an emptied column and its line | "An emptied column prints `clear <table> <key> <column> <link>`" |
| `tests/seal/model.py:222-228` expect move line | a written column, the key column re-keying the row, and its line | "A written column prints `move <table> <key> <column> <value> <link>`" |
| `tests/seal/model.py:229-232` expect lost | only a key the parent table held when the change began and does not hold now | "a key its parent table held when the change began and does not hold now" |
| `tests/seal/model.py:233-241` expect wait | the deferred link, reported by link order then key | "It prints `wait <link> <table> <key>`, the first such row by the order the links are declared and then by key" |
| `tests/seal/model.py:242-244` expect undo | the stopped change is walked back and its lines stand | "The lines a stopped change printed before it stopped stand" |

## Readings

| Reading | Sentence or published example that rules it out | Case that separates it |
|---|---|---|
| applies each effect as it reaches it, so a link reads what the links before it left | "A change works out everything it is going to do against the store as it stood when it began" | col-first-link, bar-on-removed-row |
| gives a row the group it was first reached at | "the greatest number of links on any chain" | group-longest |
| prints every change shallowest group first | "deepest group first when the change takes a row out" | out-deep-first |
| prints every change deepest group first | "shallowest group first when it gives one a new key" | mov-shallow-first |
| orders a group by key before table | "by table, in the order the tables are declared, then by the key" | group-order-table |
| prints the columns of one row last first | "the key the row had when the change began, then by column" | group-order-col |
| lets the link declared last decide a column | "the one declared first decides" | col-first-link |
| lets the link that reached a row first decide its column | "the one declared first decides" | col-first-link |
| names the link declared last on a removal | "or both take that row out, the one declared first decides" | drop-first-link |
| clears a row that another link takes out | "A row taken out takes nothing else" | drop-over-clear |
| carries the change on from a row that was only cleared | "Nothing carries on from a row that was only cleared" | clear-stays |
| carries a follow on from any column | "where that column is the row's own key" | follow-plain-stops |
| never carries a follow on past the changed row | "the change carries on from that row as well" | follow-key-carries |
| uses one action whatever the change is | "its `goes` when the change takes a row out and its `moves` when the change gives a row a new key" | kind-picks-action |
| names the key the row holds when the line is written | "whatever the row is keyed by when the line is written" | move-and-clear |
| runs the restrict check after the removed rows are dropped | "That row may well be one this change would itself have taken out" | bar-on-removed-row |
| reports the last restrict rather than the first | "the first such row by the order the links are declared and then by key" | bar-pick-first |
| does not check a key that is already held | "A key that is already held stops a change" | clash-held |
| calls a re-key onto its own key a clash | "a key another row of that table holds" | clash-noop |
| stops a change on any dangling pointer | "a key its parent table held when the change began and does not hold now" | wait-dangle-stands |
| reports the largest deferred key rather than the smallest | "the first such row by the order the links are declared and then by key" | wait-pick-first |
| leaves a stopped change applied | "the next change finds the store exactly as this one found it" | wait-undone |
| walks back removed rows and nothing else | "Rows, emptied columns and moved keys all go back" | undo-cols |
| prints nothing for a key that is not there | "prints `none <table> <key>` and does nothing" | none-missing |

## Shortcuts

| Strategy | Result |
|---|---|
| the shipped tree unchanged (nop) | 0; matches 8 of 29 enumerated and 1 of 96 generated |
| constant: one fixed output for every program, nothing at all | 0; matches 0 of 29 enumerated and 0 of 96 generated |
| positional: only ever touch the row the change names | 0; matches 10 of 29 enumerated and 23 of 96 generated |
| the worked example replayed: the frozen answers for all 29 enumerated programs | 0; matches 29 of 29 enumerated and 1 of 96 generated |

## Tolerances

| Tolerance or limit | Independent implementation | Measured |
|---|---|---|
| `tests/test.sh:35` a 45 s clock | `authoring/link-clear-round/variants/relax` and `.../sweep`, both written apart from the reference | reference 3.5 s, relax 4.0 s, sweep 4.2 s over the whole graded set of 353 programs; the same reference with the rows found by walking the table 322 s, with only the deferred check walking 179 s |
