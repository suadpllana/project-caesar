# Instruction trace: trial-keep-adopt

Walked from the verifier toward the instruction (docs/INSTRUCTION-CONTRACT.md). Every graded
assertion is a row; every quote is a distinctive span from instruction.md. Checked with
`python tools/tracecheck.py trial-keep-adopt`.

## Graded assertions

| Verifier site | What it grades | Instruction sentence |
|---|---|---|
| `tests/test_outputs.py:113` test_frozen_truth_matches_the_model | the model reproduces gt.json before anything is graded | "prints a line for each thing the service does" |
| `tests/test_outputs.py:123` test_hand_case | each hand program's whole trace equals the frozen answer | "prints a line for each thing the service does" |
| `tests/test_outputs.py:132` test_every_nonce_program_matches | each generated program's whole trace equals the model | "prints a line for each thing the service does" |
| `tests/test_outputs.py:151` test_every_family_is_represented | the population covers the whole graded set | "The graded set is three programs of each of those two sizes" |
| `tests/cases.py:14` case run-order | a line is written when an evaluation finishes, reads above it | "a line is written when a field's evaluation finishes and the fields it read therefore stand above it" |
| `tests/cases.py:19` case cut-stops | a source moves without moving a capped field above it | "each is compared with the value it returned then" |
| `tests/cases.py:24` case bail-stops | the check stops at the first read that differs | "That check stops at the first read that comes back different" |
| `tests/cases.py:31` case flip-drop | an evaluation replaces its read list, an abandoned arm stops mattering | "in that order and with a field it read twice appearing twice, is the record the next check walks, and it replaces whatever the field recorded before" |
| `tests/cases.py:39` case gate-zero | a gate with a zero guard never reads its field | "reads its guard and then its field only when that guard is not zero" |
| `tests/cases.py:44` case pick-one | a pick reads the guard and only one arm | "reads its guard and then one arm" |
| `tests/cases.py:50` case twice-once | a field reached twice in one question is evaluated once | "asked for again, in the order it read them" |
| `tests/cases.py:55` case no-ask-no-run | a publication with no question evaluates nothing | "nothing but a question ever makes a field evaluate" |
| `tests/cases.py:60` case pre-keeps | the block leaves the kept results where they were | "leaves the results held outside it exactly as they were" |
| `tests/cases.py:65` case pre-share | a field the block cannot reach is not evaluated in it | "A field whose check passes under that value keeps what it had and is not evaluated" |
| `tests/cases.py:70` case pre-cut | the block turns on the value, not on reaching the source | "A field whose check passes under that value keeps what it had and is not evaluated" |
| `tests/cases.py:75` case layer-first | inside the block, the block's results stand over the base | "what it produced belongs to the block" |
| `tests/cases.py:80` case adopt-install | publishing the previewed value installs the block's results | "Publishing that same value to that same source makes them the service's own" |
| `tests/cases.py:86` case adopt-check | installed results are checked, an unrelated publication leaves the layer | "publishing to any other source leaves them standing" and "checked like any other, so a field whose reads moved while it stood is evaluated again" |
| `tests/cases.py:93` case adopt-other | a different value throws the layer away | "publishing a different value to that source throws them away" |
| `tests/cases.py:100` case adopt-second | opening another block throws the standing one away | "opening another block throws them away" |
| `tests/cases.py:108` case same-holds | publishing the value a source already carries does nothing | "Publishing to a source the value it already carries does nothing whatever" |
| `tests/cases.py:115` case pin-stands | a pinned field stands whatever moves under it | "A pinned field stands at the value it was pinned at" |
| `tests/cases.py:120` case pin-takes | pinning demands the field first | "Pinning asks for the field first, so a field with nothing to stand on is evaluated by the pin" |
| `tests/cases.py:125` case pin-blocks | a pin holds inside a block and stops it spreading | "It is never evaluated and the fields it reads are never asked for on its account, until it is freed" |
| `tests/cases.py:130` case block-many | several questions in one block, and the block's own settling | "and holds nothing but questions" |
| `tests/cases.py:137` case bulk-small | the import shorthand | "is the import shorthand that declares" |
| artifact `/app/fld/keep.py` | one of the six collected files | "The files you may change are" |
| artifact `/app/fld/look.py` | one of the six collected files | "The files you may change are" |
| artifact `/app/fld/make.py` | one of the six collected files | "The files you may change are" |
| artifact `/app/fld/need.py` | one of the six collected files | "The files you may change are" |
| artifact `/app/fld/feed.py` | one of the six collected files | "The files you may change are" |
| artifact `/app/fld/hold.py` | one of the six collected files | "The files you may change are" |
| `tests/test.sh:27` a 60 s clock | the whole graded set finishes in 60 s | "all of it has to get through inside 60 seconds" |
| `tests/seal/model.py:30` nxt | which field a form reads next: sum L-to-R, cap its field, pick guard then arm, gate guard then field-if-nonzero | "A sum reads its fields left to right, a cap reads its field, a pick reads its guard and then one arm, and a gate reads its guard and then its field only when that guard is not zero" |
| `tests/seal/model.py:50` fin | a form's value: sum totals, cap the smaller, pick the arm, gate the arm or zero | "The four derived forms are" and "and worth the smaller of the two" |
| `tests/seal/model.py:61` State.want check | a kept result is checked read by read and evaluated on the first difference | "the fields its last evaluation read are asked for again, in the order it read them" and "That check stops at the first read that comes back different" |
| `tests/seal/model.py:61` State.want keep | a check whose reads all match keeps the value silently | "A check whose reads all come back with the values they had keeps the value and writes nothing" |
| `tests/seal/model.py:61` State.want source | a source is never evaluated and reads the previewed value in a block | "A source is never evaluated" and "Inside one the named source reads as the named value" |
| `tests/seal/model.py:61` State.want pin | a pinned field stands at its value and is not evaluated | "A pinned field stands at the value it was pinned at" |
| `tests/seal/model.py:203` step put | publishing installs, discards or leaves the layer, and same value is a no-op | "Publishing that same value to that same source makes them the service's own, publishing a different value to that source throws them away, opening another block throws them away, and publishing to any other source leaves them standing" |
| `tests/seal/model.py:203` step open/shut | a block reads as the value and its results outlive it | "Those results outlive the block" |
| `tests/seal/model.py:203` step pin | pinning demands the field first and fixes that value | "the value the pin fixes is the one that question produced" |
| `tests/seal/model.py:203` step bulk | the import shorthand builds cap-at-500 and sum, publishing i%s+1 | "as a cap of it at 500 and" |
| `tests/seal/model.py:232` expect | run/val are the only lines written | "A field's evaluation writes" and "Nothing else is written" |

## Readings

| Reading | Sentence or published example that rules it out | Case that separates it |
|---|---|---|
| dirty the dependents outward from a publication | "only when the service cannot show that the value it already has still stands" (a walk down from the question) | no-ask-no-run |
| check every recorded read, not stop at the first | "That check stops at the first read that comes back different" | bail-stops |
| record the form's arguments, not the reads taken | "is the record the next check walks" (the reads, in order) | flip-drop |
| merge new reads into the record | "it replaces whatever the field recorded before" | flip-drop |
| read both arms of a pick or gate | "reads its guard and then one arm" | pick-one, gate-zero |
| throw the block's results away at its end | "Those results outlive the block" | pre-keeps |
| write the block's results into the kept results | "leaves the results held outside it exactly as they were" | pre-keeps |
| re-evaluate everything demanded inside a block | "A field whose check passes under that value keeps what it had and is not evaluated" | pre-share |
| evaluate every field that can reach the previewed source | "A field whose check passes under that value keeps what it had" | block-many |
| consult the kept results before the layer | "what it produced belongs to the block" | block-many |
| install the layer on any publication to its source | "Publishing that same value to that same source" | adopt-other |
| install without checking the results after | "A result taken over that way is checked like any other" | adopt-check |
| invalidate on a publication of the value already carried | "Publishing to a source the value it already carries does nothing whatever" | same-holds |
| drop a standing layer on a publication to another source | "publishing to any other source leaves them standing" | adopt-check |
| check a pinned field instead of standing it | "A pinned field stands at the value it was pinned at" | pin-stands |
| pin the kept value without demanding the field | "Pinning asks for the field first" | pin-takes |
| write the run line before the body | "a line is written when a field's evaluation finishes" | run-order |

## Shortcuts

| Strategy | Result |
|---|---|
| the shipped tree unchanged (nop) | 0 - the shipped engine is wrong in six places; caught across every family |
| constant: one fixed value for every field | 0 - the run lines are the graded output and no constant reproduces them |
| positional: always evaluate, never check | this is the `pre-fresh`/`no-memo` shape; correct on values, killed by the deep limit or by silent-keep cases |
| the worked example's output replayed | 0 - the worked example is tiny.txt's fix; every hand and nonce program differs |

## Tolerances

| Tolerance or limit | Independent implementation | Measured |
|---|---|---|
| `tests/test.sh:27` a 60 s clock | `authoring/trial-keep-adopt/readings/pre-copy/hold.py` and `authoring/trial-keep-adopt/readings/no-memo/need.py`, written apart from the reference | reference 3s for the whole set; pre-copy 88-95s on wide alone; no-memo over 240s on one deep program |
