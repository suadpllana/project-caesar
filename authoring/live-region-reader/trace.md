# Instruction trace: live-region-reader

Walked from the verifier toward the instruction (docs/INSTRUCTION-CONTRACT.md). The sealed model
is the test file here, because every graded line is `assert got == want` against it, so it is
split into one row per rule it applies, with its lines. Checked with
`python tools/tracecheck.py live-region-reader`.

## Graded assertions

| Verifier site | What it grades | Instruction sentence |
|---|---|---|
| `tests/test_outputs.py:124` test_frozen_truth_matches_the_model | the sealed side agrees with itself before judging: the model reproduces every frozen hand answer | the whole contract, printed as "prints what someone using assistive technology would hear" |
| `tests/test_outputs.py:134` test_hand_case | each of the 35 hand pages, line for line against the frozen answer, and the page unaltered | "and 35 written by hand" |
| `tests/test_outputs.py:143` test_every_nonce_program_matches | every generated page, line for line against the model, none altered or missing | "The graded set is three pages like each of those two, 270 smaller ones of at most 120 ticks" |
| `tests/test_outputs.py:162` test_every_family_is_represented | the graded population holds every family, the two large kinds included | "The graded set is three pages like each of those two" |
| `tests/cases.py:45` case tiny-example | the brief's own page: equal words in a second node are spoken again | "it prints two lines where it should print these three" |
| `tests/cases.py:59` case plain-once | spaced-out changes are each spoken once, in order | "Nothing before and words now is an addition, words before and nothing now a removal, and different words a text change." |
| `tests/cases.py:72` case timing-words | an utterance of w words started at t finishes at t + w, and the next starts then | "An utterance of w words started at tick t finishes at tick t + w." |
| `tests/cases.py:83` case tie-node-id | equal ages go to the lower text node id, not to document order | "On equal ages the lower text node id goes first, then the lower region element id." |
| `tests/cases.py:93` case assertive-first | a free reader takes an assertive difference before an older polite one | "the reader takes the oldest unheld waiting difference in an assertive region, or failing that the oldest in a polite region" |
| `tests/cases.py:110` case edit-keeps-age | a waiting difference edited again keeps its age | "It keeps that age for as long as it lasts, whatever happens to its words" |
| `tests/cases.py:127` case stale-in-line | what is spoken is read when the utterance starts, so a later edit is what is heard | "the words the node has if it is exposed in that region now" |
| `tests/cases.py:140` case undone-in-line | an edit undone before its turn is no difference and is never spoken | "Equal words are no difference, however the node moved inside its region." |
| `tests/cases.py:155` case cut-hands-back | a cut polite utterance teaches nothing and its change is spoken again | "The cut utterance teaches nothing. Every pair it carried is compared again against belief" |
| `tests/cases.py:169` case cut-keeps-age | what a cut hands back waits at its old age, ahead of newer polite changes | "a difference found there waits at the age it had when the utterance took it" |
| `tests/cases.py:186` case alert-waits | an assertive difference never cuts assertive speech | "Nothing cuts an assertive utterance." |
| `tests/cases.py:198` case finish-before-cut | an utterance whose tick has come finishes before the cut check | "then the playing utterance finishing if its tick has come, then the comparison, then a cut" |
| `tests/cases.py:212` case held-alert-no-cut | a held assertive difference cuts nothing until released | "an unheld waiting difference in an assertive region cuts it off" |
| `tests/cases.py:229` case late-case | an atomic unit cut by an alert and edited during it is read again with its newest words | "A unit is spoken as the words of every exposed text node inside it" |
| `tests/cases.py:250` case off-stops | an off region nested in a polite one stops the search and is silent | "an off region inside a polite one is a region of its own" |
| `tests/cases.py:264` case off-absorbs | a change made while the region is off is absorbed, not spoken later | "A difference whose region does not voice" |
| `tests/cases.py:277` case hidden-false-stays | aria-hidden false does not expose what a hidden ancestor hides | "exposes nothing that such an element hides" |
| `tests/cases.py:293` case hidden-any-value | the hidden attribute hides with any value, false included | "with any value, or" |
| `tests/cases.py:307` case hide-removes | hiding content is a removal and showing it again an addition | "A node is exposed while it is on the page and no element at or above it carries" |
| `tests/cases.py:320` case region-hidden-silent | removals from a hidden region are absorbed; showing it again voices its words | "A region voices while it is exposed and polite or assertive." |
| `tests/cases.py:336` case relevant-region-only | aria-relevant on an inner element means nothing | "`aria-relevant` anywhere else means nothing." |
| `tests/cases.py:350` case relevant-bogus | unknown tokens only leave the default in force | "missing, or with no token it knows, it means" |
| `tests/cases.py:360` case relevance-absorbs | an irrelevant difference is absorbed, not kept for a later relevance change | "does not name, is absorbed on the spot: the reader believes the current words" |
| `tests/cases.py:376` case atomic-inner | an inner aria-atomic true container is read whole | "makes that element the unit, and" |
| `tests/cases.py:391` case atomic-false-stops | an explicit aria-atomic false stops the walk below an atomic region element | "From the start up to and including the region element, the first element whose" |
| `tests/cases.py:406` case empty-unit | a unit with no exposed words says nothing and the next difference is chosen at once | "If a unit has no exposed words, nothing is said and the utterance counts as finished at once" |
| `tests/cases.py:420` case unit-leaves-held | a unit reads held words but leaves the held difference waiting | "The utterance carries every unheld waiting difference whose unit is that same element." |
| `tests/cases.py:440` case busy-inner | aria-busy on a container holds only the differences beneath it | "A waiting difference is held while an element on its path carries" |
| `tests/cases.py:455` case busy-false-releases | aria-busy false holds nothing | "A waiting difference is held while an element on its path carries" |
| `tests/cases.py:465` case busy-above-ignored | aria-busy above the region element holds nothing | "For an addition or a text change the path runs from the node's parent up to and including its region element." |
| `tests/cases.py:478` case removal-last-believed | a removal is placed under the parent remembered at the last belief, and re-reads that unit | "The start is the node's parent, or for a removal the remembered parent when it is still exposed in the same region" |
| `tests/cases.py:495` case removal-held-anchor | a removal is held by a busy element above its remembered parent | "For a removal it runs from the remembered parent up to and including the region element" |
| `tests/cases.py:511` case anchor-stale-hold | a move inside a region does not refresh the remembered parent | "Each belief also remembers the parent the node had when those words were taken" |
| `tests/cases.py:528` case move-across | a node moved between regions is a removal in one and an addition in the other | "For every region and every text node the reader believes that certain words are there, or that nothing is." |
| `tests/cases.py:541` case absorb-carried | absorbing a carried pair releases it, so finishing teaches nothing stale | "and the playing utterance stops carrying that pair" |
| artifact `/app/sr/look.py` | collected and laid over the pristine tree | "and nothing else. The rest of the tree is replaced by our own copy before a script is run" |
| artifact `/app/sr/know.py` | collected and laid over the pristine tree | "and nothing else. The rest of the tree is replaced by our own copy before a script is run" |
| artifact `/app/sr/watch.py` | collected and laid over the pristine tree | "and nothing else. The rest of the tree is replaced by our own copy before a script is run" |
| artifact `/app/sr/unit.py` | collected and laid over the pristine tree | "and nothing else. The rest of the tree is replaced by our own copy before a script is run" |
| artifact `/app/sr/line.py` | collected and laid over the pristine tree | "and nothing else. The rest of the tree is replaced by our own copy before a script is run" |
| artifact `/app/sr/voice.py` | collected and laid over the pristine tree; its Reader is the entry point | "After all of each later tick's operations it calls" |
| `tests/worker.py:40` the pristine overlay | nothing outside the six files changes what a page prints, a new file beside them included | "A file you add beside those six is not used" |
| `tests/test.sh:33` a 60 s clock | the whole graded set, the large pages included, has to be read inside it or the run scores 0 | "All of it has to be read within 60 seconds on one CPU." |
| `tests/seal/model.py:59-87` parse | the script grammar: page T, rising ticks from @0, the seven operations, end and child positions | "lines open the ticks in rising order" and "moves a node together with everything under it" |
| `tests/seal/model.py:322-387` apply | operations applied in order; a move counted after the node is taken out; dropped nodes gone for good | "counted once the node has been taken out" and "removes one for good" |
| `tests/seal/model.py:379-381` apply, aria-live switched | a region keeps its element but its value may change after the load; voicing, loudness and absorption follow the current value | "a later tick may switch it between those three, but never sets it on another element or unsets it" |
| `tests/seal/model.py:127-143` refresh, exposure | hidden with any value or aria-hidden true on the node or above hides it; aria-hidden false never re-exposes | "A node is exposed while it is on the page and no element at or above it carries" |
| `tests/seal/model.py:127-143` refresh, region | the nearest element at or above with aria-live, off included | "The region of a node is the nearest element at or above it that carries" |
| `tests/seal/model.py:158-159` voices | a region voices while exposed and polite or assertive | "A region voices while it is exposed and polite or assertive." |
| `tests/seal/model.py:161-168` relevant | tokens additions, removals, text, all; others ignored; default additions text; the region element's own attribute | "separated by spaces, and ignores any other token; missing, or with no token it knows, it means" |
| `tests/seal/model.py:414-419` load | belief is exactly what is exposed at the end of the load, with each node's parent; nothing is spoken for it | "At the end of the load it believes exactly what is exposed. It says nothing about the load." |
| `tests/seal/model.py:181-184` expect | a difference is measured against the playing utterance's carried value where it carries the pair, else belief | "which is what that utterance carries for the pair if it carries it and the belief otherwise" |
| `tests/seal/model.py:152-156` cur | the current value of a pair: the node's words and parent when exposed in that region now | "the words the node has if it is exposed in that region now" |
| `tests/seal/model.py:90-101` differs, kind | presence and words only; addition, removal, text change; equal words are none | "Nothing before and words now is an addition, words before and nothing now a removal, and different words a text change." |
| `tests/seal/model.py:302-306` settle, absorption | silent or irrelevant differences: belief takes the current value and the playing utterance stops carrying the pair | "does not name, is absorbed on the spot: the reader believes the current words, and the playing utterance stops carrying that pair" |
| `tests/seal/model.py:307-309` settle, age | a new difference gets the tick; a persisting one keeps its age | "and its age is the tick at whose end it was found." |
| `tests/seal/model.py:247-254` start | the node's parent, or for a removal the remembered parent while exposed in the same region, else none | "The start is the node's parent, or for a removal the remembered parent when it is still exposed in the same region; otherwise the removal has no start." |
| `tests/seal/model.py:256-265` is_held | aria-busy true from the start up to and including the region element, or the region element alone | "For a removal it runs from the remembered parent up to and including the region element when that parent is still exposed in the same region, and is the region element alone otherwise." |
| `tests/seal/model.py:239-243` top | oldest first; ties to the lower text node id then the lower region element id | "On equal ages the lower text node id goes first, then the lower region element id." |
| `tests/seal/model.py:440` tick, the class order | assertive before polite whenever the reader chooses | "or failing that the oldest in a polite region" |
| `tests/seal/model.py:267-278` unit | the first explicit aria-atomic from the start up to and including the region element decides | "reaching the region element without either, or having no start means there is no unit" |
| `tests/seal/model.py:280-291` text_of | a unit's words: every exposed text node inside it in document order, one space between | "in document order (depth first, an element before its children, children in order), one space between" |
| `tests/seal/model.py:448-457` tick, unit carry | a unit utterance carries every unheld difference whose unit is that element | "The utterance carries every unheld waiting difference whose unit is that same element." |
| `tests/seal/model.py:445-447` tick, no unit | the node's words, or removed and the believed words, carrying one difference | "followed by the believed words, and carries that one difference" |
| `tests/seal/model.py:458-460` tick, carried | a carried difference no longer waits; its carried value is the node's current words and parent | "A carried difference no longer waits." |
| `tests/seal/model.py:461-464` tick, empty unit | an empty unit is believed at once and the reader chooses again in the same tick | "the reader believes what it carried and chooses again" |
| `tests/seal/model.py:465-470` tick, start | politeness is the region's when the utterance starts; finish at t + w; the start line | "It is polite or assertive as its region was when it started." |
| `tests/seal/model.py:425-429` tick, finish | a finishing utterance teaches its carried values | "Belief changes in only two ways: an utterance finishes and the reader believes what it carried, or a difference is absorbed." |
| `tests/seal/model.py:431-438` tick, cut | a polite utterance cut by an unheld assertive difference; carried pairs compared again at their carried age; the cut line | "While a polite utterance is playing, an unheld waiting difference in an assertive region cuts it off" |
| `tests/seal/model.py:421-470` tick, the order | operations, finish, comparison, cut, choosing while nothing plays | "A tick runs in this order: its operations, then the playing utterance finishing if its tick has come, then the comparison, then a cut, then choosing as often as nothing is playing." |
| `tests/seal/model.py:473-481` expect | ticks 1 to T whether named or not; one log per page; nothing else printed | "Ticks run from 1 to T whether or not a script names them." |
| `tests/seal/model.py:470` tick, the log line | the exact start line and cut line, in the order they happen | "for each cut, in the order they happen, and nothing else" |

## Readings

Every reading below is written as a whole reader by `authoring/live-region-reader/readings.py`,
measured by `python tools/readingcheck.py live-region-reader` and emitted as a cheat by
`authoring/live-region-reader/emit.py`.

| Reading | Sentence or published example that rules it out | Case that separates it |
|---|---|---|
| event-driven: the shipped reader, mutation records turned into queued strings | "it prints two lines where it should print these three" | tiny-example, assertive-first |
| learn-at-start: the listener learns a change when its utterance starts | "Belief changes in only two ways: an utterance finishes and the reader believes what it carried" | cut-hands-back |
| queue-strings: everything pending gathered into a queue of strings when free | "the words the node has if it is exposed in that region now" | stale-in-line |
| atomic-region-only: aria-atomic read on the region element alone | "From the start up to and including the region element, the first element whose" | late-case, atomic-inner |
| atomic-false-ignored: an explicit false does not stop the walk | "reaching the region element without either, or having no start means there is no unit" | atomic-false-stops |
| relevant-nearest: aria-relevant from the nearest element carrying it | "`aria-relevant` anywhere else means nothing." | relevant-region-only |
| removal-at-region: a removal is always placed at its region element | "or for a removal the remembered parent when it is still exposed in the same region" | empty-unit, removal-last-believed |
| anchor-follows-move: a move inside a region refreshes the remembered parent | "Each belief also remembers the parent the node had when those words were taken" | removal-last-believed, anchor-stale-hold |
| busy-region-only: aria-busy honoured on the region element only | "For an addition or a text change the path runs from the node's parent up to and including its region element." | unit-leaves-held, busy-inner |
| cut-to-back: a cut hands changes back at the tick of the cut | "a difference found there waits at the age it had when the utterance took it" | cut-keeps-age |
| assertive-cuts-assertive: an assertive change cuts assertive speech | "Nothing cuts an assertive utterance." | alert-waits |
| belief-by-node: belief kept per node, so a move between regions is nothing | "For every region and every text node the reader believes that certain words are there, or that nothing is." | move-across |
| off-transparent: an off region lets the search carry on outward | "an off region inside a polite one is a region of its own" | off-stops |
| absorb-keeps-carry: absorbing leaves the playing utterance carrying the pair | "and the playing utterance stops carrying that pair" | absorb-carried |
| hidden-false-reveals: aria-hidden false exposes beneath a hidden ancestor | "exposes nothing that such an element hides" | hidden-false-stays |
| hidden-false-shows: hidden=false read as shown | "with any value, or" | hidden-any-value |
| tie-doc-order: equal ages broken by document order | "On equal ages the lower text node id goes first, then the lower region element id." | tie-node-id |
| timing-plus-one: w words last w + 1 ticks | "An utterance of w words started at tick t finishes at tick t + w." | timing-words |
| empty-says: an empty unit is spoken as an empty line | "If a unit has no exposed words, nothing is said and the utterance counts as finished at once" | empty-unit |
| unit-carries-held: a unit carries its held differences too | "The utterance carries every unheld waiting difference whose unit is that same element." | unit-leaves-held |
| busy-above-region: aria-busy above the region element holds | "For an addition or a text change the path runs from the node's parent up to and including its region element." | busy-above-ignored |
| age-resets-on-edit: an edited waiting difference goes to the back | "It keeps that age for as long as it lasts, whatever happens to its words" | edit-keeps-age |
| irrelevant-kept: an irrelevant difference waits for a later relevance change | "does not name, is absorbed on the spot: the reader believes the current words" | relevance-absorbs |
| silent-kept: a difference in an off region waits for the region to voice | "A difference whose region does not voice" | off-absorbs |
| cut-when-held: a held assertive difference still cuts | "an unheld waiting difference in an assertive region cuts it off" | held-alert-no-cut |
| finish-after-cut: the cut check comes before a due utterance finishes | "then the playing utterance finishing if its tick has come, then the comparison, then a cut" | finish-before-cut |
| oldest-across-classes: the oldest goes first whatever its politeness | "or failing that the oldest in a polite region" | assertive-first |
| busy-any-value: aria-busy with any value holds | "A waiting difference is held while an element on its path carries" | busy-false-releases |
| relevant-bogus-empty: only unknown tokens let nothing through | "missing, or with no token it knows, it means" | relevant-bogus |
| region-hidden-voiced: a hidden region still voices its removals | "A region voices while it is exposed and polite or assertive." | region-hidden-silent |

## Shortcuts

| Strategy | Result |
|---|---|
| the shipped tree unchanged (nop) | scores 0: right on 12 of 35 hand pages (the spaced-out ones) and 34 of 276 generated pages in one draw; fails tiny-example, the brief's own page; Docker nop reward 0 |
| constant: nothing spoken on any page (`cheat-const-silent.sh`) | scores 0: right on 0 of 35 hand pages and 1 of 276 generated pages (one whose log is empty); fails plain-once |
| positional: every addition and edit spoken in record order, never cut (`cheat-pos-record-order.sh`) | scores 0: right on 14 of 35 hand pages, the worked example among them, and 32 of 276 generated pages; fails stale-in-line |
| the worked example's output replayed on every page (`cheat-replay-example.sh`) | scores 0: right on 1 of 35 hand pages (tiny-example itself) and 0 of 276 generated pages; fails plain-once |
| the frozen hand answers carried over the shipped reader (`cheat-forge-hand.sh`) | scores 0: right on all 35 hand pages by construction and 35 of 276 generated pages; fails test_every_nonce_program_matches, because the generated pages are drawn after the agent has finished |

## Tolerances

| Tolerance or limit | Independent implementation | Measured |
|---|---|---|
| `tests/test.sh:33` a 60 s clock | `authoring/live-region-reader/variants/ok-cache/voice.py` and `authoring/live-region-reader/variants/ok-region/voice.py`, both written apart from the reference | the whole graded set as the worker inside the verifier image on one CPU, two runs each after the families were reshaped: ok-cache 1.90 and 2.06 s, ok-region 2.48 and 2.62 s, reference 2.29 and 2.40 s; exactly correct but naive readers 193 s (line rescan) and 434 s (whole-page recompute) on the final bundle, and cut off by the 60 s clock (cheat_report.py, docker_trial) |
