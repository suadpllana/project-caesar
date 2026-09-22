# Instruction trace: anchor-band-settle

Walked from the verifier toward the instruction (docs/INSTRUCTION-CONTRACT.md), on 2026-09-22,
author-run: the session that wrote the model wrote this walk, so the cold-reader half below is
the mechanical form, not a fresh reader. Every quote is word for word from
`tasks/anchor-band-settle/instruction.md`. Checked with `python tools/tracecheck.py anchor-band-settle`.

## Graded assertions

| Verifier site | What it grades | Instruction sentence |
|---|---|---|
| `tests/test_outputs.py:126` test_frozen_truth_matches_the_model | the sealed model reproduces the frozen hand answers before anything is judged; grades nothing the agent wrote, and fails only on a verifier defect | "We grade every line of every program exactly" |
| `tests/test_outputs.py:133` test_program_file_holds_every_family | the root-written program file holds the 39 hand programs and every generated family, at least 300 small ones | "thirty-nine written by hand, and three hundred and ninety smaller ones and three of each large shape generated after you finish" |
| `tests/test_outputs.py:145` test_hand_case | each enumerated program's printed lines equal the frozen answer, and the program the worker ran is the one enumerated | "We grade every line of every program exactly" |
| `tests/test_outputs.py:155` test_every_small_program_matches | every line of every generated small program equals the model's | "three hundred and ninety smaller ones" and "We grade every line of every program exactly" |
| `tests/test_outputs.py:170` test_every_scale_program_matches | every line of the three long and three wide programs equals the model's | "one program of each of two large shapes, about forty thousand boxes and ten thousand frames each" |
| `tests/cases.py:52` case hold-ordinary | content above resolves: the offset moves by exactly the growth, same holder | "the pass asks for that box's top, less its own distance, less the band, clamped" |
| `tests/cases.py:66` case hold-still | a frame with no edits, and one whose edits lie below the view, keep offset and holder | "Asking for the offset it began from ends the frame, held by that box" |
| `tests/cases.py:80` case hold-band | the holder under a stuck header keeps its distance below the band, and keeps it when the header is unpinned and the band falls to 0 | "each of them has a distance: its top less s less the band, taken before the edits" |
| `tests/cases.py:95` case top-held | a view at offset 0 is held like any other | "A view at offset 0 is held like any other." |
| `tests/cases.py:105` case flow-shut | a shut row's children take no space; opening it pushes the holder down | "A lifted box, the children of a shut box and everything inside either are not laid out and take no space." |
| `tests/cases.py:121` case flow-lift | a lifted box takes no space; lifting it pulls the holder up | "A lifted box, the children of a shut box and everything inside either are not laid out and take no space." |
| `tests/cases.py:135` case stick-strict | a stick line exactly on a header's top does not stick it | "is stuck when the lesser of s + T and the end of its section less its height is greater than its top" |
| `tests/cases.py:151` case stick-push | the end of its section pushes a stuck header up, and the band with it | "the lesser of s + T and the end of its section less its height" and "Its section ends where its parent's box ends" |
| `tests/cases.py:168` case stick-none | a header of no height, one under a shut row and one lifted never stick | "a laid-out header of some height is stuck when" |
| `tests/cases.py:185` case band-lowest | overlapping stuck headers: the band is the lowest edge, not a sum | "The band at s is how far below s the lowest bottom edge of a stuck header reaches" |
| `tests/cases.py:200` case band-floor | a header pushed wholly above the view adds nothing | "or 0 when none reaches below s" |
| `tests/cases.py:214` case pick-below | the first box showing under the band is passed over | "The part of the view below the band covers the rows from s plus the band up to s plus the view's height" |
| `tests/cases.py:227` case pick-edges | a box ending on the band line does not show; one starting on it can be whole | "a box with top y and height h covers the rows from y up to y + h, not including y + h" and "a box shows when it covers some row of that part" |
| `tests/cases.py:244` case pick-partial | a partly showing box with nothing inside it is picked, and holds when it grows | "and is picked itself when nothing in it is" |
| `tests/cases.py:254` case pick-first | a partly showing box comes before a wholly showing one after it | "so the first box that shows ends the look" |
| `tests/cases.py:266` case pick-skips | live, lifted and zero-height boxes are passed over | "A box that is lifted, live or of no height, or does not show, is passed over with everything in it." |
| `tests/cases.py:280` case pick-empty | a band as tall as the view leaves nothing to pick | "and is empty when the band is as tall as the view" and "prints `none` at its old offset" |
| `tests/cases.py:291` case fall-dropped | a dropped holder hands over to its container at the container's own distance | "takes the first box of the chain that still qualifies there: in the tree" and "less its own distance" |
| `tests/cases.py:305` case fall-hidden | a holder under a row that was shut hands over to that row | "in the tree, laid out, of some height, and neither stuck nor inside a box that is" |
| `tests/cases.py:318` case fall-lifted | a lifted holder hands over to its container | "in the tree, laid out, of some height, and neither stuck nor inside a box that is" |
| `tests/cases.py:332` case fall-empty | a holder resized to nothing hands over | "in the tree, laid out, of some height, and neither stuck nor inside a box that is" |
| `tests/cases.py:344` case fall-two | holder and container gone: the next box up takes over | "The picked box and the boxes containing it, innermost first, are the chain" |
| `tests/cases.py:359` case fall-none | the whole chain gone: no holder, offset clamped | "If none does, the frame prints `none` at the offset the pass began from." |
| `tests/cases.py:370` case none-late | nothing qualifies at the second pass: the offset that pass began from | "If none does, the frame prints `none` at the offset the pass began from." |
| `tests/cases.py:384` case stuck-inside | a box inside a stuck header cannot hold, nor can the header | "and neither stuck nor inside a box that is" |
| `tests/cases.py:399` case turn-back | the holder sticks at the old offset, its container holds a pass, it returns | "A pass reads the band at the offset it begins from and takes the first box of the chain that still qualifies there" |
| `tests/cases.py:418` case turn-late | the band falls as the view rises, the holder sticks at the fourth pass, the resized section holds, four passes never agree | "After four passes that all moved, the frame takes the smallest offset any of them asked for, held by the box of the first pass that asked for it." |
| `tests/cases.py:432` case settle-cycle | two offsets alternate: the smallest, held by the first pass to reach it | "the frame takes the smallest offset any of them asked for, held by the box of the first pass that asked for it" |
| `tests/cases.py:447` case settle-stick | the old offset unsticks the header, the first pass overshoots to the clamp, it re-sticks and settles | "otherwise the next pass begins at the offset asked for" |
| `tests/cases.py:456` case settle-fourth | three moves and a fourth pass that stands still | "Asking for the offset it began from ends the frame, held by that box" and "After four passes that all moved" |
| `tests/cases.py:470` case settle-drift | a section end moves the band every pass; four passes never agree | "After four passes that all moved, the frame takes the smallest offset any of them asked for" |
| `tests/cases.py:484` case settle-holder | the holder and its container alternate; the smallest offset is the container's | "held by the box of the first pass that asked for it" |
| `tests/cases.py:493` case clamp-pass | a target past the end of the range is clamped before the next pass reads it | "the pass asks for that box's top, less its own distance, less the band, clamped" |
| `tests/cases.py:504` case clamp-start | the first pass begins at the old offset, not the clamped one | "the first beginning at the old offset as it is, clamped or not" |
| `tests/cases.py:517` case off-scroll | an explicit scroll wins; the last one counts, clamped to the tree as the frame leaves it | "the frame prints `off scroll` at the offset of its last `to`" and "every offset a frame prints is clamped into the range of the tree as the frame leaves it" |
| `tests/cases.py:534` case off-live | an edit inside a live box switches holding off for the frame | "A frame with an edit naming a box that is live or inside a live box" |
| `tests/cases.py:548` case off-live-add | adding a live box counts as an edit inside one | "for `add` the new box, prints `off live` at its old offset" |
| `tests/cases.py:560` case off-both | an explicit scroll and a live edit together: the scroll's line | "A frame with both prints `off scroll`." |
| `tests/cases.py:571` case none-before | nothing showing to pick before the edits | "When neither happened and nothing was picked before the edits, the frame prints `none` at its old offset." |
| artifact `/app/view/lay.py` | only the declared files are collected | "You may change `/app/view/lay.py`, `/app/view/stick.py`, `/app/view/pick.py` and `/app/view/hold.py`, and nothing else." |
| artifact `/app/view/stick.py` | only the declared files are collected | "You may change `/app/view/lay.py`, `/app/view/stick.py`, `/app/view/pick.py` and `/app/view/hold.py`, and nothing else." |
| artifact `/app/view/pick.py` | only the declared files are collected | "You may change `/app/view/lay.py`, `/app/view/stick.py`, `/app/view/pick.py` and `/app/view/hold.py`, and nothing else." |
| artifact `/app/view/hold.py` | only the declared files are collected; a new file beside them is not | "The rest of the tree is replaced by our own copy before anything runs, a new file put beside those four included." |
| `tests/test.sh:38` a 90 s clock | the worker, every program included, is killed at 90 seconds and a lost record scores 0 | "The whole set has to get through inside 90 seconds." |
| `tests/worker.py:52` one process, `view.frame.run` | every program runs through the frozen driver, one after another in the worker's process, so module state carries over | "Every graded program goes through `view.frame.run`, one after another in a single process." |
| `environment/app_src/view/frame.py:4-17` the driver | `hold.start` once, then per frame `hold.before`, the edits, `hold.after` returning offset and word | "It calls `hold.start` once. Then, for each frame, it calls `hold.before`, applies the edits, and calls `hold.after`, which returns the offset and the word." |
| `environment/app_src/view/frame.py:16` the line | `<n> <offset> <word>`, n from 1 | "prints a line per frame, `<n> <offset> <word>`: the frame's number counting from 1" |
| `tests/seal/model.py:21` Fen | prefix sums only, no rule; the row order is document order | "its children follow its own height in order" |
| `tests/seal/model.py:73` Node | the fields a box carries: own height, pin, shut, lift, live, children | "the flags are `pin=T`, `shut`, `lift` and `live`" |
| `tests/seal/model.py:92` parse_flags | `pin=T`, `shut`, `lift`, `live` | "the flags are `pin=T`, `shut`, `lift` and `live`" |
| `tests/seal/model.py:109` World | the tree the model keeps; its rules are the rows below | "A program describes a tree of boxes inside one scrolling view and runs frames" |
| `tests/seal/model.py:120-136` World.attach | a declared box is the last child; an add goes at index I among all children | "adds a box as the last child of PARENT, or of the document when PARENT is `-`" and "inserts a new box at index I among all of PARENT's children counting from 0" |
| `tests/seal/model.py:141-151` World.detach | a drop removes the box and everything in it | "`drop ID` removes a box and everything in it" |
| `tests/seal/model.py:169-170` World.refresh heights | own height plus children's unless shut; lifted counts nothing | "A box's height is its own height plus, unless it is shut, the heights of its children that are not lifted" |
| `tests/seal/model.py:180-181` World.span | scroll range | "The scroll range runs from 0 to the document's height less the view's height, or is just 0." |
| `tests/seal/model.py:183-192` World.top | tops in document order, children after the parent's own height | "The document is laid out from 0 downward in whole rows" and "its children follow its own height in order" |
| `tests/seal/model.py:199-204` World.end_of | the section's end: parent's box, or the document | "Its section ends where its parent's box ends, or at the end of the document for a header with no parent." |
| `tests/seal/model.py:206-215` World.shows | laid out: nothing lifted from it up, nothing shut above it | "A lifted box, the children of a shut box and everything inside either are not laid out and take no space." |
| `tests/seal/model.py:217-221` World.stuck | the stuck rule, strict, of some height | "a laid-out header of some height is stuck when the lesser of s + T and the end of its section less its height is greater than its top" |
| `tests/seal/model.py:223-229` World.under_stuck | a box inside a stuck box is disqualified | "neither stuck nor inside a box that is" |
| `tests/seal/model.py:231-259` World.band | lowest bottom edge of a stuck header below s, floored at 0; only laid-out rows are searched | "The band at s is how far below s the lowest bottom edge of a stuck header reaches, or 0 when none reaches below s." |
| `tests/seal/model.py:262-265` World.pick region | the part below the band, empty when the band reaches the view's height | "and is empty when the band is as tall as the view" |
| `tests/seal/model.py:271-279` World.pick skip | lifted, zero-height, live and non-showing boxes passed over with their contents | "A box that is lifted, live or of no height, or does not show, is passed over with everything in it." |
| `tests/seal/model.py:280-281` World.pick whole | a box whose rows all lie in the part is picked | "A box whose rows all lie in that part is picked." |
| `tests/seal/model.py:282-286` World.pick partial | looked into unless shut, picked itself when nothing inside is | "Any other box is looked into, its children in order by the same rule, unless it is shut, and is picked itself when nothing in it is" |
| `tests/seal/model.py:292-297` live_above | live or inside a live box | "an edit naming a box that is live or inside a live box" |
| `tests/seal/model.py:300-315` begin | declarations and `at` | "`at S` gives the offset before the first frame." |
| `tests/seal/model.py:318-345` expect | one line per frame, numbered from 1, each frame starting from the last printed offset | "A frame starts from the offset the frame before it printed, or from `at`." |
| `tests/seal/model.py:349-357` one_frame chain | the pick before the edits, its chain innermost first, distances before the edits | "The picked box and the boxes containing it, innermost first, are the chain, and each of them has a distance: its top less s less the band, taken before the edits." |
| `tests/seal/model.py:361-395` one_frame edits | edits applied in order; `add` checked for live after it is placed, others before | "its edits follow, applied in order" and "for `add` the new box" |
| `tests/seal/model.py:399-400` one_frame fit | clamping | "Clamping an offset moves it into that range" |
| `tests/seal/model.py:402-403` one_frame scroll | off scroll at the last `to`, clamped, first of all | "Two things switch holding off, and they come before everything above." and "at the offset of its last `to`" |
| `tests/seal/model.py:404-405` one_frame live | off live at the old offset, clamped, after scroll | "prints `off live` at its old offset. A frame with both prints `off scroll`." |
| `tests/seal/model.py:406-407` one_frame nothing picked | none at the old offset, clamped | "When neither happened and nothing was picked before the edits, the frame prints `none` at its old offset." |
| `tests/seal/model.py:409-414` one_frame first pass | the first pass begins at the old offset unclamped; each pass reads the band at its own start | "the first beginning at the old offset as it is, clamped or not" and "A pass reads the band at the offset it begins from" |
| `tests/seal/model.py:415-421` one_frame qualify | first qualifying box of the chain, judged at this pass's offset; none: the pass's offset, clamped | "takes the first box of the chain that still qualifies there" and "If none does, the frame prints `none` at the offset the pass began from." |
| `tests/seal/model.py:422-423` one_frame target | top less its own distance less the band, clamped | "Otherwise the pass asks for that box's top, less its own distance, less the band, clamped." |
| `tests/seal/model.py:426-429` one_frame settle | a pass asking for its own start ends the frame; otherwise the next begins where this one asked | "Asking for the offset it began from ends the frame, held by that box; otherwise the next pass begins at the offset asked for." |
| `tests/seal/model.py:412` one_frame cap | four passes at most | "After four passes that all moved" |
| `tests/seal/model.py:430-431` one_frame smallest | the smallest offset, the first pass that asked for it | "the frame takes the smallest offset any of them asked for, held by the box of the first pass that asked for it" |

## Readings

| Reading | Sentence or published example that rules it out | Case that separates it |
|---|---|---|
| dist-view-top | "its top less s less the band, taken before the edits" and "less its own distance, less the band" | settle-cycle, hold-band (frame 2) |
| one-pass | "otherwise the next pass begins at the offset asked for" | settle-stick |
| cap-three | "After four passes that all moved" | settle-fourth |
| cap-five | "After four passes that all moved" | settle-drift |
| last-offset | "the frame takes the smallest offset any of them asked for" | settle-cycle |
| min-last-holder | "held by the box of the first pass that asked for it" | settle-holder |
| clamp-last | "Otherwise the pass asks for that box's top, less its own distance, less the band, clamped." | clamp-pass |
| clamp-first | "the first beginning at the old offset as it is, clamped or not" | clamp-start |
| fresh-pick | "takes the first box of the chain that still qualifies there" | fall-dropped |
| holder-distance | "Otherwise the pass asks for that box's top, less its own distance, less the band, clamped." | fall-dropped |
| eligible-once | "A pass reads the band at the offset it begins from and takes the first box of the chain that still qualifies there" | turn-back |
| pick-after | "Before a frame's edits the view picks the box it is held by, from the tree as it stands" | hold-ordinary |
| none-old-offset | "If none does, the frame prints `none` at the offset the pass began from." | none-late |
| stuck-contents-ok | "and neither stuck nor inside a box that is" | stuck-inside |
| hidden-qualifies | "in the tree, laid out, of some height" and "the children of a shut box and everything inside either are not laid out" | fall-hidden |
| empty-qualifies | "in the tree, laid out, of some height" | fall-empty |
| band-sum | "how far below s the lowest bottom edge of a stuck header reaches" | band-lowest |
| no-push | "the lesser of s + T and the end of its section less its height" | stick-push |
| stick-at-line | "the end of its section less its height is greater than its top" | stick-strict |
| band-no-floor | "or 0 when none reaches below s" | band-floor |
| empty-header-sticks | "a laid-out header of some height is stuck when" | stick-none |
| pick-whole-view | "The part of the view below the band covers the rows from s plus the band"; also the published example, `environment/app_src/progs/small.txt`, whose first line the brief gives as 1 31 b4 | pick-below |
| pick-whole-only | "and is picked itself when nothing in it is" | pick-partial |
| pick-zero | "A box that is lifted, live or of no height, or does not show, is passed over with everything in it." | pick-skips |
| pick-live | "A box that is lifted, live or of no height, or does not show, is passed over with everything in it." | pick-skips |
| pick-at-zero | "A view at offset 0 is held like any other." | top-held |
| live-ignored | "A frame with an edit naming a box that is live or inside a live box" | off-live |
| live-new-ignored | "for `add` the new box, prints `off live` at its old offset" | off-live-add |
| live-first | "A frame with both prints `off scroll`." | off-both |
| scroll-first | "at the offset of its last `to`" | off-scroll |
| pick-touch | "covers the rows from y up to y + h, not including y + h" and "a box shows when it covers some row of that part" | pick-edges |
| pick-straddle | "and is empty when the band is as tall as the view" | pick-empty |
| lifted-qualifies | "in the tree, laid out, of some height" and "A lifted box, the children of a shut box and everything inside either are not laid out and take no space." | fall-lifted |

Readings that survive the published evidence: none. Each reading above contradicts a stated
sentence, and each is failed by the enumerated case named for it (`python3
authoring/anchor-band-settle/readings.py --cases`, all 33 "ok"). Two readings built early were
found unobservable and dropped rather than kept as rules nobody can see: a stuck header can never
show below the band (its laid-out rows end above the band's bottom edge), so skipping it in the
pick is redundant and the brief does not state it; and looking into a shut box only ever finds
children that never qualify, so the view falls back to the shut box at the shut box's own
distance and the result is the correct one.

## Shortcuts

| Strategy | Result |
|---|---|
| the shipped tree unchanged (nop) | scores 0: the worker runs out of the 90 s clock on the scale programs (host trial, 2026-09-22); on the enumerated programs alone it gets 15 of 39 right (`emit_shortcuts.py`, 2026-09-22), so the population, not just the clock, rejects it |
| constant: the most common value of every graded field | scores 0 (`cheat/cheat-const-lines.sh`): prints the most common offset and the most common word, `0 off scroll`, for every frame; matches 0 of 39 enumerated programs (`cheat_report.py`, caught by `test_hand_case`) |
| positional: always the first candidate | scores 0 (`cheat/cheat-pos-first-box.sh`): holds by the first laid-out box of the document at the old offset; matches 1 of 39 enumerated programs (`cheat_report.py`, caught by `test_hand_case`) |
| the worked example's output replayed | scores 0 (`cheat/cheat-replay-small.sh`): replays the four worked-example lines by frame number; matches 0 of 39 enumerated programs, and none of the generated ones (`cheat_report.py`, caught by `test_hand_case`) |
| a forgery carrying the frozen enumerated answers | scores 0 (`cheat/cheat-forge-from-truth.sh`): keys on the declarations and per-frame edits and replays the frozen line; passes all 39 enumerated and 0 of the generated programs, so the post-seed population rejects it (`cheat_report.py`, caught by `test_every_small_program_matches`) |

## Tolerances

| Tolerance or limit | Independent implementation | Measured |
|---|---|---|
| `tests/test.sh:38` a 90 s clock | `tests/seal/model.py`, `authoring/anchor-band-settle/variants/ok-onefile/hold.py`, `authoring/anchor-band-settle/variants/ok-memo/hold.py` | worker over the full graded set (435 programs, 10000-frame scale programs) on this host: reference 5.1 s, ok-onefile 6.7 s, ok-memo 18.7 s, a no-row-cache reading 19.3 s; exact but naive: a full relayout per frame 489 s, a scan of every header per pass 471 s. The slowest correct implementation has 4.8x headroom; the naive families are 5.2x and 5.4x over |
