# Instruction trace: rekey-copy-replay

Walked from the verifier toward the instruction (docs/INSTRUCTION-CONTRACT.md). Every graded
assertion, every enumerated case, every collected artifact, the clock, and every rule the sealed
model applies is below with the sentence that tells the agent about it. Checked with
`python tools/tracecheck.py rekey-copy-replay`.

## Graded assertions

| Verifier site | What it grades | Instruction sentence |
|---|---|---|
| `tests/test_outputs.py:128` test_frozen_truth_matches_the_model | the sealed model still reproduces the frozen answers, so a drifted model cannot redefine correct | "prints a line for each thing that happens" |
| `tests/test_outputs.py:138` test_hand_case | every printed line of each enumerated program, in order, against the frozen answer | "prints a line for each thing that happens" |
| `tests/test_outputs.py:147` test_every_nonce_program_matches | every printed line of 330 generated programs against the sealed model | "The graded set is three programs of each of" |
| `tests/test_outputs.py:164` test_the_graded_set_is_the_size_the_brief_states | the graded set is the size the brief quotes | "The graded set is three programs of each of" |
| `tests/test_outputs.py:172` test_generated_programs_respect_the_stated_bounds | the graded programs stay inside the stated bounds on keys, fields, C and n | "each field is an integer below a hundred, C is between 1 and 5, and n is never negative" |
| `tests/test_outputs.py:190` test_every_family_is_represented | that the generated population still covers all eleven shapes | "hundred and twenty-four smaller ones across nine other shapes" |
| `tests/test_outputs.py:141` sig check on a hand program | that the program run is the program given | "programs, and a program is graded exactly as it stands" |
| `tests/test_outputs.py:156` sig check on a nonce program | that the program run is the program given | "programs, and a program is graded exactly as it stands" |
| `tests/cases.py:10` case chunk-count | a chunk takes the next C present keys, not a key range | "takes the C smallest source keys standing above the cursor" |
| `tests/cases.py:14` case chunk-lands | the cursor lands on the largest key taken | "a chunk lands the cursor on the largest key it took" |
| `tests/cases.py:18` case chunk-empty | a chunk that finds nothing leaves the cursor and prints none | "all leaves the cursor where it was and prints `chunk 0` with the cursor and `none`" |
| `tests/cases.py:21` case chunk-after-delete | deletes below the reach do not stop the chunk taking the next present keys | "as the source stands at" |
| `tests/cases.py:25` case walk-order | the keys a chunk took are offered smallest first | "offers those keys to the rebuild in ascending order" |
| `tests/cases.py:31` case mark-not-latest | the mark that decides an entry is the covering reach's, not the newest | "whose position is at most the mark of the reach covering its key is dropped and prints" |
| `tests/cases.py:35` case miss-twice | a delete of a row the rebuild does not know reports a miss | "source key the rebuild is holding no row for prints `miss` with that key" |
| `tests/cases.py:38` case play-then-copy | a play takes n entries, not every entry waiting | "`play n` takes the next n journal entries in position order" |
| `tests/cases.py:42` case late-aside-order | a freed pair goes to the smallest source key, not the first to ask | "key set aside for it takes it at once and prints `on`" |
| `tests/cases.py:46` case mark-per-chunk | each chunk carries its own mark | "which is that reach's mark" |
| `tests/cases.py:50` case mark-boundary | an entry sitting exactly on the mark is dropped | "whose position is at most the mark of the reach covering its key is dropped and prints" |
| `tests/cases.py:53` case mark-after-chunk | an entry written after its chunk was read is applied | "other entry prints `done` and is applied" |
| `tests/cases.py:56` case seen-then-move | an entry dropped as seen leaves the rebuild holding what the chunk wrote | "because the chunk that carried the key was read after the entry was written" |
| `tests/cases.py:62` case ahead-dropped | an entry above the cursor is dropped and never tried again | "stands above the cursor is dropped and prints `entry` with its position, its key and `ahead`" |
| `tests/cases.py:66` case all-ahead | with no chunk yet read every entry is ahead and the walk does the work | "the walk has not reached that key and will read the row itself" |
| `tests/cases.py:69` case zero-play | a play of nothing prints nothing | "`play n` takes the next n journal entries in position order" |
| `tests/cases.py:72` case play-partial | a play takes only what is left when fewer than n remain | "fewer than n are left, and each one it takes is finished with" |
| `tests/cases.py:76` case late-key | a key written below a cursor that has passed it is applied by the replay | "other entry prints `done` and is applied" |
| `tests/cases.py:81` case move-leaves-held | a move leaves the pair the rebuild holds, not the one the entry names | "leaving and frees that key, and a row that was only set aside prints `drop` in the same shape" |
| `tests/cases.py:85` case same-fields | an unchanged pair prints same and does not move | "are unchanged, the third is taken and the row prints `same` with its key and its two fields" |
| `tests/cases.py:88` case same-aside | a row only set aside also prints same | "whether the row is holding that key or only set aside for it" |
| `tests/cases.py:91` case move-into-waiting | a row moving onto a held pair is set aside while its old pair is freed | "A pair already held sets the row" |
| `tests/cases.py:97` case aside-order | the first of two rows wanting one pair holds it and the other is set aside | "taken, and the row prints `on` with its key and that pair" |
| `tests/cases.py:100` case free-smallest | the smallest source key set aside takes a freed pair | "When a pair is freed, the smallest source" |
| `tests/cases.py:104` case two-waiters | releases run one row at a time in source key order | "key set aside for it takes it at once and prints `on`; the rest stay where they are" |
| `tests/cases.py:108` case drop-no-release | a row that was only set aside frees nothing when it leaves | "and frees nothing. It then asks for the pair its new fields name" |
| `tests/cases.py:112` case off-releases | a row that was holding a pair frees it when it leaves | "a row that was holding a key prints `off` with its key and the two fields it is" |
| `tests/cases.py:117` case miss-unknown | an entry above the cursor for a deleted key never reaches the rebuild | "the walk has not reached that key and will read the row itself" |
| `tests/cases.py:120` case del-frees | a delete frees the pair for a row set aside | "A `del` entry that is applied takes the rebuild's row out the same way" |
| `tests/cases.py:123` case miss-after-move | a delete reaches the pair the rebuild holds after a move | "`drop` and freeing the key where it was held, and the rebuild forgets it" |
| `tests/cases.py:126` case key-reuse | a source key written again after a delete is taken again | "`set k a b c` puts the source row under key k with" |
| `tests/cases.py:132` case end-counts | the closing line counts holders, rows set aside, and totals over holders only | "the third field added up over the rows holding a pair only" |
| `tests/cases.py:136` case ordinary | the everyday program with nothing stale and nothing contested still passes | "other entry prints `done` and is applied" |
| `tests/cases.py:140` case cut-loop | cut walks and drains until a chunk takes no key | "`cut` walks a chunk and then plays every entry still waiting, and repeats that until a" |
| artifact `/app/reb/walk.py` | only the declared files are collected | "The files you may change are" |
| artifact `/app/reb/mark.py` | only the declared files are collected | "The files you may change are" |
| artifact `/app/reb/sift.py` | only the declared files are collected | "The files you may change are" |
| artifact `/app/reb/place.py` | only the declared files are collected | "The files you may change are" |
| artifact `/app/reb/wait.py` | only the declared files are collected | "The files you may change are" |
| artifact `/app/reb/tally.py` | only the declared files are collected | "tree is replaced by our own copy before a program is run, a new file put beside those six" |
| `tests/test.sh:35` a 60 s clock | the whole graded set must run inside the wall clock on the worker | "has to get through inside 60 seconds" |
| `tests/seal/model.py:53-57` Model.write | a set appends one journal entry and replaces the source row | "Each `set` and each `del` appends one entry to the journal, whose positions run" |
| `tests/seal/model.py:59-66` Model.erase | a del appends one journal entry whether or not the row was there | "Each `set` and each `del` appends one entry to the journal, whose positions run" |
| `tests/seal/model.py:133-134` Model.copy chunk selection | the C smallest present keys above the cursor, as the source stands | "takes the C smallest source keys standing above the cursor" |
| `tests/seal/model.py:135-137` Model.copy empty chunk | nothing taken leaves the cursor and prints none | "all leaves the cursor where it was and prints `chunk 0` with the cursor and `none`" |
| `tests/seal/model.py:138-141` Model.copy reach and mark | the reach covered is recorded against the journal length | "is every key above where the cursor was and at or below where it now is, against the length the" |
| `tests/seal/model.py:142-143` Model.copy cursor landing | the cursor lands on the largest key taken | "a chunk lands the cursor on the largest key it took" |
| `tests/seal/model.py:144` Model.copy chunk line | the chunk line carries the count, the cursor and the mark | "prints `chunk` with the number of keys it took, the cursor after it and its mark" |
| `tests/seal/model.py:145-147` Model.copy offers | the keys taken are offered in ascending order by the replay's rules | "offers those keys to the rebuild in ascending order" |
| `tests/seal/model.py:150-152` Model._mark_for | the mark is the covering reach's, found by its top | "whose position is at most the mark of the reach covering its key is dropped and prints" |
| `tests/seal/model.py:154-157` Model.play bound | the next n entries in position order, fewer if fewer remain, each consumed | "fewer than n are left, and each one it takes is finished with" |
| `tests/seal/model.py:161-163` Model.play ahead | an entry above the cursor is dropped as ahead | "stands above the cursor is dropped and prints `entry` with its position, its key and `ahead`" |
| `tests/seal/model.py:164-166` Model.play seen | an entry at or below the mark of its reach is dropped as seen | "whose position is at most the mark of the reach covering its key is dropped and prints" |
| `tests/seal/model.py:167-171` Model.play done | every other entry is applied, a set by offer and a del by remove | "other entry prints `done` and is applied" |
| `tests/seal/model.py:110-115` Model.offer unchanged pair | an unchanged pair takes the third field and prints same | "are unchanged, the third is taken and the row prints `same` with its key and its two fields" |
| `tests/seal/model.py:116-121` Model.offer move | a changed pair leaves where it was and then asks again | "Otherwise the row first leaves" |
| `tests/seal/model.py:81-86` Model._withdraw holder | a holder prints off and frees its pair | "a row that was holding a key prints `off` with its key and the two fields it is" |
| `tests/seal/model.py:87-94` Model._withdraw set aside | a row only set aside prints drop and frees nothing | "leaving and frees that key, and a row that was only set aside prints `drop` in the same shape" |
| `tests/seal/model.py:68-79` Model._free | a freed pair goes at once to the smallest source key set aside for it | "When a pair is freed, the smallest source" |
| `tests/seal/model.py:96-108` Model._ask | a free pair is taken and prints on, a held one sets the row aside | "taken, and the row prints `on` with its key and that pair" |
| `tests/seal/model.py:122-130` Model.remove | a delete takes the row out the same way, and an unknown row is a miss | "source key the rebuild is holding no row for prints `miss` with that key" |
| `tests/seal/model.py:175-181` Model.cut loop | cut walks and drains until a chunk takes no key | "`cut` walks a chunk and then plays every entry still waiting, and repeats that until a" |
| `tests/seal/model.py:182-186` Model.cut closing line | the closing counts and the total over holders only | "the third field added up over the rows holding a pair only" |
| `tests/seal/model.py:188-210` expect | the program grammar and that cfg fixes the chunk size | "opens the file and fixes the chunk size" |

## Readings

| Reading | Sentence or published example that rules it out | Case that separates it |
|---|---|---|
| walk-range-chunk | "takes the C smallest source keys standing above the cursor" | chunk-after-delete |
| walk-cursor-top | "a chunk lands the cursor on the largest key it took" | all-ahead |
| walk-desc-offer | "offers those keys to the rebuild in ascending order" | all-ahead |
| mark-one-start | "which is that reach's mark" | chunk-empty |
| mark-latest | "the mark of the reach covering its key" | mark-not-latest |
| sift-apply-behind | "because the chunk that carried the key was read after the entry was written" | ahead-dropped |
| sift-strict-mark | "whose position is at most the mark of the reach covering its key is dropped and prints" | aside-order |
| sift-keep-ahead | "fewer than n are left, and each one it takes is finished with" | ahead-dropped |
| sift-seen-silent | "stands above the cursor is dropped and prints `entry` with its position, its key and `ahead`" | ahead-dropped |
| sift-takes-all | "`play n` takes the next n journal entries in position order" | play-then-copy |
| place-same-reannounce | "are unchanged, the third is taken and the row prints `same` with its key and its two fields" | same-aside |
| place-aside-frees | "and frees nothing. It then asks for the pair its new fields name" | drop-no-release |
| place-no-miss | "source key the rebuild is holding no row for prints `miss` with that key" | miss-twice |
| place-key-from-entry | "leaving and frees that key, and a row that was only set aside prints `drop` in the same shape" | drop-no-release |
| place-move-keeps | "Otherwise the row first leaves" | free-smallest |
| wait-first-asked | "When a pair is freed, the smallest source" | late-aside-order |
| wait-largest | "key set aside for it takes it at once and prints `on`; the rest stay where they are" | free-smallest |
| tally-counts-aside | "the third field added up over the rows holding a pair only" | aside-order |
| tally-total-all | "the third field added up over the rows holding a pair only" | aside-order |

## Shortcuts

| Strategy | Result |
|---|---|
| the shipped tree unchanged (the nop) | reward 0; it disagrees with the frozen answer on 34 of 34 hand programs |
| a constant closing line and no placement lines (cheat-const-end-only) | reward 0; matches 0 of 34 hand programs |
| the closing line of the program the brief quotes, for every program (cheat-hardcode-quoted) | reward 0; matches 1 of 34 hand programs on its closing line and none in full |
| every row given the pair it asks for, nobody set aside (cheat-pos-first-always) | reward 0; the positional strategy loses every contested pair |
| a freed pair to the row that asked first (cheat-wait-first-asked) | reward 0; separated by late-aside-order |
| the real work put in a new file beside the six (cheat-probe-uncollected-file) | reward 0; the file is never collected and the rebuilt tree cannot import it |

## Tolerances

| Tolerance or limit | Independent implementation | Measured |
|---|---|---|
| the 60 second wall clock on the worker, stated as "has to get through inside 60 seconds" | `authoring/rekey-copy-replay/naive/` - correct semantics with the obvious structures - and `tests/seal/model.py`, both written apart from the reference | reference 3.4 s for the six large programs against naive 176.3 s for the same six; the sealed model runs all 330 generated programs in 3.2 s; the two correct variants under `authoring/rekey-copy-replay/variants/` run the same set in 3.5 s |
| exact comparison, no numeric tolerance anywhere | `tests/seal/model.py` and `authoring/rekey-copy-replay/variants/bucketed`, both written apart from the reference | 330 generated and 34 hand programs, 0 disagreements |
