# Instruction trace: row-anchor-pass

Walked from the verifier toward the instruction (docs/INSTRUCTION-CONTRACT.md). Every graded
assertion, enumerated case, model rule, collected artifact and clock below carries the sentence
of `instruction.md` that tells the agent about it. Checked with
`python tools/tracecheck.py row-anchor-pass`.

## Graded assertions

| Verifier site | What it grades | Instruction sentence |
|---|---|---|
| `tests/test_outputs.py:118` test_frozen_truth_matches_the_model | that the sealed model still reproduces the frozen answers, so a drifted model cannot redefine what the hand documents are graded against | "Each frame prints `f <frame> s <offset> g <group> b <band> w <first> <last> h <item> <gap> m <rows> p <passes>`" - the frozen answers are those lines and nothing else |
| `tests/test_outputs.py:128` test_hand_case | every line of every enumerated document, compared exactly | "Each frame prints `f <frame> s <offset> g <group> b <band> w <first> <last> h <item> <gap> m <rows> p <passes>`" and "Nothing else is printed." |
| `tests/test_outputs.py:137` test_every_nonce_program_matches | every line of every generated document, compared exactly | "The graded set is thirty-four documents written by hand, three hundred and fifteen smaller generated ones and three of each of those two shapes" |
| `tests/test_outputs.py:156` test_every_family_is_represented | that the generated population is the whole one the brief describes rather than a shrunken one | "The graded set is thirty-four documents written by hand, three hundred and fifteen smaller generated ones and three of each of those two shapes" |
| `tests/cases.py:18` case band-whole | the band is the whole header when nothing pushes it off | "the band is the smaller of two numbers: the height of the pinned header, and the distance from the offset to the header top of the next group" |
| `tests/cases.py:28` case band-push | the next header shortens the band | "The header of the next group pushes it off from below" |
| `tests/cases.py:39` case band-at-top | a header standing exactly at the offset has pinned | "The pinned group is the last group whose header top is at or before the offset." |
| `tests/cases.py:51` case band-last | the last group measures its push-off against the total | "For the last group the total stands in for that header top." |
| `tests/cases.py:62` case win-edges | both edges of the visible test, on boundary-aligned offsets | "An item is visible when its top is less than the offset plus the viewport height and its bottom is greater than the offset." |
| `tests/cases.py:72` case win-over-both | overscan above the viewport as well as below | "The window runs from K items before the first visible item to K items after the last visible item, clipped to the ends of the flow." |
| `tests/cases.py:81` case win-over-clip | the window clipped at both ends of the flow | "clipped to the ends of the flow" |
| `tests/cases.py:92` case meas-once | a row is measured once and counted once | "A row is as tall as the estimate its group carries until the pane has measured it, and as tall as its real height afterwards." and "`m` counts the rows this frame measured for the first time, over all its passes" |
| `tests/cases.py:102` case meas-over | rows the overscan reaches are measured although off screen | "A pass measures, in item order, every row of its window that has not been measured yet." |
| `tests/cases.py:112` case hold-under-band | the hold is the item across the line, not the first visible one | "The item a frame holds is the one whose top is at or before the anchor line and whose bottom is after it" |
| `tests/cases.py:121` case hold-gap | the sign and origin of the gap | "The gap is the top of that item less the line." |
| `tests/cases.py:130` case hold-end | a line falling on the total holds the last item | "When the line falls on the total it is the last item of the flow." |
| `tests/cases.py:141` case edit-ins-above | an insert above the hold moves the hold's place and not its gap | "The hold is taken next, against the document as it stands before any insert or delete." |
| `tests/cases.py:150` case edit-ins-below | an insert below the hold changes nothing about it | "The hold is taken next, against the document as it stands before any insert or delete." |
| `tests/cases.py:159` case edit-del-above | a delete above the hold leaves the hold itself alone | "The hold is taken next, against the document as it stands before any insert or delete." |
| `tests/cases.py:168` case edit-del-held | the hold walks forward when the delete takes it | "When it removes the held item, the hold becomes the first item that survives after it" |
| `tests/cases.py:179` case edit-del-tail | the hold walks back when nothing survives after it | "or the last item that survives before it when none follows" |
| `tests/cases.py:190` case edit-del-gap | the gap moves by tops taken before the edit | "the gap moves by the difference between the top of the new item and the top of the old one as both stood before the edit" |
| `tests/cases.py:202` case foot-rest | a pane at the foot follows the foot instead of the hold | "It then puts the offset at the foot if the pane is following the foot" |
| `tests/cases.py:211` case foot-leave | one pixel off the foot must not snap back | "The pane is following the foot when the offset that movement left behind is the foot." |
| `tests/cases.py:222` case foot-grow | the foot is re-derived inside the loop from a total the pass moved | "It then puts the offset at the foot if the pane is following the foot" with "A pass works out the band and the window from the offset it begins with and does its measuring." |
| `tests/cases.py:230` case foot-shrink | the foot after a delete shrinks the document | "The foot is the total less the viewport height, or 0 when that would be negative" |
| `tests/cases.py:242` case pass-two | a second pass when the first pass's measuring moves the window | "A frame is settled once a pass has measured nothing and left the offset where it was." |
| `tests/cases.py:250` case pass-cap | the cap stops the frame unsettled | "It stops after P passes however unsettled it is." |
| `tests/cases.py:259` case pass-still | the ordinary frame that must not move at all | "otherwise at the top of the held item, less the gap, less the band that pass worked out, clamped" |
| `tests/cases.py:270` case pass-both-tests | both halves of the settle condition | "A frame is settled once a pass has measured nothing and left the offset where it was" |
| `tests/cases.py:280` case pass-band-moves | the offset is solved against the band that pass worked out | "less the band that pass worked out, clamped" |
| `tests/cases.py:291` case pass-report | the line reports the last pass's band and window | "The group is the id of the pinned group and the band is the band height, both as the last pass worked them out, and the window is the first and last item of the last pass." |
| `tests/cases.py:301` case clamp-foot | the anchored offset is clamped at the foot | "Clamping an offset means holding it at 0 below and at the foot above." |
| `tests/cases.py:309` case clamp-top | the anchored offset is clamped at 0 | "Clamping an offset means holding it at 0 below and at the foot above." |
| `tests/cases.py:319` case size-grow | a taller viewport moves the foot and widens the window | "`size <v>` sets the viewport height to v" |
| `tests/cases.py:328` case size-shrink | a shorter viewport narrows the window and can reach the foot | "`size <v>` sets the viewport height to v" |
| `tests/cases.py:339` case plain-read | an ordinary read down the document and back | "Each frame prints `f <frame> s <offset> g <group> b <band> w <first> <last> h <item> <gap> m <rows> p <passes>`" |
| `tests/cases.py:352` case empty-group | groups with no rows, and a group that loses all of them | "Then come one or more `g <id> <header> <estimate> <low> <high> <rows>` lines, the groups in the order they stand in the document, with distinct ids." |
| artifact `/app/pane/geom.py` | only the declared files are collected | "The files you may change are `/app/pane/geom.py`" and "The rest of the tree is replaced by our own copy before a document is replayed, a new file put beside those six included." |
| artifact `/app/pane/band.py` | only the declared files are collected | "The files you may change are" ... "`/app/pane/band.py`" |
| artifact `/app/pane/win.py` | only the declared files are collected | "The files you may change are" ... "`/app/pane/win.py`" |
| artifact `/app/pane/hold.py` | only the declared files are collected | "The files you may change are" ... "`/app/pane/hold.py`" |
| artifact `/app/pane/move.py` | only the declared files are collected | "The files you may change are" ... "`/app/pane/move.py`" |
| artifact `/app/pane/frame.py` | only the declared files are collected | "The files you may change are" ... "and `/app/pane/frame.py`" |
| `tests/test.sh:35` a 60 s clock | the whole graded set must replay inside 60 seconds | "all of it has to get through inside 60 seconds" |
| `tests/seal/model.py:59-60` Doc.real | a row's real height as an arithmetic function of its id and the bounds of its group | "The real height of a row is `low + (id * 2654435761) % (high - low + 1)`, over the bounds its group declares." |
| `tests/seal/model.py:234` expect | the offset a run starts at, before the first event | "The pane starts at offset 0." |
| `tests/seal/model.py:62-66` Doc.rowh | the estimate stands in until the row has been measured | "A measured row stays measured for the rest of the run." |
| `tests/seal/model.py:45-57` Doc.__init__ | row ids handed out from 0 in creation order | "Row ids are handed out from 0 in the order rows are created" |
| `tests/seal/model.py:68-96` Doc.flatten | the flow is each group's header then its rows, numbered from 0 | "The flow is, group by group, the header of a group and then its rows." and "Items are numbered from 0 across the whole flow and frames from 0." |
| `tests/seal/model.py:68-96` Doc.flatten | a header is as tall as its group declares | "A header is as tall as the height its group declares." |
| `tests/seal/model.py:97-114` Doc.blocks and Doc.bump | the block sums the model adds item heights into, which is where every top and total comes from | "The top of an item is the sum of the heights of the items before it, and the total is the sum of all of them." |
| `tests/seal/model.py:116-129` Doc.count and Doc.total and Doc.top | an item's top is the sum of the heights before it, the total the sum of all | "The top of an item is the sum of the heights of the items before it, and the total is the sum of all of them." |
| `tests/seal/model.py:131-144` Doc.at | the item whose span holds an offset, the last item past the end | "The item a frame holds is the one whose top is at or before the anchor line and whose bottom is after it." |
| `tests/seal/model.py:146-147` Doc.gtop | a group's header top, read off the flow | "The flow is, group by group, the header of a group and then its rows." |
| `tests/seal/model.py:149-153` Doc.key | the printed name of an item | "written as `H` and the id of its group for a header and `R` and its row id for a row" |
| `tests/seal/model.py:155-167` Doc.mark | measuring is once per row and permanent, and counts once | "A row is as tall as the estimate its group carries until the pane has measured it, and as tall as its real height afterwards." and "`m` counts the rows this frame measured for the first time, over all its passes" |
| `tests/seal/model.py:169-173` Doc.gfind | an event names a group by its id | "Then come one or more `g <id> <header> <estimate> <low> <high> <rows>` lines, the groups in the order they stand in the document, with distinct ids." |
| `tests/seal/model.py:175-180` Doc.insert | an insert puts n new rows at that row position | "`ins <group> <at> <n>` puts n new rows into that group at that row position" |
| `tests/seal/model.py:182-187` Doc.remove | a delete takes n rows from that row position | "`del <group> <at> <n>` takes n rows out of that group from that row position" |
| `tests/seal/model.py:190-199` band_of | the pinned group is the last whose header top has reached the offset | "The pinned group is the last group whose header top is at or before the offset." |
| `tests/seal/model.py:200-203` band_of | the band is the header height or the room to the next header, whichever is smaller, with the total standing in for the last group | "the band is the smaller of two numbers: the height of the pinned header, and the distance from the offset to the header top of the next group" and "For the last group the total stands in for that header top." |
| `tests/seal/model.py:205-209` hold_of | the held item is the one across the line and the gap is its top less the line | "The item a frame holds is the one whose top is at or before the anchor line and whose bottom is after it" and "The gap is the top of that item less the line." |
| `tests/seal/model.py:212-217` window_of | the window is the visible run widened by the overscan on both sides and clipped | "The window runs from K items before the first visible item to K items after the last visible item, clipped to the ends of the flow." |
| `tests/seal/model.py:212-217` window_of | the visible run itself, by the strict inequalities at both edges | "An item is visible when its top is less than the offset plus the viewport height and its bottom is greater than the offset." |
| `tests/seal/model.py:220-221` foot_of | the foot is the total less the viewport, floored at 0 | "The foot is the total less the viewport height, or 0 when that would be negative" |
| `tests/seal/model.py:224-226` clamped | clamping holds an offset between 0 and the foot | "Clamping an offset means holding it at 0 below and at the foot above." |
| `tests/seal/model.py:236-243` expect | the event's own movement, then the clamp; an edit moves nothing | "The movement the event asks for comes first" and "the offset is then clamped, while an insert or a delete moves nothing" |
| `tests/seal/model.py:244` expect | the foot flag is read from what the movement left behind | "The pane is following the foot when the offset that movement left behind is the foot." |
| `tests/seal/model.py:246-247` expect | the anchor line is the offset plus the band, and the hold is taken there before any edit | "The anchor line is at the offset plus the band." and "The hold is taken next, against the document as it stands before any insert or delete." |
| `tests/seal/model.py:248-249` expect | the edit is applied after the hold is taken | "Then the edit is applied" |
| `tests/seal/model.py:251-262` expect | a pass lays out from the offset it begins with and measures its window | "A pass works out the band and the window from the offset it begins with and does its measuring." |
| `tests/seal/model.py:263-266` expect | the offset goes to the foot when following it, otherwise to the held item's top less the gap less that pass's band, clamped | "It then puts the offset at the foot if the pane is following the foot, and otherwise at the top of the held item, less the gap, less the band that pass worked out, clamped." |
| `tests/seal/model.py:267-269` expect | settled means a pass measured nothing and left the offset alone; the cap stops it either way | "A frame is settled once a pass has measured nothing and left the offset where it was." |
| `tests/seal/model.py:270-273` expect | the printed fields and which pass each comes from | "The offset is the one the frame ended at." and "The group is the id of the pinned group and the band is the band height, both as the last pass worked them out, and the window is the first and last item of the last pass." |
| `tests/seal/model.py:274` expect | the closing line and its run total | "After the last frame comes `end s <offset> t <total> m <rows>`, where the rows are every row the run measured, whether or not it is still in the document." |
| `tests/seal/model.py:278-289` carry | an insert only shifts the hold's place in the flow | "The hold is taken next, against the document as it stands before any insert or delete." |
| `tests/seal/model.py:290-300` carry | a removed hold walks forward, or back when nothing follows, and the gap moves by tops taken before the edit | "When it removes the held item, the hold becomes the first item that survives after it, or the last item that survives before it when none follows, and the gap moves by the difference between the top of the new item and the top of the old one as both stood before the edit" |
| `tests/seal/model.py:301-304` carry | a delete elsewhere shifts the hold's place and leaves the gap alone | "The hold is taken next, against the document as it stands before any insert or delete." |
| `tests/seal/model.py:306-326` read | the event file grammar the model reads | "The first line of an event file is `cfg V K P`, giving the viewport height, the overscan and the pass cap." |

## Readings

| Reading | Sentence or published example that rules it out | Case that separates it |
|---|---|---|
| hold-first-visible: the hold is the first visible item, measured from the top of the pane | "The item a frame holds is the one whose top is at or before the anchor line and whose bottom is after it" | band-at-top, and the frame the brief prints in full |
| hold-gap-from-top: the right item, but the gap measured from the viewport top | "The gap is the top of that item less the line." | band-at-top |
| hold-gap-sign: the gap is the line less the item's top | "The gap is the top of that item less the line." | band-last |
| hold-end-first: a line on the total holds the first item | "When the line falls on the total it is the last item of the flow." | band-last |
| band-no-push: the pinned header is always shown whole | "The header of the next group pushes it off from below" | band-push |
| band-no-next: push-off measured against the end of the document | "the distance from the offset to the header top of the next group" | band-at-top |
| band-strict: a header exactly at the offset has not pinned yet | "The pinned group is the last group whose header top is at or before the offset." | band-at-top |
| win-bottom-edge: an item starting exactly on the bottom edge is visible | "its top is less than the offset plus the viewport height" | win-edges |
| win-top-edge: an item ending exactly on the top edge is visible | "its bottom is greater than the offset" | win-edges |
| win-over-below: overscan below the viewport only | "from K items before the first visible item to K items after the last visible item" | meas-over |
| win-over-above: overscan above the viewport only | "from K items before the first visible item to K items after the last visible item" | meas-over |
| win-meas-visible: only the visible items are measured | "every row of its window that has not been measured yet" | meas-over |
| meas-counts-window: every rendered row counts as measured | "`m` counts the rows this frame measured for the first time, over all its passes" | band-at-top |
| pass-once: the frame lays out, measures and corrects once | "It stops after P passes however unsettled it is." | pass-two |
| pass-uncapped: the frame settles until it stops moving, cap or no cap | "in at most P passes" | pass-cap |
| pass-offset-only: settled as soon as the offset stops moving | "once a pass has measured nothing and left the offset where it was" | pass-both-tests |
| pass-meas-only: settled as soon as a pass measures nothing | "once a pass has measured nothing and left the offset where it was" | pass-both-tests |
| pass-band-after: the offset solved against a band recomputed after the measuring | "less the band that pass worked out, clamped" | pass-band-moves |
| pass-report-first: the line reports the first pass's band and window | "both as the last pass worked them out, and the window is the first and last item of the last pass" | pass-report |
| pass-report-settled: the line reports a band and window worked out after settling | "both as the last pass worked them out" | pass-report |
| pass-counts-moves: the pass count counts only the passes that changed something | "`p` counts the passes it ran" | band-at-top |
| foot-before-move: the foot read before the event's own movement | "The pane is following the foot when the offset that movement left behind is the foot." | foot-leave |
| foot-never: a pane at the foot is anchored like any other | "It then puts the offset at the foot if the pane is following the foot" | foot-rest |
| foot-once: the foot worked out once and reused by every pass | "It then puts the offset at the foot if the pane is following the foot" applied inside "in at most P passes" | foot-grow |
| clamp-never: the anchored offset is not pulled back into the document | "less the band that pass worked out, clamped" | clamp-foot |
| hold-not-tracked: the hold is left alone while the source changes under it | "When it removes the held item, the hold becomes the first item that survives after it" | edit-del-above |
| hold-ins-index: an insert above the hold leaves its place in the flow where it was | "The hold is taken next, against the document as it stands before any insert or delete." | edit-ins-above |
| hold-back-first: a removed hold falls back to the item before it | "the hold becomes the first item that survives after it, or the last item that survives before it when none follows" | edit-del-gap |
| hold-gap-kept: a removed hold hands its gap to the next item unchanged | "the gap moves by the difference between the top of the new item and the top of the old one as both stood before the edit" | edit-del-gap |

## Shortcuts

| Strategy | Result |
|---|---|
| the shipped tree unchanged (nop) | 0; the shipped pane is wrong on 34 of 34 enumerated documents and does not finish the scale families inside the clock |
| constant: one fixed line for every frame of every document (cheat-const-one-line) | 0; matches 0 of 34 enumerated documents |
| positional: the pane never corrects its offset at all (cheat-pos-never-moves) | 0; matches 0 of 34 enumerated documents |
| the worked example's output replayed, and the frozen answers carried whole (cheat-forge-hand) | 0; passes all 34 enumerated documents and fails on the generated ones, which are drawn after the agent's container is gone |

## Tolerances

| Tolerance or limit | Independent implementation | Measured |
|---|---|---|
| `tests/test.sh:35` a 60 s clock on the whole graded set | `authoring/row-anchor-pass/variants/ok-block` and `authoring/row-anchor-pass/variants/ok-hybrid`, written apart from the reference, and `authoring/row-anchor-pass/naive/geom.py` for the other side | reference 0.40 s and 0.21 s on one wide and one deep document, 0.7% and 0.3% of the limit; both correct variants complete the 34 enumerated and 85 generated documents including all six scale documents in 3.9 s and 2.6 s; the naive flat prefix array takes 325.4 s and 67.4 s on the same two documents, 542% and 112% of the limit on one document each |
