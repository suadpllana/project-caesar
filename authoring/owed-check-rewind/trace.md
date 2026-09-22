# Instruction trace: owed-check-rewind

Walked from the verifier toward the instruction (docs/INSTRUCTION-CONTRACT.md). The sealed model
is the test file here, because every graded token is `lines == want` against it, so it is split
into one row per rule it applies, citing its lines. Checked with
`python tools/tracecheck.py owed-check-rewind`.

## Graded assertions

| Verifier site | What it grades | Instruction sentence |
|---|---|---|
| `tests/test_outputs.py:135` test_frozen_truth_matches_the_model | the sealed side agrees with itself before it judges: the model still reproduces every frozen answer | "prints one line per statement" |
| `tests/test_outputs.py:145` test_hand_case | the 50 enumerated programs, line for line against the frozen answers, and that none was altered | "and fifty written by hand" |
| `tests/test_outputs.py:154` test_every_generated_program_matches | the generated population, line for line against the model, and that no program was altered | "The graded set is three programs of each of those two shapes, three hundred and twenty-four smaller ones" |
| `tests/test_outputs.py:172` test_every_family_is_represented | that the population graded holds every family, the two scale shapes included | "three programs of each of those two shapes" |
| `tests/test_outputs.py:91-101` _same | a printout counts only when every line is equal, in number and in content | "Every line is compared exactly" |
| `tests/cases.py:57` case key-dup | an insert of a present key raises key on it before anything else, and aborts | "An insert of a key that is already there raises `key` on it at once" |
| `tests/cases.py:63` case miss-noop | an update or delete of a missing key prints ok and changes nothing | "An update or a delete of a key that is not there does nothing" |
| `tests/cases.py:70` case min-null | a null under an immediate min is no violation | "A null is never below anything" |
| `tests/cases.py:76` case min-floor | a value at the floor passes and one below it raises | "by a row whose col is below N" |
| `tests/cases.py:82` case notnull-null | a deferred notnull gains, loses and regains an entry as the row is written | "is violated by a row whose col is null" |
| `tests/cases.py:97` case row-at-write | a setnull write raises at that moment though a later cascade would remove the row | "checks it at once against each immediate check of its table in declaration order" |
| `tests/cases.py:112` case row-final-state | the same walk with the check deferred owes nothing, because the row is gone at the end | "looks at the rows of its table the statement wrote or deleted" |
| `tests/cases.py:127` case restrict-at-once | restrict raises when the walk reaches it, naming the deleted row | "`restrict` raises at once on the deleted row if there is any such row" |
| `tests/cases.py:141` case noaction-at-end | noaction does nothing at the delete, and a key no longer held at the end is not left behind | "and `noaction` does nothing" |
| `tests/cases.py:155` case walk-listed-late | holders are taken when each fk is reached, so a row an earlier cascade removed is not held | "it takes the rows that hold the deleted key in that fk's column at that moment" |
| `tests/cases.py:169` case walk-touch-order | entries one statement makes are made in the order it first touched their rows | "in the order the statement first wrote or deleted each" |
| `tests/cases.py:185` case walk-depth-first | a cascade finishes each deleted row before the next fk runs | "deletes each one still there in this same way before moving on" |
| `tests/cases.py:204` case cascade-clears | a row deleted by a cascade loses its entries | "looks at the rows of its table the statement wrote or deleted" |
| `tests/cases.py:219` case walk-decl-order | the fks referring to a table run in declaration order | "goes over the fks whose parent is its table, in declaration order" |
| `tests/cases.py:232` case action-deferred | a deferred cascade and a deferred setnull still act at the delete; only what they owe waits | "in declaration order and whatever their modes" |
| `tests/cases.py:249` case imm-key-end | an immediate fk raises at the end, on the child it names or on the key left behind | "The first row that violates it or key it leaves behind raises" |
| `tests/cases.py:259` case imm-order | at the end the immediate fks go in declaration order, not row by row | "each immediate fk in declaration order looks at the rows of its table" |
| `tests/cases.py:277` case lazy-mend | inserting a missing key elsewhere leaves the child owed until a check point | "keeps its entry until a statement looks at it" |
| `tests/cases.py:284` case lazy-own-write | writing the child itself judges it and removes the entry at once | "each that has an entry and is no violation now loses it" |
| `tests/cases.py:291` case rewrite-keeps-place | a row written again while it still violates keeps its entry where it stands | "An entry that is still a violation stays where it stands" |
| `tests/cases.py:299` case side-parent | a deleted parent still held is one entry on the parent table and key | "a key k is left behind by it when P has no row k and some row of T holds k in col" |
| `tests/cases.py:305` case side-reinsert | inserting the key again removes the left-behind entry | "at the keys of its parent the statement deleted or inserted" |
| `tests/cases.py:311` case side-holders-moved | moving the holders away leaves the key entry owed until a check point | "A statement changes no other entry" |
| `tests/cases.py:318` case side-both | a written child and its missing key can both be owed; the older entry raises first | "at most one entry for each constraint and row, or constraint and key left behind" |
| `tests/cases.py:324` case deleted-row-clears | deleting a row removes its entries of every constraint | "each that has an entry and is no violation now loses it" |
| `tests/cases.py:330` case check-and-key | a row owing a check and a key loses both when rewritten | "each deferred constraint, in declaration order, looks at the rows of its table" |
| `tests/cases.py:339` case order-decl | a check point raises on the earlier-declared constraint, not the older entry | "The ledger is ordered by declaration and, within a constraint, by when each entry was made" |
| `tests/cases.py:345` case order-within | within a constraint the older entry raises first | "within a constraint, by when each entry was made" |
| `tests/cases.py:351` case order-listing | a check point lists what it clears in declaration order | "then the entries the statement took out of the ledger as `-C T k` in the order they stood" |
| `tests/cases.py:360` case commit-lists | a commit lists every entry it takes out, in ledger order | "A commit or a rollback that ends the transaction takes out every entry" |
| `tests/cases.py:370` case replace-place | an entry cleared and re-made after a savepoint goes back to its old place, and the rollback lists neither | "each entry in its old place"; "is in neither list, even if its place has changed" |
| `tests/cases.py:380` case rewind-lists | a rollback to a savepoint lists the entries leaving and those coming back | "then the ones it put in as `+C T k` in ledger order" |
| `tests/cases.py:391` case rewind-cleared-back | an entry cleared by a check point after the savepoint comes back, and the mode with it | "The rows, the ledger and every mode are put back exactly as they stood when that savepoint was made" |
| `tests/cases.py:402` case rewind-mode | a mode set after the savepoint is undone by rolling back to it | "The rows, the ledger and every mode are put back exactly as they stood" |
| `tests/cases.py:411` case rewind-keeps | the savepoint survives its own rollback | "the savepoints made after it are dropped, S stays" |
| `tests/cases.py:420` case release-drops-later | release drops the savepoint and every later one | "`release S` drops the latest S and every savepoint made after it" |
| `tests/cases.py:429` case release-merges | a released inner savepoint's work goes back with the outer rollback | "goes back to the latest savepoint named S" |
| `tests/cases.py:439` case shadow | of two savepoints with one name the latest is addressed, and releasing it exposes the older | "`rollback to S` goes back to the latest savepoint named S" |
| `tests/cases.py:449` case error-unknown | an unknown savepoint is an error that aborts, and rollback to a real one recovers | "Naming a savepoint that does not exist is an error" |
| `tests/cases.py:460` case failset-atomic | a failing check point leaves the entries it passed where they were | "the first such raises and nothing changes" |
| `tests/cases.py:472` case set-named-only | set C immediate looks at C's entries only | "`set C immediate` goes over C's entries in ledger order" |
| `tests/cases.py:481` case set-nondeferrable | naming a non-deferrable constraint is an error; set all skips it | "naming one that is not deferrable is an error" |
| `tests/cases.py:491` case set-immediate-nondeferrable | set C immediate naming a constraint that is not deferrable is an error too | "In any `set`, `all` means every deferrable constraint, and naming one that is not deferrable is an error" |
| `tests/cases.py:502` case set-all-deferred | set all deferred defers every deferrable constraint | "`all` means every deferrable constraint" |
| `tests/cases.py:509` case modes-per-txn | modes start from the declared ones in every transaction | "Each transaction starts with the declared modes" |
| `tests/cases.py:519` case abort-ignored | an aborted transaction ignores statements; rollback to a real savepoint recovers | "every statement other than `rollback`, `rollback to S` and `commit` prints `aborted` and does nothing" |
| `tests/cases.py:532` case abort-commit | a commit in an aborted transaction rolls back and says so | "and `commit` rolls back and prints `rollback`" |
| `tests/cases.py:541` case commit-fail | a commit that raises rolls the whole transaction back | "when it raises the whole transaction is rolled back" |
| `tests/cases.py:550` case rollback-lists | a rollback lists every entry it discards | "A commit or a rollback that ends the transaction takes out every entry" |
| `tests/cases.py:560` case place-ordinary | an ordinary transaction with no violation prints ok for every statement | "Every other line is `ok`" |
| artifact `/app/tx/heap.py` | collected and laid over the pristine tree | "The files you may change are" |
| artifact `/app/tx/act.py` | collected and laid over the pristine tree | "The files you may change are" |
| artifact `/app/tx/chk.py` | collected and laid over the pristine tree | "The files you may change are" |
| artifact `/app/tx/owe.py` | collected and laid over the pristine tree | "The files you may change are" |
| artifact `/app/tx/sp.py` | collected and laid over the pristine tree | "The files you may change are" |
| artifact `/app/tx/sess.py` | collected and laid over the pristine tree | "The files you may change are" |
| `tests/worker.py:36-45` overlay | nothing outside the six files can change a printout, a new file beside them included | "The rest of the tree is replaced by our own copy before a program is run, a new file included" |
| `tests/test.sh:34` a 60 s clock | stage one, which runs the whole graded set, is killed at 60 seconds and scores 0 | "All of it has to get through inside 60 seconds" |
| `tests/seal/model.py:87-103` parse | declarations first, then committed rows, then one statement per line | "A program declares its tables and constraints first, one per line" |
| `tests/seal/model.py:60-80` Con, the flags | deferrable and deferrable deferred, and everything else immediate | "which also starts it deferred. Any other constraint is always immediate" |
| `tests/seal/model.py:98` parse, declaration order | the order of check and fk lines is the declaration order | "Declaration order is the order of the check and fk lines" |
| `tests/seal/model.py:83-84` _value | a dash is null | "every value is an integer or `-` for null" |
| `tests/seal/model.py:212-213` _row_bad, notnull | notnull is violated by null | "`check C T col notnull` is violated by a row whose col is null" |
| `tests/seal/model.py:214` _row_bad, min | min is violated below the floor and never by null | "A null is never below anything" |
| `tests/seal/model.py:215` _row_bad, fk | a child row violates when its value names no parent row | "is violated by a row of T whose col is not null and matches the key of no row of P" |
| `tests/seal/model.py:217-218` _left_behind | a key is left behind when no parent row has it and a child holds it | "a key k is left behind by it when P has no row k and some row of T holds k in col" |
| `tests/seal/model.py:308-312` _dml, insert | an insert of a present key raises key before anything is written | "An insert of a key that is already there raises `key` on it at once" |
| `tests/seal/model.py:313-322` _dml, update and delete | an update or delete of a missing key does nothing | "An update or a delete of a key that is not there does nothing" |
| `tests/seal/model.py:239-244` _write | each write checks the row against every immediate check, declaration order, first raises | "and the first one it violates raises" |
| `tests/seal/model.py:246-249` _delete, the order | remove the row, then the fks referring to its table in declaration order | "Deleting a row removes it and then goes over the fks whose parent is its table, in declaration order and whatever their modes" |
| `tests/seal/model.py:250` _delete, the holders | holders taken when the fk is reached, in increasing key order | "in that fk's column at that moment, in increasing key order" |
| `tests/seal/model.py:251-253` _delete, restrict | restrict raises on the deleted row if anything holds it | "`restrict` raises at once on the deleted row if there is any such row" |
| `tests/seal/model.py:254-257` _delete, cascade | cascade deletes each holder still there, depth-first | "`cascade` deletes each one still there in this same way before moving on" |
| `tests/seal/model.py:258-263` _delete, setnull | setnull writes null into the column, which is a write | "`setnull` writes null into that column" |
| `tests/seal/model.py:232-237` _mark | the order rows and keys are first written or deleted | "in the order the statement first wrote or deleted each" |
| `tests/seal/model.py:265-276` _end_immediate | at the end, immediate fks in declaration order over rows written and keys deleted | "When the writes are over, each immediate fk in declaration order looks at the rows of its table the statement wrote that are still there" |
| `tests/seal/model.py:324-327` _dml, the raise | a raising statement is undone, prints raise with constraint, table and key, and aborts | "A statement that raises leaves nothing behind" |
| `tests/seal/model.py:290-298` _end_deferred, what is looked at | deferred constraints in declaration order over rows written or deleted and keys deleted or inserted | "at the keys of its parent the statement deleted or inserted" |
| `tests/seal/model.py:281-288` _end_deferred, settle | violated and not owed gains an entry; owed and not violated loses it; owed and still violated keeps its place | "is a violation now and has no entry gets one"; "An entry that is still a violation stays where it stands" |
| `tests/seal/model.py:283-284` _end_deferred, the recording number | each entry takes its place when it is made | "within a constraint, by when each entry was made" |
| `tests/seal/model.py:227-228` _place | ledger order is declaration index, then recording number | "The ledger is ordered by declaration and, within a constraint, by when each entry was made" |
| `tests/seal/model.py:334-340` _settle | a check point goes over its entries in ledger order and raises on the first still violated | "An entry is still a violation when its row violates the constraint, or its key is left behind, at that moment" |
| `tests/seal/model.py:220-225` _still_bad | a row entry is judged on its row, a key entry on its key | "its row violates the constraint, or its key is left behind" |
| `tests/seal/model.py:352-362` _set, immediate | a clean check point removes the entries and makes the constraints immediate | "Otherwise they all go and the constraints become immediate" |
| `tests/seal/model.py:355-357` _set, a raise | a raising check point changes nothing and aborts | "the first such raises and nothing changes" |
| `tests/seal/model.py:343-350` _set, targets | all is every deferrable constraint; a non-deferrable one named is an error, whichever way it is set | "In any `set`, `all` means every deferrable constraint, and naming one that is not deferrable is an error" |
| `tests/seal/model.py:360-361` _set, deferred | set deferred changes modes only | "`set C deferred` and `set all deferred` only change modes" |
| `tests/seal/model.py:381-386` step, begin | a transaction starts from the declared modes with nothing owed | "Each transaction starts with the declared modes" |
| `tests/seal/model.py:391-403` step, commit | commit goes over every entry; a raise rolls the whole transaction back | "`commit` does the same over every entry, and when it raises the whole transaction is rolled back" |
| `tests/seal/model.py:392-394` step, commit when aborted | in an aborted transaction commit rolls back and prints rollback | "and `commit` rolls back and prints `rollback`" |
| `tests/seal/model.py:387-390` step, rollback | rollback ends the transaction and takes out every entry | "A commit or a rollback that ends the transaction takes out every entry" |
| `tests/seal/model.py:406-407` step, aborted | every other statement prints aborted and does nothing | "prints `aborted` and does nothing" |
| `tests/seal/model.py:408-410` step, savepoint | a savepoint prints ok | "Every other line is `ok`" |
| `tests/seal/model.py:411-418` step, release | release drops the latest S and everything after it; unknown is an error | "`release S` drops the latest S and every savepoint made after it" |
| `tests/seal/model.py:371-375` _find | the latest savepoint with the name | "goes back to the latest savepoint named S" |
| `tests/seal/model.py:423-427` _rollback_to, unknown | an unknown name is an error and aborts | "Naming a savepoint that does not exist is an error" |
| `tests/seal/model.py:430-437` _rollback_to, the restore | rows, ledger with places and modes as when the savepoint was made; later ones dropped; S kept; aborted state ends | "each entry in its old place, the savepoints made after it are dropped, S stays, and an aborted state ends" |
| `tests/seal/model.py:438-440` _rollback_to, the listing | entries leaving in the order they stood, entries coming back in ledger order, an entry there before and after in neither | "the entries the statement took out of the ledger as `-C T k` in the order they stood"; "An entry in the ledger both before and after a statement is in neither list" |
| `tests/seal/model.py:443-447` _ok | ok, then minus entries, then plus entries, single spaces | "all separated by single spaces" |
| `tests/seal/model.py:450-454` expect | one printed line per statement, nothing else | "prints one line per statement" |

## Readings

Every reading below is built by `authoring/owed-check-rewind/emit.py`, measured by
`python tools/readingcheck.py owed-check-rewind` (all 39 separated by the 50 enumerated programs) and
scored as a cheat; `authoring/owed-check-rewind/cheat_report.py` asserts that each is caught by
the case named here.

| Reading | Sentence or published example that rules it out | Case that separates it |
|---|---|---|
| key-upsert: an insert of a present key overwrites the row | "An insert of a key that is already there raises `key` on it at once" | key-dup |
| missing-raises: an update of a missing key raises | "An update or a delete of a key that is not there does nothing" | miss-noop |
| min-null-fails: a null is below every min | "A null is never below anything" | min-null |
| min-inclusive: a value at the floor violates min | "by a row whose col is below N" | min-floor |
| row-at-end: row checks wait for the end of the statement | "checks it at once against each immediate check of its table in declaration order" | row-at-write |
| restrict-at-end: restrict waits for the end like noaction | "`restrict` raises at once on the deleted row if there is any such row" | restrict-at-once |
| noaction-at-delete: an immediate noaction raises at the delete | "When the writes are over, each immediate fk in declaration order looks at the rows of its table" | noaction-at-end |
| walk-breadth: actions run breadth-first | "deletes each one still there in this same way before moving on" | walk-depth-first |
| walk-listed-early: holders of every fk listed before the walk | "the rows that hold the deleted key in that fk's column at that moment" | walk-listed-late |
| walk-reverse: the fks referring to a table in reverse order | "goes over the fks whose parent is its table, in declaration order" | walk-decl-order |
| touch-key-order: a statement's entries made in key order | "in the order the statement first wrote or deleted each" | walk-touch-order |
| imm-touch-first: immediate fks at the end row by row | "each immediate fk in declaration order looks at the rows of its table" | imm-order |
| deferred-no-action: a deferred key's cascade or setnull waits, like its check | "in declaration order and whatever their modes" | action-deferred |
| eager-mend: inserting a missing key clears the holders' entries | "keeps its entry until a statement looks at it" | lazy-mend |
| rewrite-remakes: a row written again while still violating is owed afresh, at the back | "An entry that is still a violation stays where it stands" | rewrite-keeps-place |
| name-children: a key left behind owed by each holder | "a key k is left behind by it when P has no row k and some row of T holds k in col" | side-parent |
| side-eager: a key entry cleared when its holders move away | "A statement changes no other entry" | side-holders-moved |
| side-merged: a holder of an owed key is not owed itself | "at most one entry for each constraint and row, or constraint and key left behind" | side-both |
| deleted-keeps: a deleted row keeps its entries | "looks at the rows of its table the statement wrote or deleted" | deleted-row-clears |
| order-by-record: the ledger ignores declaration order | "The ledger is ordered by declaration and, within a constraint, by when each entry was made" | order-decl |
| newest-first: within a constraint the newest entry first | "within a constraint, by when each entry was made" | order-within |
| failset-clears: a failing check point clears what it passed | "the first such raises and nothing changes" | failset-atomic |
| set-judges-all: set C immediate goes over every entry | "`set C immediate` goes over C's entries in ledger order" | set-named-only |
| commit-no-list: commit takes entries out without listing them | "A commit or a rollback that ends the transaction takes out every entry" | commit-lists |
| rollback-no-list: rollback discards entries without listing them | "A commit or a rollback that ends the transaction takes out every entry" | rollback-lists |
| mode-kept: rollback to a savepoint keeps the modes in force | "The rows, the ledger and every mode are put back exactly as they stood" | rewind-mode |
| modes-carry: modes carry from one transaction to the next | "Each transaction starts with the declared modes" | modes-per-txn |
| nondeferrable-ok: naming a non-deferrable constraint is ignored | "naming one that is not deferrable is an error" | set-nondeferrable |
| immediate-nondeferrable-ok: set C immediate on a constraint that is not deferrable does nothing | "In any `set`, `all` means every deferrable constraint, and naming one that is not deferrable is an error" | set-immediate-nondeferrable |
| recompute-ledger: a rollback recomputes owed entries from the rows | "The rows, the ledger and every mode are put back exactly as they stood when that savepoint was made" | rewind-cleared-back |
| place-not-restored: a restored entry goes to the end | "each entry in its old place" | replace-place |
| list-moved: an entry a rollback moves back to its old place is listed as leaving and coming back | "is in neither list, even if its place has changed" | replace-place |
| release-keeps-later: release drops only the named savepoint | "`release S` drops the latest S and every savepoint made after it" | release-drops-later |
| rollback-drops-it: rollback to S also drops S | "the savepoints made after it are dropped, S stays" | rewind-keeps |
| shadow-oldest: the oldest of two same-named savepoints is addressed | "`rollback to S` goes back to the latest savepoint named S" | shadow |
| unknown-ok: an unknown savepoint does nothing | "Naming a savepoint that does not exist is an error" | error-unknown |
| aborted-acts: savepoint and release still act when aborted | "every statement other than `rollback`, `rollback to S` and `commit` prints `aborted` and does nothing" | abort-ignored |
| aborted-commits: commit in an aborted transaction commits | "and `commit` rolls back and prints `rollback`" | abort-commit |
| commit-fail-keeps: a commit that raises keeps the rows | "when it raises the whole transaction is rolled back" | commit-fail |
| the worked example's reading: a left-behind key named by its holders | "should read `ok +emp_dept dept 1`" | side-parent |

## Shortcuts

| Strategy | Result |
|---|---|
| the shipped tree unchanged (the nop) | reward 0 in host emulation: stage one is killed at the 60 s clock on the scale programs; run without a clock it prints a wrong line in 23 of the 50 hand programs and in 127 of 144 sampled generated ones |
| constant: every statement prints ok (cheat-const-ok) | reward 0; fails 44 of 50 enumerated programs and 144 of 144 sampled generated ones |
| positional: the prior made whole - owed checks recomputed from the rows (cheat-recompute-ledger stands for it at rollback, and the shipped tree everywhere) | reward 0; the shipped tree fails 23 of 50 hand programs and recompute-ledger moves 63 of 144 sampled generated programs |
| the worked example's output replayed: the frozen answers for every enumerated program (cheat-forge-hand) | reward 0; passes all 50 enumerated programs and fails the generated population it could not have seen (54 of 144 sampled) |
| exactly correct but copying or scanning (cheat-slow-copy, cheat-slow-scan, cheat-slow-ledger) | reward 0: every line right, stage one killed at the clock |

## Tolerances

| Tolerance or limit | Independent implementation | Measured |
|---|---|---|
| `tests/test.sh:34` a 60 s clock on the whole graded set | `authoring/owed-check-rewind/variants/ok-journal` and `authoring/owed-check-rewind/variants/ok-queue`, both written apart from the reference and from the model | 13.8 s and 7.8 s for a whole population of 330 generated programs on this machine, against 8.5 s for the reference; the exactly-correct naive executors take 73 s (scan) and 168 s (copy) on one wrap program and 79 s (ledger copy) on one load program |
| exactness: every printed line compared as a string, no tolerance | `tests/seal/model.py`, written from the frozen contract and not from the reference | the model, the reference and both variants print identical lines on 1320 generated programs over four seeds and all 50 hand programs |
