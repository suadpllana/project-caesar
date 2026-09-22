# Instruction trace: row-anchor-pass

Walked from the verifier toward the instruction (docs/INSTRUCTION-CONTRACT.md), after the easiness
recovery of 2026-09-22 rebuilt the contract. Every row cites the instruction word for word. The
walk ran author-side: this session wrote the model and the reference, so the cold-reader pass
below is the mechanical form (list every graded output, every decision behind it, the four
clusters put to each), not a fresh session. Check with `python tools/tracecheck.py row-anchor-pass`.

## Graded assertions

| Verifier site | What it grades | Instruction sentence |
|---|---|---|
| `tests/test_outputs.py:127` test_frozen_truth_matches_the_model | the sealed model reproduces gt.json before anything is judged; it grades no submission | "takes an event file and prints a line for each frame" (the model's lines are the format the instruction defines) |
| `tests/test_outputs.py:137` test_hand_case | every enumerated program's printed lines equal gt.json exactly, and the program the worker ran is the one enumerated | "takes an event file and prints a line for each frame"; "Nothing else is printed." |
| `tests/test_outputs.py:146` test_every_nonce_program_matches | every generated program's printed lines equal the model's, all or nothing | "The graded set is fifty-four documents written by hand, three hundred and sixty smaller generated ones and three of each of those three shapes" |
| `tests/test_outputs.py:165` test_every_family_is_represented | the generated set covers every family, so a record missing a family fails | "three hundred and sixty smaller generated ones and three of each of those three shapes" |
| `tests/cases.py:19` case band-whole | the band is the whole header while the next header is far | "The band is the smaller of its header height and the distance from the offset to the next group's header top" |
| `tests/cases.py:29` case band-push | the next header inside the band shortens it | "the distance from the offset to the next group's header top" |
| `tests/cases.py:40` case band-at-top | a header exactly at the offset has pinned | "The pinned group is the last group whose header top is at or before the offset." |
| `tests/cases.py:52` case band-last | the last group is pushed off by the total | "the total standing in for that top after the last group" |
| `tests/cases.py:63` case win-edges | items exactly on the top and bottom edges are not visible | "An item is visible when its top is less than the offset plus V and its bottom is greater than the offset" |
| `tests/cases.py:73` case win-over-both | overscan on both sides of the viewport | "the window runs from K items before the first visible item to K items after the last" |
| `tests/cases.py:82` case win-over-clip | the window is clipped at both ends of the flow | "clipped to the flow" |
| `tests/cases.py:93` case meas-once | a remembered row is not measured again | "measures each row the pane does not remember at the moment it gets there" |
| `tests/cases.py:103` case meas-over | rows reached by the overscan are measured | "It then goes through the window in item order" |
| `tests/cases.py:113` case carry-basic | rows below a measured row take its real height, not E | "Any other row is as tall as the real height of the nearest row above it in the flow that the pane remembers" |
| `tests/cases.py:122` case carry-cross | the borrowed height crosses a group boundary | "in whatever group that row sits, headers not counting" |
| `tests/cases.py:133` case carry-header | a header lends no height | "in whatever group that row sits, headers not counting" |
| `tests/cases.py:142` case carry-empty | an empty group does not stop the carried height | "the nearest row above it in the flow that the pane remembers" |
| `tests/cases.py:155` case carry-est | rows with no remembered row above stay at E | "With no remembered row above it, it is E tall" |
| `tests/cases.py:164` case carry-del-source | deleting the row a run borrows from hands the run to the row above | "A deleted row is forgotten, and an inserted row is not remembered." |
| `tests/cases.py:176` case carry-ins | inserted rows borrow from the remembered row above them | "A deleted row is forgotten, and an inserted row is not remembered." |
| `tests/cases.py:186` case carry-forget | a forgotten row stops lending its height | "it first forgets the one it has seen least recently" |
| `tests/cases.py:200` case mem-big | a memory larger than the document forgets nothing | "The pane remembers at most C rows." |
| `tests/cases.py:210` case mem-seen | the row seen least recently goes, not the oldest measurement | "A row is seen by every pass whose window holds it" |
| `tests/cases.py:223` case mem-tie | a tie goes to the row nearer the start of the flow | "of two rows last seen by the same pass the pane forgets the one nearer the start of the flow" |
| `tests/cases.py:234` case mem-thrash | a window larger than the memory runs the frame to its cap | "it stops after P passes however unsettled it is" |
| `tests/cases.py:243` case mem-sweep-now | a row given up earlier in the same sweep is measured again when reached | "measures each row the pane does not remember at the moment it gets there" |
| `tests/cases.py:252` case mem-del | a deleted row frees its place in the memory | "A deleted row is forgotten, and an inserted row is not remembered." |
| `tests/cases.py:263` case mem-window-first | every row of the window counts as seen from the start of the pass | "every row in that window counts as seen by it from that moment" |
| `tests/cases.py:274` case hold-under-band | the hold is at the anchor line, not the first visible item | "The frame holds the item whose top is at or before the anchor line and whose bottom is after it" |
| `tests/cases.py:284` case hold-gap | the gap is the held item's top less the line | "The gap is the held item's top less the line." |
| `tests/cases.py:294` case hold-end | a line on the total holds the last item | "or the last item when the line is on the total" |
| `tests/cases.py:305` case hold-jump | after a jump the header above is held, not the unremembered row | "it holds instead the nearest item before it in the flow that is a header or a remembered row" |
| `tests/cases.py:314` case hold-near | the nearest holdable item before the line, not after it | "it holds instead the nearest item before it in the flow that is a header or a remembered row" |
| `tests/cases.py:325` case hold-evicted | a forgotten row across the line is not held | "It can only hold what it has laid out, so when that item is a row the pane does not remember" |
| `tests/cases.py:337` case edit-ins-above | an insert above the hold moves it down with its gap | "The hold is taken next, on the document as it stands before any edit." |
| `tests/cases.py:347` case edit-ins-below | an insert below the hold changes nothing about it | "The hold is taken next, on the document as it stands before any edit." |
| `tests/cases.py:357` case edit-del-above | a delete above the hold keeps the hold | "When it removes the held item, the hold becomes the first item that survives after it" |
| `tests/cases.py:367` case edit-del-held | a removed hold moves to the first survivor after it | "the hold becomes the first item that survives after it" |
| `tests/cases.py:379` case edit-del-tail | with no survivor after, the last survivor before | "or the last that survives before it when none follows" |
| `tests/cases.py:391` case edit-del-gap | the gap moves by the difference of the pre-edit tops | "the gap moves by the top of the new item less the top of the old one, both as they stood before the edit" |
| `tests/cases.py:404` case hold-carry-free | a carried hold may be an unremembered row | "which may be a row the pane does not remember" |
| `tests/cases.py:415` case edit-clamp | the offset is clamped after the edit, before any pass | "After an edit the offset is clamped again." |
| `tests/cases.py:427` case foot-rest | resting at the foot, an insert keeps the pane at the foot | "The pane is following the foot when the offset that movement leaves is the foot." |
| `tests/cases.py:436` case foot-leave | one pixel off the foot does not snap back | "The pane is following the foot when the offset that movement leaves is the foot." |
| `tests/cases.py:447` case foot-grow | the foot is taken after each pass's measuring | "After that it puts the offset at the foot if the pane is following the foot" |
| `tests/cases.py:455` case foot-shrink | at the foot while a delete shrinks the document | "After an edit the offset is clamped again." |
| `tests/cases.py:467` case pass-two | a second pass after the first one's measuring moves the window | "The frame then settles, in at most P passes." |
| `tests/cases.py:475` case pass-cap | the cap stops an unsettled frame | "it stops after P passes however unsettled it is" |
| `tests/cases.py:484` case pass-still | a frame over remembered rows settles in one pass where the scroll put it | "A frame is settled once a pass has measured nothing and left the offset where it was" |
| `tests/cases.py:498` case pass-both-tests | both halves of the settle condition | "A frame is settled once a pass has measured nothing and left the offset where it was" |
| `tests/cases.py:510` case pass-band-moves | the offset is solved against the band the pass worked out, not a later one | "less the band that pass worked out, clamped" |
| `tests/cases.py:521` case pass-report | the line carries the last pass's band and window | "The pinned group's id, the band and the window's first and last items are all four as the last pass worked them out" |
| `tests/cases.py:531` case clamp-foot | the solved offset is clamped at the foot | "and otherwise at the held item's top less the gap less the band that pass worked out, clamped" |
| `tests/cases.py:539` case clamp-top | the solved offset is clamped at 0 | "clamping holds an offset between 0 and the foot" |
| `tests/cases.py:549` case size-grow | a taller viewport moves the foot and widens the window | "sets the viewport height to v" |
| `tests/cases.py:558` case size-shrink | a shorter viewport narrows the window | "sets the viewport height to v" |
| `tests/cases.py:569` case plain-read | ordinary reading down and back | "A frame runs in this order." |
| `tests/cases.py:582` case empty-group | a group with no rows and one emptied by a delete | "Then come one or more" |
| artifact `/app/pane/geom.py` | only the declared files are collected | "The files you may change are" |
| artifact `/app/pane/band.py` | only the declared files are collected | "Nothing else is collected: the rest of the tree is replaced by our own copy before a document is replayed" |
| artifact `/app/pane/win.py` | only the declared files are collected | "a new file put beside those six is dropped" |
| artifact `/app/pane/hold.py` | only the declared files are collected | "The files you may change are" |
| artifact `/app/pane/move.py` | only the declared files are collected | "The files you may change are" |
| artifact `/app/pane/frame.py` | only the declared files are collected | "The files you may change are" |
| `tests/test.sh:35` a 120 s clock | the whole graded set runs in one process under a 120 s wall clock | "all of it has to get through inside 120 seconds" |
| `tests/worker.py:59` the worker imports the pane from the pristine tree with the six files laid over it | the pane runs on the verifier's Python with nothing installed | "They run on Python 3.12 with its standard library and nothing else." |
| `tests/seal/model.py:49` Tree | index plumbing for sums over groups; applies no rule of its own | "The top of an item is the sum of the heights before it and the total is the sum of all of them." |
| `tests/seal/model.py:81` walk | the group holding an offset, descending two sums at one carried height | "The top of an item is the sum of the heights before it" |
| `tests/seal/model.py:97` walk_one | the group holding an item index | "Items are numbered from 0 across the flow and frames from 0." |
| `tests/seal/model.py:111` Doc | groups in document order, row ids from 0 in creation order | "Row ids are handed out from 0 in the order rows are created" |
| `tests/seal/model.py:146-148` Doc.real | the real height formula | "The real height of a row is" |
| `tests/seal/model.py:150-157` Doc.row_heights | a remembered row is its real height, any other the last remembered height above, headers skipped | "A header is as tall as its group declares and a row the pane remembers is as tall as its real height." |
| `tests/seal/model.py:159-173` Doc.summarise | rows before a group's first remembered row take the carried height | "in whatever group that row sits, headers not counting" |
| `tests/seal/model.py:214-225` Doc.top_of_group | E before the first remembered row of the flow | "With no remembered row above it, it is E tall" |
| `tests/seal/model.py:227-228` Doc.total | the total | "the total is the sum of all of them" |
| `tests/seal/model.py:265-279` Doc.at | the item holding an offset; past the end, the last item | "or the last item when the line is on the total" |
| `tests/seal/model.py:287-291` Doc.key | H and the group id for a header, R and the row id for a row | "and its group's id for a header" and "and its row id for a row" |
| `tests/seal/model.py:293-299` Doc.forget_one | the row seen least recently, ties to the earlier row | "of two rows last seen by the same pass the pane forgets the one nearer the start of the flow" |
| `tests/seal/model.py:301-308` Doc.sweep, stamping | every remembered row of the window counts as seen by this pass first | "every row in that window counts as seen by it from that moment" |
| `tests/seal/model.py:309-320` Doc.sweep, measuring | in item order, a row not remembered right then is measured, forgetting first when full | "It then goes through the window in item order and measures each row the pane does not remember at the moment it gets there." |
| `tests/seal/model.py:331-335` band_of | pinned group and band | "The pinned group is the last group whose header top is at or before the offset." |
| `tests/seal/model.py:337-345` hold_of | the item across the line, walked back to a header or a remembered row; the gap | "it holds instead the nearest item before it in the flow that is a header or a remembered row" |
| `tests/seal/model.py:349-352` window_of | first and last visible items widened by K, clipped | "the window runs from K items before the first visible item to K items after the last, clipped to the flow" |
| `tests/seal/model.py:357-358` foot_of | the foot | "The foot is the total less V, or 0 when that is negative" |
| `tests/seal/model.py:361-362` clamped | clamping | "clamping holds an offset between 0 and the foot" |
| `tests/seal/model.py:373-380` carry, insert | new rows are fresh ids, not remembered; the hold's index moves past them | "the rows of each" and "as it is replayed" (row ids), "an inserted row is not remembered" |
| `tests/seal/model.py:381-389` carry, removed hold | first survivor after or last before, gap moved by pre-edit tops | "the gap moves by the top of the new item less the top of the old one, both as they stood before the edit" |
| `tests/seal/model.py:390-395` carry, deleted rows | a deleted row is forgotten | "A deleted row is forgotten, and an inserted row is not remembered." |
| `tests/seal/model.py:408-416` expect, movement | scroll, go, size, clamp, then the foot flag from what the movement left | "The pane is following the foot when the offset that movement leaves is the foot." |
| `tests/seal/model.py:418-422` expect, hold then edit then re-clamp | the hold before the edit; clamp after it | "The hold is taken next, on the document as it stands before any edit." and "After an edit the offset is clamped again." |
| `tests/seal/model.py:427-440` expect, the settle loop | band and window from the starting offset, measure, solve or follow the foot, settle test, cap | "After that it puts the offset at the foot if the pane is following the foot, and otherwise at the held item's top less the gap less the band that pass worked out, clamped." |
| `tests/seal/model.py:441-443` expect, the lines | the frame line and the end line, field by field | "the measurements the frame made and the passes it ran" and "where the rows are every measurement of the run" |
| `tests/seal/model.py:449` read | the grammar | "The first line of an event file is" |

## Readings

Every reading below is built by `authoring/row-anchor-pass/emit.py`, measured by
`python tools/readingcheck.py row-anchor-pass` (all 44 separated by the enumerated set) and
scored as a cheat; `authoring/row-anchor-pass/cheat_report.py` asserts the named case catches it.

| Reading | Sentence or published example that rules it out | Case that separates it |
|---|---|---|
| prior-reference: the submitted bundle - fixed estimate, every row kept, any item held, no re-clamp | "Any other row is as tall as the real height of the nearest row above it in the flow that the pane remembers" | carry-basic |
| carry-group: a group's rows borrow only inside the group | "in whatever group that row sits, headers not counting" | carry-cross |
| carry-header: a header lends its height | "in whatever group that row sits, headers not counting" | carry-header |
| carry-empty-reset: an empty group hands on E | "the nearest row above it in the flow that the pane remembers" | carry-empty |
| carry-first-default: rows with nothing remembered above take the first height ever measured | "With no remembered row above it, it is E tall" | carry-est |
| mem-by-measure: forget the row measured longest ago | "A row is seen by every pass whose window holds it" | mem-seen |
| mem-tie-late: a tie forgets the later row | "the pane forgets the one nearer the start of the flow" | mem-tie |
| mem-at-start: a pass measures only what it did not remember when it began | "measures each row the pane does not remember at the moment it gets there" | mem-sweep-now |
| mem-stamp-late: a row counts as seen only when the sweep reaches it | "every row in that window counts as seen by it from that moment" | mem-window-first |
| mem-del-keeps: a deleted row keeps its place in the memory | "A deleted row is forgotten, and an inserted row is not remembered." | mem-del |
| mem-unbounded: nothing is ever forgotten | "The pane remembers at most C rows." | mem-thrash |
| hold-any: any item may be held | "It can only hold what it has laid out, so when that item is a row the pane does not remember" | hold-jump |
| hold-walk-down: fall back to the next holdable item below | "the nearest item before it in the flow that is a header or a remembered row" | hold-near |
| hold-carry-remembered: a carried hold skips unremembered rows | "which may be a row the pane does not remember" | hold-carry-free |
| hold-first-visible: hold the first visible item | "The frame holds the item whose top is at or before the anchor line and whose bottom is after it" | hold-under-band; also the brief's worked frame |
| hold-gap-from-top: the gap from the top of the pane | "The gap is the held item's top less the line." | hold-gap; also the brief's worked frame |
| hold-gap-sign: the gap is the line less the top | "The gap is the held item's top less the line." | hold-gap |
| hold-end-first: a line on the total holds the first item | "or the last item when the line is on the total" | hold-end |
| hold-gap-kept: the gap is not moved when the hold is removed | "the gap moves by the top of the new item less the top of the old one" | edit-del-gap |
| hold-back-first: a removed hold falls back to the item before | "the hold becomes the first item that survives after it" | edit-del-held |
| hold-ins-index: an insert above the hold does not move it | "The hold is taken next, on the document as it stands before any edit." | edit-ins-above |
| hold-not-tracked: the hold is chosen again after the edit | "The hold is taken next, on the document as it stands before any edit." | edit-del-above |
| edit-no-clamp: no clamp after the edit | "After an edit the offset is clamped again." | edit-clamp |
| band-no-push: the pinned header is always whole | "The band is the smaller of its header height and the distance from the offset to the next group's header top" | band-push |
| band-no-next: the last header is never pushed off | "the total standing in for that top after the last group" | band-last |
| band-strict: a header exactly at the offset has not pinned | "whose header top is at or before the offset" | band-at-top |
| win-bottom-edge: an item on the bottom edge is visible | "its top is less than the offset plus V" | win-edges |
| win-top-edge: an item ending on the top edge is visible | "its bottom is greater than the offset" | win-edges |
| win-over-above: overscan above only | "K items after the last" | win-over-both |
| win-over-below: overscan below only | "the window runs from K items before the first visible item" | win-over-both |
| win-meas-visible: only the visible rows are measured | "It then goes through the window in item order" | meas-over |
| meas-counts-window: m counts every rendered item | "the measurements the frame made" | meas-once; also the brief's worked frame |
| foot-before-move: the foot flag read before the movement | "The pane is following the foot when the offset that movement leaves is the foot." | foot-leave |
| foot-never: never follow the foot | "After that it puts the offset at the foot if the pane is following the foot" | foot-rest |
| foot-once: the foot worked out once per frame | "After that it puts the offset at the foot" | foot-grow |
| clamp-never: the solved offset is not clamped | "less the band that pass worked out, clamped" | clamp-foot |
| pass-band-after: solve against the band after measuring | "less the band that pass worked out, clamped" | pass-band-moves |
| pass-counts-moves: p counts only passes that changed something | "the passes it ran" | pass-two; also the brief's worked frame |
| pass-meas-only: settled once nothing was measured | "measured nothing and left the offset where it was" | pass-both-tests |
| pass-offset-only: settled once the offset stood still | "measured nothing and left the offset where it was" | pass-both-tests |
| pass-once: one pass per frame | "The frame then settles, in at most P passes." | pass-two |
| pass-uncapped: the cap is ignored | "it stops after P passes however unsettled it is" | pass-cap |
| pass-report-first: the first pass's band and window are printed | "as the last pass worked them out" | pass-report |
| pass-report-settled: a band and window worked out after settling | "as the last pass worked them out" | pass-cap |

## Shortcuts

| Strategy | Result |
|---|---|
| the shipped tree unchanged (the nop) | reward 0 in the emulated two-stage trial; it is also the reading closest to the prior and fails the worked frame of the brief |
| constant: one fixed line for every frame of every document (cheat-const-one-line) | reward 0; fails all 54 enumerated programs and all 144 sampled generated ones |
| positional: the offset is never corrected, the pane stays where the movement put it (cheat-pos-never-moves) | reward 0; fails 23 of 54 enumerated and 123 of 144 sampled generated programs |
| the worked example's line replayed onto the shipped pane (cheat-replay-example) | reward 0; the shipped pane's other lines are wrong |
| the frozen answers for every enumerated program carried in the pane (cheat-forge-hand) | reward 0; passes all 54 enumerated programs and fails the generated population it could not have seen |
| the previous revision of the reference - the bundle the probe solved (cheat-prior-reference) | reward 0; fails 53 of 54 enumerated and 144 of 144 sampled generated programs |

## Tolerances

| Tolerance or limit | Independent implementation | Measured |
|---|---|---|
| `tests/test.sh:35` a 120 s clock on the whole graded set | `authoring/row-anchor-pass/variants/breaks` and `authoring/row-anchor-pass/variants/blocks`, both written apart from the reference, and the sealed model `tests/seal/model.py` | full graded set of 423 documents: 26.4 s, 37.9 s and 27.1 s against 18.0 s for the reference (seed t2, this machine); the exactly-correct slow repairs in `authoring/row-anchor-pass/slow` are recorded in STATE.md |
| exactness: every line compared string for string, no tolerance | `tests/seal/model.py`, written from the rules with a different decomposition, and `authoring/row-anchor-pass/brute.py` | the reference, the model and the brute-force transcription agree on all 54 enumerated programs and 3000 fuzzed documents; the reference and the model agree on every generated family including the three scale families |
