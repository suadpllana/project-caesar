# Instruction trace: pack-span-settle

Walked from the verifier toward the instruction (docs/INSTRUCTION-CONTRACT.md). Every graded
assertion, enumerated case, model rule, collected artifact and clock below is cited against a
sentence of `instruction.md`. Re-run `python tools/tracecheck.py pack-span-settle` after any
change to the instruction, the tests, the model, the generator or the environment.

## Graded assertions

| Verifier site | What it grades | Instruction sentence |
|---|---|---|
| `tests/test_outputs.py:116` test_frozen_truth_matches_the_model | that the sealed model still reproduces the frozen answers before anything is graded; it reads nothing the agent wrote | the frozen answers are the traces of the same contract, so it is held to "prints a line for each record and each step as it settles" and "Nothing else is printed" like every other trace |
| `tests/test_outputs.py:126` test_hand_case | each enumerated shard's trace, line for line, against the frozen answers | "prints a line for each record and each step as it settles" and "Nothing else is printed" |
| `tests/test_outputs.py:135` test_every_nonce_shard_matches | each generated shard's trace, line for line, against the sealed model | "prints a line for each record and each step as it settles" and "The graded set is three shards of each of those two sizes and three hundred and eighty-nine small ones" |
| `tests/test_outputs.py:153` test_every_family_is_represented | that the generated population covers every family; grades nothing the agent wrote | internal to the generator, and "The graded set is three shards of each of those two sizes and three hundred and eighty-nine small ones" states the population the submission is graded on |
| `tests/cases.py:13` case plain-fit | records that fit in the room left share a window, are cut into one piece, and settle at the close of the step holding them | "the longest run of at least two tokens that fits in the room left and leaves the record either finished or with at least two tokens still to place" and "a record of `n` tokens cut into `p` pieces carries `n - p` of them" |
| `tests/cases.py:18` case exact-fill | a record that exactly fills the room leaves no slot behind and forces no short close | "the longest run of at least two tokens that fits in the room left and leaves the record either finished or with at least two tokens still to place" and "A window is also closed when it is full, and at" |
| `tests/cases.py:24` case cross-count | the position where one record ends and the next begins is not scored | "A position is scored when the position after it lies in the same window and belongs to the same record" |
| `tests/cases.py:32` case fill-brim | a record that is not finished takes the whole of the room whenever two or more tokens are left over | "the longest run of at least two tokens that fits in the room left and leaves the record either finished or with at least two tokens still to place" |
| `tests/cases.py:37` case carry-two | a record carried into a second window loses a scored position to the cut, and its divisor with it | "a record of `n` tokens cut into `p` pieces carries `n - p` of them" and "A record's weight is spread evenly over the scored positions it has inside steps that were kept" |
| `tests/cases.py:43` case stranded-tail | taking the whole of the room would strand one token, so the piece steps back and the window closes with a slot unused | "the longest run of at least two tokens that fits in the room left and leaves the record either finished or with at least two tokens still to place" and "When no such run fits, that window is closed with the room left in it unused" |
| `tests/cases.py:49` case room-one | one slot left and a record still to lay: no piece of two tokens fits, so the window closes with it unused | "the longest run of at least two tokens that fits in the room left and leaves the record either finished or with at least two tokens still to place" and "When no such run fits, that window is closed with the room left in it unused" |
| `tests/cases.py:55` case room-two | two slots against three tokens: neither a piece of two nor a piece of one is allowed, so the window closes | "the longest run of at least two tokens that fits in the room left and leaves the record either finished or with at least two tokens still to place" and "When no such run fits, that window is closed with the room left in it unused" |
| `tests/cases.py:60` case first-window | the window a record reports is the one holding its first piece, not the one open when it arrived | "where the first window is the one holding its first piece" |
| `tests/cases.py:68` case one-token | a one token record is passed over, prints `skip` as it is read, and takes no room | "it takes no room at all and prints" |
| `tests/cases.py:73` case two-token | two tokens is the floor, not three: a two token record is laid and scores one position | "the longest run of at least two tokens that fits in the room left and leaves the record either finished or with at least two tokens still to place" and "a record of `n` tokens cut into `p` pieces carries `n - p` of them" |
| `tests/cases.py:78` case skip-shifts | a passed over record leaves the layout exactly as it was, including a later short close | "it takes no room at all and prints" |
| `tests/cases.py:85` case floor-edge | a step carrying exactly the floor is kept | "is trained on only if it carries at least `floor` scored positions" |
| `tests/cases.py:90` case floor-under | a step one position short of the floor is dropped and prints at its close | "One below that is dropped, and prints `drop <step> <windows> <positions>` when it closes" |
| `tests/cases.py:95` case drop-void | a record whose every scored position fell in a dropped step prints `void` | "a record left with none of them prints" |
| `tests/cases.py:101` case drop-part | only kept steps count toward the divisor, so a record's scored count and its divisor differ | "A record's weight is spread evenly over the scored positions it has inside steps that were kept" and "a record of `n` tokens cut into `p` pieces carries `n - p` of them" |
| `tests/cases.py:107` case drop-order | a dropped step prints at its close, before the kept steps waiting behind it on the same record | "its `drop` line comes first if it was dropped, then the records that settle with it in the order the shard declared them, then the step lines they release in step order" |
| `tests/cases.py:114` case band-waits | a step closed while a record is still being laid waits for that record before it settles | "a kept step settles once it has closed and every record with a piece in it has settled" |
| `tests/cases.py:119` case settle-order | one record ending settles several steps at once, printed after it in step order | "its `drop` line comes first if it was dropped, then the records that settle with it in the order the shard declared them, then the step lines they release in step order" |
| `tests/cases.py:124` case many-bands | a record spanning several steps carries its weight into each of them | "A record's weight is spread evenly over the scored positions it has inside steps that were kept" and "the fraction is the sum of what those positions carry, again in lowest terms" and "A fraction that comes out whole keeps its denominator" |
| `tests/cases.py:129` case band-closes | a step whose records all ended inside it settles at its own close, after their lines | "A record settles when the last step it has a piece in closes" and "its `drop` line comes first if it was dropped, then the records that settle with it in the order the shard declared them, then the step lines they release in step order" |
| `tests/cases.py:136` case width-next | a width op sets the width of windows opened after it and does not reach the open one | "A window keeps the width it was opened with" and "A step keeps the span and the floor that were in force when it was opened" |
| `tests/cases.py:142` case span-next | a span op sets the span of steps opened after it and does not resize the open one | "A window keeps the width it was opened with" and "A step keeps the span and the floor that were in force when it was opened" |
| `tests/cases.py:148` case floor-next | a floor op sets the floor of steps opened after it and does not decide the open one | "A window keeps the width it was opened with" and "A step keeps the span and the floor that were in force when it was opened" |
| `tests/cases.py:155` case seal-short | `seal` closes a window with room still in it and the step holding it | "closes the window and the step still open" |
| `tests/cases.py:160` case seal-empty | `seal` with nothing open settles nothing and prints nothing more | "closes the window and the step still open" and "Nothing else is printed" |
| `tests/cases.py:167` case frac-reduce | a weight and a divisor sharing a factor print in lowest terms | "the fraction is its weight over its divisor in lowest terms" and "A fraction that comes out whole keeps its denominator" |
| `tests/cases.py:172` case frac-sum | a step's fraction is the sum over different denominators, in lowest terms | "the fraction is the sum of what those positions carry, again in lowest terms" and "A fraction that comes out whole keeps its denominator" |
| `tests/cases.py:177` case weight-one | a weight of one over many positions stays a fraction | "the fraction is its weight over its divisor in lowest terms" and "A fraction that comes out whole keeps its denominator" |
| artifact `/app/pipe/cut.py` | only the six declared modules are collected from the agent | "The files you may change are `/app/pipe/cut.py`, `/app/pipe/win.py`, `/app/pipe/lay.py`, `/app/pipe/step.py`, `/app/pipe/hold.py` and `/app/pipe/weigh.py`. Nothing else." |
| artifact `/app/pipe/win.py` | only the six declared modules are collected from the agent | "The files you may change are `/app/pipe/cut.py`, `/app/pipe/win.py`, `/app/pipe/lay.py`, `/app/pipe/step.py`, `/app/pipe/hold.py` and `/app/pipe/weigh.py`. Nothing else." |
| artifact `/app/pipe/lay.py` | only the six declared modules are collected from the agent | "The files you may change are `/app/pipe/cut.py`, `/app/pipe/win.py`, `/app/pipe/lay.py`, `/app/pipe/step.py`, `/app/pipe/hold.py` and `/app/pipe/weigh.py`. Nothing else." |
| artifact `/app/pipe/step.py` | only the six declared modules are collected from the agent | "The files you may change are `/app/pipe/cut.py`, `/app/pipe/win.py`, `/app/pipe/lay.py`, `/app/pipe/step.py`, `/app/pipe/hold.py` and `/app/pipe/weigh.py`. Nothing else." |
| artifact `/app/pipe/hold.py` | only the six declared modules are collected from the agent | "The files you may change are `/app/pipe/cut.py`, `/app/pipe/win.py`, `/app/pipe/lay.py`, `/app/pipe/step.py`, `/app/pipe/hold.py` and `/app/pipe/weigh.py`. Nothing else." |
| artifact `/app/pipe/weigh.py` | only the six declared modules are collected from the agent | "The files you may change are `/app/pipe/cut.py`, `/app/pipe/win.py`, `/app/pipe/lay.py`, `/app/pipe/step.py`, `/app/pipe/hold.py` and `/app/pipe/weigh.py`. Nothing else." |
| `tests/test.sh:27` a 60 s clock | the whole graded set must replay inside 60 seconds | "all of it has to get through inside 60 seconds in 2048 MB" |
| `tests/seal/model.py:31-47` piece_len | the piece placed: the longest run of at least two tokens that fits and leaves nothing stranded, or nothing at all | "the longest run of at least two tokens that fits in the room left and leaves the record either finished or with at least two tokens still to place" |
| `tests/seal/model.py:44-47` piece_len step-back | taking the whole of the room when it would strand one token is stepped back by one | "the longest run of at least two tokens that fits in the room left and leaves the record either finished or with at least two tokens still to place" |
| `tests/seal/model.py:49-64` Step | a step carries its cap and floor from when it was opened, its windows, its scored positions, what each record contributed, and its total | "A window keeps the width it was opened with" and "A step keeps the span and the floor that were in force when it was opened" and "where `windows` is how many it held, `positions` is the scored positions in it" |
| `tests/seal/model.py:66-78` Rec | a record carries the window of its first piece, its piece count, its scored count and the steps it touched | "where the first window is the one holding its first piece" |
| `tests/seal/model.py:101-104` Engine.open_step | a step takes the span and floor in force when it is opened, and steps are numbered from 1 | "A window keeps the width it was opened with" and "A step keeps the span and the floor that were in force when it was opened" and "Windows are numbered from 1 in the order they are opened and steps from 1, in each shard" |
| `tests/seal/model.py:106-111` Engine.open_window | a window takes the width in force when it is opened, and windows are numbered from 1 | "A window keeps the width it was opened with" and "A step keeps the span and the floor that were in force when it was opened" and "Windows are numbered from 1 in the order they are opened and steps from 1, in each shard" |
| `tests/seal/model.py:113-117` Engine.close_window | a closed window counts toward its step, and the step closes when it has its span of them | "is trained on only if it carries at least `floor` scored positions" (the step holds `span` windows) and "A window is also closed when it is full, and at" |
| `tests/seal/model.py:119-129` Engine.close_step | a step is kept when it carries at least the floor, and a dropped one prints at its close | "is trained on only if it carries at least `floor` scored positions" and "One below that is dropped, and prints `drop <step> <windows> <positions>` when it closes" |
| `tests/seal/model.py:131-142` Engine.settle_records | the records due at a close are those whose last step is the one that closed | "A record settles when the last step it has a piece in closes" |
| `tests/seal/model.py:144-163` Engine.settle_record | the divisor is the scored positions inside kept steps; zero prints `void`, otherwise `lay` with the weight over it in lowest terms, and each kept step takes its share | "A record's weight is spread evenly over the scored positions it has inside steps that were kept", "a record left with none of them prints" and "the fraction is its weight over its divisor in lowest terms" and "A fraction that comes out whole keeps its denominator" |
| `tests/seal/model.py:165-180` Engine.settle_steps | a kept step prints once it is closed and owes nobody, and they print in step order | "a kept step settles once it has closed and every record with a piece in it has settled" and "its `drop` line comes first if it was dropped, then the records that settle with it in the order the shard declared them, then the step lines they release in step order" |
| `tests/seal/model.py:182-215` Engine.lay | a one token record is passed over and takes no room; otherwise pieces are placed against the room, the window closes when full or when the record continues, a piece of `t` carries `t - 1`, and the scored count is the length less the pieces | "it takes no room at all and prints", "the longest run of at least two tokens that fits in the room left and leaves the record either finished or with at least two tokens still to place", "A position is scored when the position after it lies in the same window and belongs to the same record" and "a record of `n` tokens cut into `p` pieces carries `n - p` of them" |
| `tests/seal/model.py:217-221` Engine.seal | `seal` closes the open window and the open step | "closes the window and the step still open" |
| `tests/seal/model.py:223-241` Engine.run | the five ops and nothing else; `width`, `span` and `floor` change a setting, `rec` lays, `seal` ends | "sets the width of the windows opened after it" |
| `tests/seal/model.py:243-245` trace | drives one shard from its text and returns the trace; no rule of its own | "prints a line for each record and each step as it settles" |
| `tests/seal/model.py:248-250` expect | drives one shard from its op lines and returns the trace; no rule of its own | "prints a line for each record and each step as it settles" |

## Readings

| Reading | Sentence or published example that rules it out | Case that separates it |
|---|---|---|
| cut-brim | the piece rule: "the longest run of at least two tokens that fits in the room left and leaves the record either finished or with at least two tokens still to place" | `stranded-tail` |
| cut-floor-one | the two token floor in "the longest run of at least two tokens that fits in the room left and leaves the record either finished or with at least two tokens still to place" | `room-one` |
| cut-always-back | the whole of the room is taken when two or more are left: "the longest run of at least two tokens that fits in the room left and leaves the record either finished or with at least two tokens still to place" | `fill-brim` |
| div-length | "A record's weight is spread evenly over the scored positions it has inside steps that were kept" with "a record of `n` tokens cut into `p` pieces carries `n - p` of them" | `carry-two` |
| div-first-step | "A record's weight is spread evenly over the scored positions it has inside steps that were kept": every kept step it has a piece in, not the first | `many-bands` |
| div-all-steps | "A record's weight is spread evenly over the scored positions it has inside steps that were kept": inside steps that were kept | `drop-part` |
| scored-length | "a record of `n` tokens cut into `p` pieces carries `n - p` of them" | `carry-two` |
| pay-at-piece | "A record settles when the last step it has a piece in closes" | `band-waits` |
| step-at-shut | "a kept step settles once it has closed and every record with a piece in it has settled" | `band-waits` |
| step-before-lay | "its `drop` line comes first if it was dropped, then the records that settle with it in the order the shard declared them, then the step lines they release in step order" | `band-waits` |
| drop-late | "its `drop` line comes first if it was dropped, then the records that settle with it in the order the shard declared them, then the step lines they release in step order" | `drop-part` |
| first-at-op | "where the first window is the one holding its first piece" | `first-window` |
| lay-one-token | "it takes no room at all and prints" | `one-token` |
| skip-two-token | the two token floor in "the longest run of at least two tokens that fits in the room left and leaves the record either finished or with at least two tokens still to place", and "it takes no room at all and prints" is for one token | `two-token` |
| skip-room | "it takes no room at all and prints" | `one-token` |
| floor-strict | "is trained on only if it carries at least `floor` scored positions" | `floor-edge` |
| floor-now | "A window keeps the width it was opened with" and "A step keeps the span and the floor that were in force when it was opened" | `floor-next` |
| width-now | "A window keeps the width it was opened with" and "A step keeps the span and the floor that were in force when it was opened" | `width-next` |
| span-now | "A window keeps the width it was opened with" and "A step keeps the span and the floor that were in force when it was opened" | `span-next` |
| cross-score | "A position is scored when the position after it lies in the same window and belongs to the same record" | `cross-count` |
| void-zero | "a record left with none of them prints" | `drop-void` |
| frac-raw | "the fraction is its weight over its divisor in lowest terms" and "A fraction that comes out whole keeps its denominator" | `frac-reduce` |
| sum-positions | "the fraction is the sum of what those positions carry, again in lowest terms" and "A fraction that comes out whole keeps its denominator" | `frac-sum` |

Measured, not assumed: `python tools/readingcheck.py pack-span-settle 120` reports every one
of the twenty-three separated by an enumerated case, and
`python authoring/pack-span-settle/cheat_report.py` asserts that each is separated by the case
named for its rule rather than by whichever case happens to come first. Two readings were
dropped after measurement rather than kept on paper: settling a record by the step it started
in is semantically equivalent to settling it by the step it ended in, because only one record
is ever in flight, so it is a correct variant instead; and a step-back rule without the two
token floor cannot terminate, so it is not a reading a solver can hold.

## Shortcuts

| Strategy | Result |
|---|---|
| the shipped tree unchanged (nop) | 0. It is wrong on 28 of the 29 enumerated shards; only `seal-empty` matches |
| constant: the most common line shape for every graded field | 0. `cheat-sum-positions` prints a step's position count where its weight belongs and matches no step line that carries a weight other than its position count; measured 0 |
| positional: the first candidate everywhere - the first window for every record, the first step for every divisor | 0. `cheat-first-at-op` and `cheat-div-first-step` are exactly that, and both score 0 |
| the worked example's output replayed, and the frozen answers carried as a table | 0. `cheat-forge-truth` reproduces all 29 enumerated shards and prints nothing at all on the 366 generated ones |

## Tolerances

| Tolerance or limit | Independent implementation | Measured |
|---|---|---|
| `tests/test.sh:27` a 60 s clock on the whole graded set | `authoring/pack-span-settle/variants/own-tally`, `variants/rational` and `variants/settle-by-first`, each written apart from the reference, and the sealed model in `tests/seal/model.py` | the reference settles all 395 shards in 2.02 s and the three variants score 1 through the real verifier; the sealed model settles the same set in 1.10 s. Two correct-but-costly families fail on it: `cheat-slow-positions`, which keeps a value per token position, takes 248 s on one deep shard, and `cheat-slow-steps`, which asks every step opened so far for a divisor, takes 37 s on each of three wide shards |
| no numeric tolerance anywhere | `authoring/pack-span-settle/variants/rational`, written apart from the reference | it computes the same fractions with a rational type instead of integer pairs and agrees on all 395 shards |
| 2048 MB | `authoring/pack-span-settle/variants/own-tally` and `tests/seal/model.py`, both written apart from the reference | the reference peaks at 62 MB over the whole graded set, the sealed model at 41 MB on the largest single shard; `cheat-slow-positions` is the family the cap and the clock together rule out |

