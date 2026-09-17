# Instruction trace: still-graft-charge

Walked from the verifier toward the instruction (docs/INSTRUCTION-CONTRACT.md). Every graded
assertion, every enumerated case, every branch of the sealed model that can move a printed
token, every condition in `tests/test.sh` that can turn a run into a 0, and every wrong reading
in `authoring/still-graft-charge/readings.py`. Checked with
`python tools/tracecheck.py still-graft-charge`.

## Graded assertions

| Verifier site | What it grades | Instruction sentence |
|---|---|---|
| `tests/test_outputs.py:114` test_frozen_truth_matches_the_model | the sealed side agrees with itself before it judges; grades nothing the agent wrote | "The programs you are graded on are not the ones in" |
| `tests/test_outputs.py:124` test_hand_case | every enumerated program's printed trace, line for line, and that the program was not altered | "The lines come out in the order the ops run, one per line, on standard output" |
| `tests/test_outputs.py:133` test_every_nonce_program_matches | the same, for programs generated after the agent's container is gone | "The programs you are graded on are not the ones in" |
| `tests/test_outputs.py:152` test_every_family_is_represented | that the graded population was not shrunk | "The programs you are graded on are not the ones in" |
| `tests/cases.py:28` case put-fresh | a put lays one block per cell at the size it names, and `at` reports its number | "A block is what a put lays, one per cell of its range, each of the size that put names" |
| `tests/cases.py:37` case put-over | a put over cells the head holds leaves only the new blocks, and the old ones go | "A put over a cell the head already holds a block at leaves the head holding only the new one" |
| `tests/cases.py:45` case put-keep | a still holding the old block keeps it alive across the overwrite, and the drop releases it | "A line holds a block when its head holds it, or when a still the line owns holds it" |
| `tests/cases.py:55` case put-number | a refused put takes no number, so the next taken put takes the one it did not | "lays no block, takes no number, and leaves the line as it was" |
| `tests/cases.py:68` case still-frozen | a still holds what the head held when it was taken, not what it holds later | "A still holds what the head of its line held at the moment it was taken" |
| `tests/cases.py:79` case still-lines | four stills of one line over one block are one holder, not four | "A line holds a block when its head holds it, or when a still the line owns holds it" |
| `tests/cases.py:88` case still-empty | a still of an empty line holds nothing, and a graft from it starts empty | "The head of a graft starts out holding exactly what its origin still holds" |
| `tests/cases.py:99` case graft-share | a block two lines hold is charged to neither | "The charge of a line is the total size of the blocks that line holds and no other line holds" |
| `tests/cases.py:108` case graft-diverge | a graft writing over an inherited cell hands that block back to the line above | "stops holding one of those cells when the graft writes over that cell or cuts it" |
| `tests/cases.py:118` case graft-cut | a graft cutting an inherited cell does the same | "stops holding one of those cells when the graft writes over that cell or cuts it" |
| `tests/cases.py:128` case graft-chain | a graft of a graft holds what its own origin still holds, three lines deep | "The head of a graft starts out holding exactly what its origin still holds" |
| `tests/cases.py:143` case lift-prefix | a lift moves the stills up to and including the origin and no others, and the charges that follow | "The stills of that line up to and including the origin, in the order they were taken, become the stills of the graft" |
| `tests/cases.py:160` case lift-swap | the two origins are swapped, so the line above can itself be lifted afterwards | "the line above becomes a graft of the origin still" |
| `tests/cases.py:175` case lift-root | a lift of a line that was never grafted changes nothing | "A lift of a line that was not grafted does nothing" |
| `tests/cases.py:182` case lift-busy | after a lift the origin still is the line above's origin, so it still cannot be dropped | "A still that a line was grafted from cannot be dropped" |
| `tests/cases.py:195` case drop-busy | the still a line was grafted from is refused, and nothing changes | "prints `busy n` and changes nothing" |
| `tests/cases.py:205` case drop-none | a drop releases nothing while the head is still holding the blocks | "where `z` is the total size of the blocks that still was holding which no line holds any more" |
| `tests/cases.py:213` case drop-some | a drop releases the block the head has since written over | "where `z` is the total size of the blocks that still was holding which no line holds any more" |
| `tests/cases.py:222` case drop-other | with two stills over one block the first drop releases nothing and the second releases it | "where `z` is the total size of the blocks that still was holding which no line holds any more" |
| `tests/cases.py:233` case drop-graft | a graft holding the block means the drop releases nothing, and the charge moves instead | "A line holds a block when its head holds it, or when a still the line owns holds it" |
| `tests/cases.py:248` case cap-fit | a put over its own cells that exactly fills the cap is taken | "is at most the cap" |
| `tests/cases.py:256` case cap-over | a put one over the cap is refused, and the cell it named stays empty | "the put prints `full L`, lays no block" |
| `tests/cases.py:265` case cap-still | a still holding what the put replaces means the put does not pay for itself | "A put on a capped line is taken only if the charge that line would be left with, once the put had landed, is at most the cap" |
| `tests/cases.py:274` case cap-cross | a write on a graft raises the line above's charge and refuses its next put | "The charge of a line is the total size of the blocks that line holds and no other line holds" |
| `tests/cases.py:289` case cap-none | a line with no cap takes every put | "A line with no cap takes every put" |
| `tests/cases.py:299` case cut-hold | a cut releases nothing a still is holding, and the later drop releases it | "A cut leaves the head holding nothing at the cells it names" |
| `tests/cases.py:309` case cut-free | a cut leaves the head holding nothing there, and `at` says so | "`at L k -` when the head holds nothing there" |
| artifact `/app/led/cell.py` | only the declared files are collected | "The files you may change are" |
| artifact `/app/led/hold.py` | only the declared files are collected | "The files you may change are" |
| artifact `/app/led/cost.py` | only the declared files are collected | "The files you may change are" |
| artifact `/app/led/tree.py` | only the declared files are collected | "The files you may change are" |
| artifact `/app/led/gate.py` | only the declared files are collected | "The files you may change are" |
| artifact `/app/led/free.py` | only the declared files are collected | "The files you may change are" |
| `tests/test.sh:27` a 60 s clock | the whole graded set runs in one process under a wall clock, and an unfinished run scores 0 | "under a wall clock of 60 seconds and 2048 MB of memory" |
| `tests/test.sh:36` grader exit status | a worker that crashed, hung or was killed leaves the reward at 0 | "set that has not finished when the clock stops scores exactly as one that came out wrong" |
| `tests/worker.py:32` the six files laid over a pristine tree | nothing but the six files can change a trace; a seventh file is not collected | "seventh file you add under `/app/led` is not taken" |
| `tests/worker.py:64` `ops.ex` called with the shipped op table | the entry points and their arguments are fixed | "goes on calling `cell.mkline`, `cell.erase`, `cell.at`, `gate.cap`, `gate.put`, `tree.freeze`, `tree.sprout`, `tree.lift`, `free.drop` and `cost.charge`" |
| `tests/seal/model.py:173-188` op_put, the cap branch | a put is refused only when the charge it would leave is over the cap | "A put on a capped line is taken only if the charge that line would be left with, once the put had landed, is at most the cap" |
| `tests/seal/model.py:186-188` op_put, the refusal | the refused put prints `full` and changes nothing | "the put prints `full L`, lays no block, takes no number, and leaves the line as it was" |
| `tests/seal/model.py:189` op_put, the numbering | each taken put takes the next number, starting at 1 | "Every put that is taken takes the next number, the first taking 1" |
| `tests/seal/model.py:192-200` op_put, the cells | one fresh block per cell at the size named, closing whatever was open | "A block is what a put lays, one per cell of its range, each of the size that put names" |
| `tests/seal/model.py:204-212` op_cut | the head stops holding the cells named, and nothing else is decided there | "A cut leaves the head holding nothing at the cells it names" |
| `tests/seal/model.py:214-220` op_still | a still is the line frozen at that moment, and taking one moves no charge | "A still holds what the head of its line held at the moment it was taken" |
| `tests/seal/model.py:222-229` op_graft | a graft's head is laid down as what its origin still holds | "The head of a graft starts out holding exactly what its origin still holds" |
| `tests/seal/model.py:236-241` op_lift, the prefix | the stills up to and including the origin move, in the order they were taken | "The stills of that line up to and including the origin, in the order they were taken, become the stills of the graft" |
| `tests/seal/model.py:249-250` op_lift, the origins | the graft takes the line above's origin and the line above takes the origin still | "the graft is then grafted from whatever the line above was grafted from" |
| `tests/seal/model.py:232-234` op_lift, the root case | a lift of a line that was not grafted does nothing | "A lift of a line that was not grafted does nothing" |
| `tests/seal/model.py:261-264` op_drop, the refusal | the still a line was grafted from is refused and nothing changes | "A still that a line was grafted from cannot be dropped" |
| `tests/seal/model.py:274-279` op_drop, the release | what is released is what no line holds any more, and that total is printed | "where `z` is the total size of the blocks that still was holding which no line holds any more" |
| `tests/seal/model.py:129-139` holders | a line holds a block by its head or by a still it owns, and a moved still holds for its new owner | "is the line that owns the still now" |
| `tests/seal/model.py:141-153` rests | a block counts toward a charge only when exactly one line holds it | "The charge of a line is the total size of the blocks that line holds and no other line holds" |
| `tests/seal/model.py:83-94` under | what a still holds at a cell is the block that was there when it was taken | "happens afterwards changes what a still holds" |
| `tests/seal/model.py:281-282` op_ask | the charge is printed as `charge L z` | "`ask L` prints `charge L z` with the charge of that line" |
| `tests/seal/model.py:284-287` op_at | the number of the put that laid the block the head holds, or `-` | "the number of the put that laid the block the head holds at that cell" |
| `tests/seal/model.py:289-313` ex | the op table: the ten ops, their arguments, and which of them print | "A line, a cap, a cut, a still, a graft and a lift print nothing at all" |
| `tests/seal/model.py:315-319` expect | one trace per program, in op order, on standard output | "The lines come out in the order the ops run, one per line, on standard output" |
| `tests/seal/model.py:22-30` Blk | a block carries the size the put named and the number that put took | "each of the size that put names" |
| `tests/seal/model.py:32-41` Place | a block sits at one cell of one line between two still counters | "A range names every cell between its ends, both included" |
| `tests/seal/model.py:43-55` Line | a line is a cap, an origin, the stills it owns, and its cells | "A line is a mutable image: a map from cell to block" |
| `tests/seal/model.py:57-63` Still | a still records the line it was taken on and when | "A still is a line frozen" |
| `tests/seal/model.py:65-73` Ledger | the lines, the stills, the printed trace and the put counter | "Every name a program uses was made by an earlier op and no name is made twice" |

## Readings

| Reading | Sentence or published example that rules it out | Case that separates it |
|---|---|---|
| charge-refs | "A line holds a block when its head holds it, or when a still the line owns holds it" | cap-cross |
| charge-head | "A line holds a block when its head holds it, or when a still the line owns holds it" | cap-still |
| charge-parent | "The charge of a line is the total size of the blocks that line holds and no other line holds" | cap-cross |
| charge-any | "The charge of a line is the total size of the blocks that line holds and no other line holds" | cap-cross |
| still-now | "happens afterwards changes what a still holds" | cut-hold |
| graft-live | "The head of a graft starts out holding exactly what its origin still holds" | still-frozen |
| lift-all | "The stills of that line up to and including the origin, in the order they were taken, become the stills of the graft" | lift-prefix |
| lift-after | "The stills of that line up to and including the origin, in the order they were taken, become the stills of the graft" | lift-prefix |
| lift-keep | "the line above becomes a graft of the origin still" | lift-swap |
| lift-noown | "is the line that owns the still now" | lift-prefix |
| cap-added | "A put on a capped line is taken only if the charge that line would be left with, once the put had landed, is at most the cap" | cap-fit |
| cap-number | "lays no block, takes no number, and leaves the line as it was" | put-number |
| cap-before | "is at most the cap" | cap-fit |
| drop-held | "where `z` is the total size of the blocks that still was holding which no line holds any more" | cut-hold |
| drop-stills | "A line holds a block when its head holds it, or when a still the line owns holds it" | drop-graft |
| drop-any | "A still that a line was grafted from cannot be dropped" | drop-busy |
| drop-grafted | "Any other drop takes the still away" | drop-graft |
| put-release | "A line holds a block when its head holds it, or when a still the line owns holds it" | cap-cross |
| cut-release | "A cut leaves the head holding nothing at the cells it names" | cut-hold |

## Shortcuts

| Strategy | Result |
|---|---|
| the shipped tree unchanged (nop) | reward 0; matches 0 of the 438 graded traces, and also runs out the clock |
| constant: a ledger that prints nothing at all | reward 0; no graded program has an empty trace, so it matches 0 of 438 |
| positional: every charge answered with the size of what the line's head holds | reward 0; this is the `charge-head` cheat, which fails cap-still |
| the worked example's output replayed | reward 0; `cheat-forge-from-truth` carries the frozen answers to all 27 enumerated programs, reproduces every one, and fails the generated population |

## Tolerances

| Tolerance or limit | Independent implementation | Measured |
|---|---|---|
| `tests/test.sh:27` a 60 s clock on the whole graded set | `tests/seal/model.py` and `authoring/still-graft-charge/variants/ok-runs`, both written apart from the reference | reference 5.2 s for 438 programs; ok-runs and ok-predict inside the clock; slow-copy 94.7 s on one wide program and slow-scan 1630.2 s on one deep program, both exactly correct |
| `tests/test.sh:8` 2048 MB on the worker | `authoring/still-graft-charge/variants/slow-plain`, written apart from the reference | the first plan carried through correctly holds a map per still and does not fit the wide family in memory |
