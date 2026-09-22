# Instruction trace: page-pass-owe

Walked from the verifier toward the instruction (docs/INSTRUCTION-CONTRACT.md). Cite the
instruction word for word in double quotes, four words or more. Write NOT STATED where it
says nothing, then write the sentence or stop grading it. Split each model row into one
row per rule it applies, citing its lines. Check with `python tools/tracecheck.py page-pass-owe`.

## Graded assertions

| Verifier site | What it grades | Instruction sentence |
|---|---|---|
| `tests/test_outputs.py:133` test_the_model_still_reproduces_the_frozen_answers | that the frozen answers the hand cases are graded against still match the model; nothing the agent wrote | "and thirty-four written by hand" - the hand list files this guards the answers for |
| `tests/test_outputs.py:143` test_hand_list_file | every line of every enumerated list file, in order, against the frozen answers | "Nothing else is printed." |
| `tests/test_outputs.py:150` test_every_generated_list_file | every line of every generated list file, in order, against the sealed model | "The graded set is four hundred list files" |
| `tests/test_outputs.py:166` test_the_population_covers_every_family | that the generated population covers every family; nothing the agent wrote | "three of each of those two sizes, three hundred and sixty smaller ones" |
| `tests/cases.py:19` case order-tie | two rows sharing a key come out smaller id first | "among equal keys a smaller id" |
| `tests/cases.py:29` case order-key | rows come out in ascending key order whatever order they arrived in | "a smaller key comes first" |
| `tests/cases.py:39` case view-tag | a scroll is handed only rows carrying its tag | "A scroll reads the rows carrying its tag as they stand at the moment it looks" |
| `tests/cases.py:52` case led-front | the ledger is drained from the front and stops at an entry that does not fit, not picked over | "the row at the front goes out if its weight is at most the weight left, and otherwise the draining stops there" |
| `tests/cases.py:66` case led-order | the ledger's order is the order rows came to be owed, not their place order | "The ledger holds the rows owed to a scroll in the order they came to be owed." |
| `tests/cases.py:82` case empty-head | a ledger front heavier than a page goes out alone and the page's weight is spent | "a page that has handed out nothing at all takes the row it would otherwise leave behind" |
| `tests/cases.py:95` case empty-scan | the same rule reached by the scan with an empty ledger | "the weight of the page is spent to nothing by doing so" |
| `tests/cases.py:106` case empty-not | a page that has already handed something out steps over a row it cannot fit | "Any other row is stepped over and the scan carries on." |
| `tests/cases.py:120` case step-over | a row too heavy does not end the page; the lighter row behind it is handed out | "Any other row is stepped over and the scan carries on." |
| `tests/cases.py:130` case step-owed | the stepped-over row is what the next page starts from | "the row at the front goes out if its weight is at most the weight left" |
| `tests/cases.py:144` case scan-skip | a row this scroll already has is passed by and the mark still moves past it | "A row this scroll has already been handed is passed by." |
| `tests/cases.py:157` case scan-full | the scan stops at n rows and the mark stops short of the row it never looked at | "The scan stops when the page holds n rows" |
| `tests/cases.py:167` case scan-weight | a row weighing exactly the weight left fits, and the page then ends | "A row whose weight is at most the weight left is handed out." |
| `tests/cases.py:179` case scan-over | two step-overs past the allowance stop the scan with room and weight still in hand | "when the rows it has stepped over in this page weigh c or more" |
| `tests/cases.py:191` case over-exact | step-overs weighing exactly c stop the scan | "when the rows it has stepped over in this page weigh c or more" |
| `tests/cases.py:204` case mark-look | the mark is the last row the scan looked at, not the last it handed out | "The mark moves to the place of every row the scan looks at, whichever of those things happened to it." |
| `tests/cases.py:220` case hold-block | the hold is counted across every scroll, and a full hold stops a scan | "The service holds at most H weight of owed rows across every scroll at once." |
| `tests/cases.py:236` case hold-free | draining one scroll's ledger gives another scroll's scan room to step over | "A scan steps over a row only while the weight already owed plus the weight of that row is at most H" |
| `tests/cases.py:256` case hold-exact | owed weight plus the row's weight coming to exactly H is room enough | "plus the weight of that row is at most H" |
| `tests/cases.py:272` case hold-edit | an edit brings a row to be owed although the hold has no room | "An edit that brings a row to be owed is not held back by it." |
| `tests/cases.py:286` case owe-retire | a move carrying an owed row past the mark takes it out of the ledger | "A row that stops being owed leaves the ledger" |
| `tests/cases.py:299` case owe-return | a row owed a second time goes in at the end, behind what came to be owed meanwhile | "A row that comes to be owed again goes in at the end." |
| `tests/cases.py:314` case owe-add | a row added at a place the scroll has gone past is owed | "its place is at or before the mark of that scroll" |
| `tests/cases.py:326` case owe-after | a row added ahead of the mark is not owed | "its place is at or before the mark of that scroll" |
| `tests/cases.py:339` case owe-drop | dropping an owed row takes it out of the ledger and out of the weight held | "A row that stops being owed leaves the ledger" |
| `tests/cases.py:351` case owe-taken | a row this scroll has been handed is not owed however far back it moves | "that scroll has not been handed it" |
| `tests/cases.py:365` case tag-leave | retagging an owed row away takes it out of that scroll's ledger | "when it carries the tag of that scroll" |
| `tests/cases.py:377` case tag-join | retagging a row in behind the mark brings it to be owed | "A row is owed to a scroll when it carries the tag of that scroll" |
| `tests/cases.py:390` case tag-back | a handed row that leaves the view and comes back is not handed again | "A row handed out to a scroll is never handed to that scroll again, whatever becomes of it afterwards" |
| `tests/cases.py:402` case seen-scroll | two scrolls on one tag are each handed the same rows | "A row handed to one scroll is still handed to another scroll reading the same tag." |
| `tests/cases.py:415` case rep-u | u counts rows of the view not handed out, which is more than the rows owed | "u rows of its view now that it has not been handed" |
| `tests/cases.py:426` case rep-d | d counts rows handed out even after the row is dropped | "d rows handed out to it over the whole run" |
| `tests/cases.py:436` case rep-tot | tot is the owed weight across every scroll, not one of them | "the weight of the rows owed across every scroll" |
| `tests/cases.py:453` case plain-run | with nothing too heavy and no edits every page is a plain run of the view | "A row whose weight is at most the weight left is handed out." |
| artifact `/app/lst/seq.py` | only the declared files are collected | "The files you may change are `/app/lst/seq.py`" |
| artifact `/app/lst/scr.py` | only the declared files are collected | "The files you may change are `/app/lst/seq.py`, `/app/lst/scr.py`, `/app/lst/owe.py`" |
| artifact `/app/lst/owe.py` | only the declared files are collected | "may change are `/app/lst/seq.py`, `/app/lst/scr.py`, `/app/lst/owe.py`, `/app/lst/pg.py`" |
| artifact `/app/lst/pg.py` | only the declared files are collected | "`/app/lst/pg.py`, `/app/lst/edt.py` and `/app/lst/rep.py`" |
| artifact `/app/lst/edt.py` | only the declared files are collected | "`/app/lst/pg.py`, `/app/lst/edt.py` and `/app/lst/rep.py`" |
| artifact `/app/lst/rep.py` | only the declared files are collected | "`/app/lst/pg.py`, `/app/lst/edt.py` and `/app/lst/rep.py`" |
| nothing else is collected | a module placed beside the six is replaced by the verifier's copy | "The rest of the tree is replaced by our own copy before a list file is run, a new file put beside those six included." |
| `tests/test.sh:36` a 60 s clock | the whole graded set must finish inside 60 seconds | "All of it has to get through inside 60 seconds." |
| `tests/seal/model.py:45-52` View.put, `54-67` View.take | a row is in the view of its tag, and an edit moves it between views | "A scroll reads the rows carrying its tag as they stand at the moment it looks" |
| `tests/seal/model.py:69-90` View.walk | the scan reads places in key then id order, strictly after the mark | "the rows of the view whose place is after the mark, in place order" |
| `tests/seal/model.py:78-82` View.walk | a mark whose key no longer holds any row still separates before from after | "The place of a row is its key and then its id" |
| `tests/seal/model.py:92-99` View.members | the closing count is taken over the view as it finally stands | "u rows of its view now that it has not been handed" |
| `tests/seal/model.py:113-120` Led.add | a row entering the ledger goes in at the end | "A row that comes to be owed again goes in at the end." |
| `tests/seal/model.py:122-127` Led.rm | a row that stops being owed leaves the ledger and the weight held | "A row that stops being owed leaves the ledger" |
| `tests/seal/model.py:129-135` Led.front | the ledger is drained from its oldest live entry | "The first half drains the ledger of that scroll, strictly from the front" |
| `tests/seal/model.py:137-138` Led.count | o is the number of rows owed now | "o rows owed to it now" |
| `tests/seal/model.py:142-149` Scroll | a scroll carries its tag, its two limits, its mark, its ledger and what it has been handed | "`open <s> <g> <n> <c>` opens scroll s over tag g, its pages carrying at most n rows and at most c weight" |
| `tests/seal/model.py:147` Scroll.mk | a scroll opens with its mark before every place | "A scroll opens with its mark before every place." |
| `tests/seal/model.py:163-167` Run.owed_now | owed is derived from tag, place against the mark, and the delivery memory | "A row is owed to a scroll when it carries the tag of that scroll, its place is at or before the mark of that scroll, and that scroll has not been handed it." |
| `tests/seal/model.py:169-173` Run.settle | every change to one of those three inputs asks the question again | "A row that stops being owed leaves the ledger. A row that comes to be owed again goes in at the end." |
| `tests/seal/model.py:175-179` Run.standing | the weight held is summed over every scroll | "The service holds at most H weight of owed rows across every scroll at once." |
| `tests/seal/model.py:183-187` Run.add | an added row joins its tag's view and is settled on the scrolls reading that tag | "The edits are `add <id> <k> <g> <w>`, `move <id> <k>`, `tag <id> <g>` and `drop <id>`" |
| `tests/seal/model.py:189-197` Run.move | a move changes the place and settles the row on the scrolls reading its tag | "its place is at or before the mark of that scroll" |
| `tests/seal/model.py:199-210` Run.retag | a retag takes the row out of the old view outright and settles it in the new one | "when it carries the tag of that scroll" |
| `tests/seal/model.py:206-208` Run.retag | leaving a view does not touch the delivery memory | "A row handed out to a scroll is never handed to that scroll again, whatever becomes of it afterwards" |
| `tests/seal/model.py:212-218` Run.drop | a dropped row leaves the view and every ledger | "A row that stops being owed leaves the ledger" |
| `tests/seal/model.py:220-223` Run.open | a scroll reads one tag and is registered against it | "`open <s> <g> <n> <c>` opens scroll s over tag g" |
| `tests/seal/model.py:230` Run.page | a page starts with the scroll's weight limit | "A page carries at most n rows and at most c weight, and both are shared by the two halves of serving it." |
| `tests/seal/model.py:232-236` Run.page | the ledger is drained from the front and stops at an entry that does not fit | "the row at the front goes out if its weight is at most the weight left, and otherwise the draining stops there" |
| `tests/seal/model.py:236` Run.page | a page that has handed out nothing takes the ledger front whatever it weighs | "a page that has handed out nothing at all takes the row it would otherwise leave behind, whatever it weighs" |
| `tests/seal/model.py:241` Run.page | that row spends the page's whole weight | "the weight of the page is spent to nothing by doing so" |
| `tests/seal/model.py:243-245` Run.page | the scan stops on the row limit, the weight left, or the weight stepped over | "The scan stops when the page holds n rows, when its weight is spent, when the rows it has stepped over in this page weigh c or more, or when the view has no further row." |
| `tests/seal/model.py:244` Run.page | the scan reads the view from strictly after the mark, in place order | "a scan over the rows of the view whose place is after the mark, in place order" |
| `tests/seal/model.py:247-249` Run.page | a row already handed to this scroll is passed by, and the mark moves past it | "A row this scroll has already been handed is passed by." |
| `tests/seal/model.py:251-256` Run.page | a row whose weight is at most the weight left is handed out | "A row whose weight is at most the weight left is handed out." |
| `tests/seal/model.py:257-262` Run.page | the empty-page rule again, reached by the scan | "Throughout both halves, a page that has handed out nothing at all takes the row it would otherwise leave behind" |
| `tests/seal/model.py:263-264` Run.page | a full hold stops the scan and leaves the mark short of that row | "the scan stops there, and the mark does not move past that row" |
| `tests/seal/model.py:265-267` Run.page | any other row is stepped over and comes to be owed | "Any other row is stepped over and the scan carries on." |
| `tests/seal/model.py:248,253,259,265` Run.page | the mark is set for every row the scan looks at, and nowhere else | "Draining the ledger never moves the mark." |
| `tests/seal/model.py:269-272` Run.page | a page prints its scroll and the ids in the order they went out | "followed by the ids the page handed out in the order they went out" |
| `tests/seal/model.py:272` Run.page | a page that handed out nothing prints its scroll alone | "and alone when the page handed out nothing" |
| `tests/seal/model.py:280-287` Run.close | the closing report runs in ascending scroll number | "every scroll prints `sc <s> <d> <o> <u>` in ascending scroll number" |
| `tests/seal/model.py:285` Run.close | d is the size of the delivery memory | "d rows handed out to it over the whole run" |
| `tests/seal/model.py:282-285` Run.close | u counts rows of the view now that the scroll has not been handed | "u rows of its view now that it has not been handed" |
| `tests/seal/model.py:286-288` Run.close | tot is the weight owed across every scroll | "Then comes `tot <w>`, the weight of the rows owed across every scroll." |
| `tests/seal/model.py:291-315` run | the list-file grammar and the order operations are applied in | "`row <id> <k> <g> <w>` is a row present before anything runs, with sort key k, tag g and weight w" |
| `tests/seal/model.py:295-297` run | `cfg H` opens the file and sets the hold | "`cfg H` opens the file and sets the hold." |
| `tests/seal/model.py:317-318` expect | a program's trace is its lines in order; nothing else is compared | "Nothing else is printed." |

## Readings

| Reading | Sentence or published example that rules it out | Case that separates it |
|---|---|---|
| order-tie-high | "among equal keys a smaller id" | order-tie |
| led-first-fit | "otherwise the draining stops there" | led-front |
| led-low-id | "in the order they came to be owed" | led-order |
| led-newest | "in the order they came to be owed" | empty-head |
| empty-none | "takes the row it would otherwise leave behind, whatever it weighs and whatever the hold stands at" | empty-head |
| empty-keeps-weight | "the weight of the page is spent to nothing by doing so" | empty-head |
| scan-stop-misfit | "Any other row is stepped over and the scan carries on." | hold-block |
| scan-no-over | "when the rows it has stepped over in this page weigh c or more" | empty-not |
| scan-over-strict | "stepped over in this page weigh c or more" | over-exact |
| scan-fit-strict | "A row whose weight is at most the weight left is handed out." | hold-edit |
| scan-rehands-moved | "A row this scroll has already been handed is passed by." | scan-skip |
| mark-on-give | "The mark moves to the place of every row the scan looks at" | mark-look |
| mark-on-drain | "Draining the ledger never moves the mark." | mark-look |
| hold-per-scroll | "at most H weight of owed rows across every scroll at once" | hold-block |
| hold-strict | "plus the weight of that row is at most H" | hold-exact |
| hold-blocks-edits | "An edit that brings a row to be owed is not held back by it." | hold-edit |
| owe-log | "A row that stops being owed leaves the ledger" | owe-retire |
| owe-ignores-memory | "that scroll has not been handed it" | owe-taken |
| owe-strict-mark | "its place is at or before the mark of that scroll" | owe-return |
| add-always-owes | "its place is at or before the mark of that scroll" | owe-after |
| move-no-settle | "A row that stops being owed leaves the ledger" | owe-retire |
| drop-keeps-owed | "A row that stops being owed leaves the ledger" | owe-drop |
| tag-keeps-owed | "when it carries the tag of that scroll" | tag-leave |
| seen-across-scrolls | "A row handed to one scroll is still handed to another scroll reading the same tag." | hold-block |
| seen-clears-on-tag | "never handed to that scroll again, whatever becomes of it afterwards" | tag-back |
| rep-unhanded-is-owed | "u rows of its view now that it has not been handed" | empty-not |
| rep-handed-in-view | "d rows handed out to it over the whole run" | rep-d |
| rep-total-unhanded | "the weight of the rows owed across every scroll" | empty-not |

| scan-rows-inclusive | "The scan stops when the page holds n rows" | plain-run |
| view-ignores-tag | "A scroll reads the rows carrying its tag as they stand at the moment it looks" | view-tag |
| order-by-id | "a smaller key comes first" | order-key |
| add-never-owes | "its place is at or before the mark of that scroll" | owe-add |
| tag-no-join | "A row is owed to a scroll when it carries the tag of that scroll" | tag-join |
| owe-keeps-place | "A row that comes to be owed again goes in at the end." | owe-return |

## Shortcuts

| Strategy | Result |
|---|---|
| the shipped tree unchanged (nop) | 0. It matches 1 of 366 generated programs and 0 of 34 hand cases; `cheat-nop.sh` |
| constant: every page empty, every scroll `sc <s> 0 0 0`, `tot 0` | 0. `cheat-const-nothing.sh` matches 0 of 34 hand cases |
| positional: every page is the first n rows of the table, in arrival order | 0. `cheat-pos-first-rows.sh` matches 0 of 34 hand cases |
| the worked example's output replayed for every list file | 0. `cheat-const-tiny.sh` matches 1 of 34 hand cases, the one it was copied from |
| the frozen answers for every enumerated list carried in the submission | 0. `cheat-forge-hand.sh` matches all 34 hand cases and 0 of 366 generated |

## Tolerances

| Tolerance or limit | Independent implementation | Measured |
|---|---|---|
| `tests/test.sh:36` a 60 s clock | `authoring/page-pass-owe/variants/stamped/` and `authoring/page-pass-owe/variants/linked/`, both written apart from the reference | stamped 2.5 s and linked 3.4 s over the whole generated set against the 60 s limit; the reference 2.0 s; the naive family that re-derives the view per page 153.9 s and the one that re-sorts a view on every edit 126.7 s |
| exact string comparison, no tolerance | `tests/seal/model.py`, written from the contract with a different view, ledger and owed-weight structure | 0 disagreements with the reference over 366 generated programs and 34 hand cases |
