# Instruction trace: feed-lag-pare

Walked from the verifier toward the instruction (docs/INSTRUCTION-CONTRACT.md). Cite the
instruction word for word in double quotes, four words or more. Write NOT STATED where it
says nothing, then write the sentence or stop grading it. Split each model row into one
row per rule it applies, citing its lines. Check with `python tools/tracecheck.py feed-lag-pare`.

## Graded assertions

| Verifier site | What it grades | Instruction sentence |
|---|---|---|
| `tests/test_outputs.py:115` test_the_model_still_reproduces_the_frozen_answers | the sealed model still reproduces the frozen answers; grades nothing the agent wrote | "The graded set is three programs of each of those two sizes, four hundred smaller ones, and thirty-three written by hand" |
| `tests/test_outputs.py:124` test_enumerated_program | every line of every enumerated program, compared with the frozen answer | "Nothing else is printed" |
| `tests/test_outputs.py:133` test_every_generated_program | every line of every generated program, compared with the model | "The graded set is three programs of each of those two sizes, four hundred smaller ones, and thirty-three written by hand" |
| `tests/test_outputs.py:150` test_every_family_was_generated | that the generated population was not shrunk before it was run | "The graded set is three programs of each of those two sizes, four hundred smaller ones, and thirty-three written by hand" |
| `tests/cases.py:11` case fold-add-absent | an `add` onto a key that is absent makes it present at that amount | "`add` raises the value by what it names, and makes an absent key present at that amount" |
| `tests/cases.py:17` case fold-add-after-del | an `add` after a `del` starts the key again rather than doing nothing | "`add` raises the value by what it names, and makes an absent key present at that amount" |
| `tests/cases.py:25` case fold-set-wins | a `set` replaces whatever stood before it | "`set` makes the value what it names" |
| `tests/cases.py:33` case fold-del-reads-absent | a `del` makes the key absent, and absent reads back as a dash | "`del` makes the key absent" |
| `tests/cases.py:42` case head-is-held | the head is a held point even when no mark and no feed exist | "A key is held at the head, at the point of every live mark, and at the position of every live feed whose range covers it" |
| `tests/cases.py:48` case head-moves-on | the head moves as entries are appended, so the top span follows it | "the head is the sequence number of the last entry, or 0 before the first one" |
| `tests/cases.py:56` case two-pins-one-point | two pins standing at one point are one held point, and removing one leaves it held | "Two pins on one point are one held point" |
| `tests/cases.py:66` case unmark-merges | taking a mark away merges the spans it separated | "Those of its held points standing at or below the trailing point cut the rest of the key into spans" |
| `tests/cases.py:77` case feed-keeps-above | an entry above a feed's position is kept as it stands, superseded or not | "An entry above its key's trailing point is never removed and never rewritten" |
| `tests/cases.py:85` case feed-covers-range | a feed holds back only the keys its range covers | "at the position of every live feed whose range covers it" |
| `tests/cases.py:93` case feed-lowest-wins | with two feeds over one key the lower position decides the trailing point | "The trailing point of a key is the lowest position among the live feeds that cover it" |
| `tests/cases.py:103` case feed-close-frees | closing a feed puts its keys back in play | "The trailing point of a key is the lowest position among the live feeds that cover it, and the head when no live feed covers it" |
| `tests/cases.py:112` case feed-outside-collapses | a key no feed covers has its trailing point at the head | "and the head when no live feed covers it" |
| `tests/cases.py:121` case ack-moves-up | an acknowledgement above the position moves the feed | "moves feed `<f>`'s position to `<s>` when `<s>` stands above the feed's current position and not above the head" |
| `tests/cases.py:130` case ack-back-refused | an acknowledgement at or below the position does not move it | "and leaves the position where it is otherwise" |
| `tests/cases.py:139` case ack-at-head | an acknowledgement naming the head is accepted | "and not above the head" |
| `tests/cases.py:148` case ack-past-head-refused | an acknowledgement above the head is refused | "and not above the head" |
| `tests/cases.py:158` case span-nil-keeps-none | a span whose value does not change keeps no entry | "One entry is left behind when the key has different values at the top of the span and at its floor" |
| `tests/cases.py:165` case span-absent-both-ends | absent at both ends counts as no change, so the span keeps nothing | "absent counting as equal to absent" |
| `tests/cases.py:172` case span-one-entry-stands | a span that stands to remove nothing is never collapsed, so its one entry keeps its kind | "A key and one of its spans therefore stand to remove the number of entries of that key the log holds inside it, one less when an entry is left behind" |
| `tests/cases.py:179` case span-keeps-last | the entry left behind is the last of the span, not the first | "That entry sits at the sequence number of the last entry of that key the log still holds inside the span" |
| `tests/cases.py:185` case span-kind-is-set | the entry left behind becomes a `set` carrying the value at the span's top | "it becomes `set <k> <v>` carrying the value at the top of the span" |
| `tests/cases.py:190` case span-kind-is-del | the entry left behind becomes a `del` when the key is absent at the top | "or `del <k>` when the key is absent there" |
| `tests/cases.py:197` case span-last-retained | after a budget stops a pare part way and a mark goes, the entry left behind sits where the retained log says, not where the program wrote last | "the last entry of that key the log still holds inside the span" |
| `tests/cases.py:211` case pare-most-first | the pair standing to remove the most is collapsed first | "it collapses the pair standing to remove the most" |
| `tests/cases.py:220` case pare-tie-lower-span | equal removals go to the span with the lower top | "a tie going to the pair whose span has the lower top" |
| `tests/cases.py:228` case pare-tie-smaller-key | equal removals at one span top go to the smaller key | "and then to the smaller key" |
| `tests/cases.py:235` case pare-stops-at-budget | a pare stops as soon as the log is at the budget, and a log already at it loses nothing | "works while the log holds more than `n` entries" |
| `tests/cases.py:243` case pare-nothing-to-take | a pare that can remove nothing reports nothing removed | "and at least one such pair stands to remove an entry" |
| `tests/cases.py:253` case report-key-order | the report lists keys in ascending order | "one line for each key still holding an entry, in ascending key order" |
| `tests/cases.py:261` case read-survives-pare | every read returns the same value before and after a pare | "A read prints `val <p> <k> <v>`, with `-` in place of the value when that key is absent at that point" |
| `tests/cases.py:274` case floor-only-is-right | the everyday program where the retention-floor reading is exactly right and a service that keeps everything fails | "A pare prints `pare <removed> <kept>`, the entries that command removed and the entries the log holds afterwards" |
| `tests/cases.py:285` case nothing-may-go | the everyday program where nothing may be removed at all | "An entry above its key's trailing point is never removed and never rewritten" |
| artifact `/app/lg/store.py` | only the declared files are collected | "The files you may change are `/app/lg/store.py`, `/app/lg/pin.py`, `/app/lg/fold.py`, `/app/lg/span.py`, `/app/lg/pare.py` and `/app/lg/tell.py`" |
| artifact `/app/lg/pin.py` | only the declared files are collected | "The files you may change are `/app/lg/store.py`, `/app/lg/pin.py`, `/app/lg/fold.py`, `/app/lg/span.py`, `/app/lg/pare.py` and `/app/lg/tell.py`" |
| artifact `/app/lg/fold.py` | only the declared files are collected | "The files you may change are `/app/lg/store.py`, `/app/lg/pin.py`, `/app/lg/fold.py`, `/app/lg/span.py`, `/app/lg/pare.py` and `/app/lg/tell.py`" |
| artifact `/app/lg/span.py` | only the declared files are collected | "The files you may change are `/app/lg/store.py`, `/app/lg/pin.py`, `/app/lg/fold.py`, `/app/lg/span.py`, `/app/lg/pare.py` and `/app/lg/tell.py`" |
| artifact `/app/lg/pare.py` | only the declared files are collected | "The files you may change are `/app/lg/store.py`, `/app/lg/pin.py`, `/app/lg/fold.py`, `/app/lg/span.py`, `/app/lg/pare.py` and `/app/lg/tell.py`" |
| artifact `/app/lg/tell.py` | only the declared files are collected | "The files you may change are `/app/lg/store.py`, `/app/lg/pin.py`, `/app/lg/fold.py`, `/app/lg/span.py`, `/app/lg/pare.py` and `/app/lg/tell.py`" |
| `tests/worker.py:41` the pristine overlay | a new file put beside the six is never collected, and the driver is the verifier's copy | "The rest of the tree is replaced by our own copy before a program is run, a new file put beside those six included" |
| `tests/test.sh:31` a 60 s clock on the whole graded set | a correct service that cannot finish inside the limit scores 0 | "All of it has to get through inside 60 seconds" |
| `tests/seal/model.py:25-38` blend | an `add` composed onto a `del` makes the key present at that amount; onto a `set` it raises it; a `set` or a `del` replaces what came before | "`add` raises the value by what it names, and makes an absent key present at that amount" |
| `tests/seal/model.py:41-48` apply | a `set` makes the value what it names, a `del` makes the key absent, and an `add` onto an absent key makes it present at that amount | "`set` makes the value what it names" |
| `tests/seal/model.py:51-56` effect_of | each entry kind is read as the one effect it has | "`set <k> <v>`, `add <k> <n>` and `del <k>` each append an entry for key `<k>`" |
| `tests/seal/model.py:71-75` Model.add_entry | an entry takes the next sequence number and moves the head | "Entries take the sequence numbers 1, 2, 3 and so on in the order they appear" |
| `tests/seal/model.py:85-89` Model.slice | a span takes the entries above its floor and at or below its top | "A held point belongs to the span it tops, so an entry standing on one is inside the span below it and not the span above" |
| `tests/seal/model.py:92-98` Model.edges | the held points of a key: the head, the marks, and the feeds whose range covers it, counted once per point | "A key is held at the head, at the point of every live mark, and at the position of every live feed whose range covers it" |
| `tests/seal/model.py:100-105` Model.limit | the trailing point is the lowest covering feed position, and the head when none covers | "The trailing point of a key is the lowest position among the live feeds that cover it, and the head when no live feed covers it" |
| `tests/seal/model.py:108-137` Model.stretches | the cut stops at the trailing point, so everything above it is left alone | "An entry above its key's trailing point is never removed and never rewritten" |
| `tests/seal/model.py:140-143` Model.worth | what a pair stands to remove is its entry count, one less when an entry is left behind | "A key and one of its spans therefore stand to remove the number of entries of that key the log holds inside it, one less when an entry is left behind" |
| `tests/seal/model.py:145-150` Model.take | nothing is left behind when the value at the top equals the value at the floor | "One entry is left behind when the key has different values at the top of the span and at its floor, absent counting as equal to absent" |
| `tests/seal/model.py:148` Model.take, the kept sequence | the entry left behind sits at the last sequence the log still holds in the span | "That entry sits at the sequence number of the last entry of that key the log still holds inside the span" |
| `tests/seal/model.py:152-156` Model.take, the kept kind | the entry left behind becomes a `set` with the value at the top, or a `del` when absent there | "it becomes `set <k> <v>` carrying the value at the top of the span, or `del <k>` when the key is absent there" |
| `tests/seal/model.py:161-163` Model.pare, the stop | a pare runs while the log holds more than the budget | "works while the log holds more than `n` entries" |
| `tests/seal/model.py:170-171` Model.pare, nothing to take | a pare stops when no pair stands to remove an entry | "and at least one such pair stands to remove an entry" |
| `tests/seal/model.py:172` Model.pare, the order | most removed first, then the lower span top, then the smaller key | "it collapses the pair standing to remove the most, a tie going to the pair whose span has the lower top and then to the smaller key" |
| `tests/seal/model.py:177` Model.pare, the line | a pare prints what it removed and what the log holds afterwards | "A pare prints `pare <removed> <kept>`, the entries that command removed and the entries the log holds afterwards" |
| `tests/seal/model.py:180-183` Model.where | a read resolves at the point of the mark or feed it names | "`read <p> <k>` reads key `<k>` at the point of mark or feed `<p>`" |
| `tests/seal/model.py:185-191` Model.value_at | a value is folded from the entries the log still holds at or below the point | "applying, in sequence order, every entry of that key the log still holds at or below the point, starting from absent" |
| `tests/seal/model.py:204-206` Model.command, mark | a mark is placed at the head | "`mark <m>` places mark `<m>` at the head" |
| `tests/seal/model.py:210-212` Model.command, feed | a feed opens at the head over the keys it names, inclusive | "`feed <f> <a> <b>` opens feed `<f>` at the head over the keys `<a>` to `<b>` inclusive" |
| `tests/seal/model.py:213-218` Model.command, ack | an acknowledgement moves a feed only above its position and not above the head | "moves feed `<f>`'s position to `<s>` when `<s>` stands above the feed's current position and not above the head, and leaves the position where it is otherwise" |
| `tests/seal/model.py:223-226` Model.command, read | a read prints the pin, the key and the value, with a dash for absent | "A read prints `val <p> <k> <v>`, with `-` in place of the value when that key is absent at that point" |
| `tests/seal/model.py:231-234` Model.touch | a feed reaches only the keys its range covers | "at the position of every live feed whose range covers it" |
| `tests/seal/model.py:236-248` Model.finish | the report: the kept count, then one line per key in ascending order, each entry in sequence order and in its own form | "one line for each key still holding an entry, in ascending key order: `k <key> <item> <item> ...`, one item per entry of that key in sequence order, `<seq>s<v>` for a `set`, `<seq>a<n>` for an `add` and `<seq>d` for a `del`" |
| `tests/seal/model.py:250-256` expect | the whole trace and nothing besides it | "Nothing else is printed" |

## Readings

| Reading | Sentence or published example that rules it out | Case that separates it |
|---|---|---|
| fold-add-noop: an `add` onto an absent key leaves it absent | "makes an absent key present at that amount" | fold-add-absent |
| fold-del-zero: a `del` makes the value zero | "`del` makes the key absent" | fold-del-reads-absent |
| head-not-held: the head is not a held point | "A key is held at the head, at the point of every live mark" | feed-close-frees, head-is-held |
| trailing-any-feed: the trailing point is taken over every feed | "the lowest position among the live feeds that cover it" | feed-covers-range |
| held-any-feed: every feed's position is a held point of every key | "every live feed whose range covers it" | feed-covers-range |
| trailing-highest: the highest feed position decides | "the lowest position among the live feeds that cover it" | feed-lowest-wins |
| unmark-frees-point: removing one mark frees the point for both | "Two pins on one point are one held point" | two-pins-one-point |
| close-leaves-stale: closing a feed does not put its keys back in play | "and the head when no live feed covers it" | feed-close-frees |
| unmark-leaves-stale: removing a mark does not merge the spans | "Those of its held points standing at or below the trailing point cut the rest of the key into spans" | unmark-merges |
| ack-any-point: an acknowledgement moves the feed anywhere | "when `<s>` stands above the feed's current position" | ack-back-refused |
| ack-past-head: an acknowledgement may pass the head | "and not above the head" | ack-past-head-refused |
| span-to-head: spans are cut to the head, so a feed holds nothing back | "An entry above its key's trailing point is never removed and never rewritten" | feed-keeps-above, feed-close-frees |
| span-always-keeps: a span with entries always keeps one | "One entry is left behind when the key has different values at the top of the span and at its floor" | span-nil-keeps-none, fold-del-reads-absent |
| span-keeps-first: the first entry of the span is kept | "the last entry of that key the log still holds inside the span" | span-keeps-last, ack-at-head |
| span-written-last: the last entry the program wrote is kept | "the last entry of that key the log still holds inside the span" | span-last-retained |
| span-del-as-zero: an absent key is left behind as a set of zero | "or `del <k>` when the key is absent there" | span-kind-is-del |
| span-floor-included: a span takes in the entry on its floor | "A held point belongs to the span it tops, so an entry standing on one is inside the span below it" | head-moves-on |
| pare-key-order: pairs are collapsed in key order | "it collapses the pair standing to remove the most" | pare-most-first |
| pare-tie-higher: equal removals go to the higher span top | "a tie going to the pair whose span has the lower top" | pare-tie-lower-span |
| pare-tie-larger-key: equal removals go to the larger key | "and then to the smaller key" | pare-tie-smaller-key |
| pare-one-under: a pare runs until the log is under the budget | "works while the log holds more than `n` entries" | pare-most-first, pare-stops-at-budget |
| pare-count-head: the budget counts every entry ever appended | "the entries the log holds afterwards" | ack-at-head |
| tell-first-touch: the report lists keys as they were first written | "in ascending key order" | pare-most-first, report-key-order |
| tell-absent-zero: absent reads back as zero | "with `-` in place of the value when that key is absent at that point" | fold-del-reads-absent |
| the retrieved plan: one version per pinned interval, everything superseded dropped, one global list of points | ruled out by "An entry above its key's trailing point is never removed and never rewritten" and by "every live feed whose range covers it" | feed-keeps-above, feed-covers-range |
| the batch reading: the retained log recomputed from the written log and the current pins | ruled out by "the last entry of that key the log still holds inside the span" | span-last-retained |

Two readings survived every published statement and agreed with the reference on the whole
graded set, so they were promoted to correct variants that must score 1 rather than kept here:
per-key tables behind a dirty set with the pair list rebuilt once per pare
(`variants/ok-flat`), and stretches composed as single effects with the next collapse picked
out of removal buckets (`variants/ok-effect`). Both are in the Tolerances table below, because
what they also prove is that the execution limit is not measuring the reference.

## Shortcuts

| Strategy | Result |
|---|---|
| the shipped tree unchanged (nop) | reward 0 in the container trial; its trace differs on 33 of 33 hand programs |
| constant: one fixed output for every program (cheat-const-one-line) | reward 0; matches 0 of 439 graded programs |
| positional: a pare that never removes anything (cheat-pos-keep-all) | reward 0; matches 2 of 33 hand programs, the two where nothing may be removed |
| the worked example's output replayed (cheat-replay-example) | reward 0; matches 1 of 33 hand programs |
| the frozen answers carried for every enumerated program (cheat-forge-hand) | reward 0; passes the 33 it carries and fails on the 406 it could not have seen |

## Tolerances

| Tolerance or limit | Independent implementation | Measured |
|---|---|---|
| `tests/test.sh:31` a 60 s clock on the whole graded set | `authoring/feed-lag-pare/variants/ok-flat` and `authoring/feed-lag-pare/variants/ok-effect`, both written apart from the reference, and the sealed model | measured by `authoring/feed-lag-pare/timing.py` over all 439 graded programs: reference 4.4 s, ok-flat 25.4 s, ok-effect 28.7 s, against 160.9 s with the span table rebuilt for every key on every pare, and 87.4 s on the deep family alone with the pair table re-formed after every collapse |
| exact string equality on every printed line, no numeric tolerance | the sealed model and both variants agree line for line with the reference on 33 hand programs, 2500 random programs and 406 generated programs | `authoring/feed-lag-pare/check.py` and `authoring/feed-lag-pare/variant_check.py` |
