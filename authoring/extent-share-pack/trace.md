# Instruction trace: extent-share-pack

Walked from the verifier toward the instruction (docs/INSTRUCTION-CONTRACT.md). Every graded
assertion, enumerated case, artifact, clock and rule of the sealed model is carried to the
sentence that tells the agent about it. Re-run `python tools/tracecheck.py extent-share-pack`
after any change to the instruction, the tests, the model, the generator or the environment.

## Graded assertions

| Verifier site | What it grades | Instruction sentence |
|---|---|---|
| `tests/test_outputs.py:110` test_frozen_truth_matches_the_model | that the sealed model still reproduces every frozen answer before anything else is judged; it grades the verifier, not the submission | "The graded set is three programs of each of those two shapes and three hundred and forty-two smaller ones" |
| `tests/test_outputs.py:119` test_hand_case | the trace of each enumerated program, line for line, against the frozen answers | "an extent given up because nothing points into it prints `gone <extent>`, a rewrite prints `pack <old> <new> <blocks>` and nothing else for the extent it replaced" and "Within one op the write's line comes first, then a line for each extent given up in increasing extent number, then the rewrites in increasing number of the extent being rewritten" |
| `tests/test_outputs.py:125` test_every_nonce_program_matches | the trace of every generated program against the sealed model, all or nothing | "The graded set is three programs of each of those two shapes and three hundred and forty-two smaller ones" |
| `tests/test_outputs.py:135` test_every_family_is_represented | that the generated population still carries all nine families, the two large ones included | "The graded set is three programs of each of those two shapes and three hundred and forty-two smaller ones" |
| `tests/cases.py:29` case put-fresh | a write makes a new extent and the whole of it is charged to the volume | "allocates one extent with a block for each slot from `lo` to `hi` and points those slots at its blocks in order, dropping whatever they held" and "is the whole size of every extent it is on, each counted once however many of its slots are inside" |
| `tests/cases.py:39` case put-steal | a write over live slots takes them from the extent that held them, which keeps its whole size | "allocates one extent with a block for each slot from `lo` to `hi` and points those slots at its blocks in order, dropping whatever they held" and "An extent takes up its whole size for as long as any block of it is pointed at" |
| `tests/cases.py:49` case put-first-id | the write takes its extent number before the rewrite in the same op does | "Extents are numbered from 1 in the order they are allocated. A write takes its number before it touches a slot, and each rewrite takes one as it runs" |
| `tests/cases.py:62` case use-once | an extent is charged once to a volume however many of its slots are on it | "is the whole size of every extent it is on, each counted once however many of its slots are inside" |
| `tests/cases.py:71` case use-whole | a volume on one block of an extent is charged the whole extent | "An extent takes up its whole size for as long as any block of it is pointed at" and "is the whole size of every extent it is on, each counted once however many of its slots are inside" |
| `tests/cases.py:85` case hold-dup | two slots on one block count as one block occupied, so the extent falls under half | "A block is pointed at or it is not. Two slots on one block are one block and not two" and "every extent that slots of exactly one volume point into, and that has twice its pointed-at blocks fewer than its size, is rewritten" |
| `tests/cases.py:96` case hold-twice | a volume with two slots on an extent is still on it after one is cleared | "A volume is on an extent while any slot of that volume points into it" |
| `tests/cases.py:106` case hold-last | an extent survives while another volume still points into it | "given up the moment no slot anywhere points into it" |
| `tests/cases.py:119` case pack-half | an extent at exactly half is left alone | "every extent that slots of exactly one volume point into, and that has twice its pointed-at blocks fewer than its size, is rewritten" |
| `tests/cases.py:128` case pack-under | an extent under half is rewritten and its surviving blocks are renumbered in order | "every extent that slots of exactly one volume point into, and that has twice its pointed-at blocks fewer than its size, is rewritten" and "a new extent is allocated with exactly as many blocks as were pointed at, those blocks keep the order they were in, every pointer into the old extent moves to the block of the new one that its own block became" |
| `tests/cases.py:140` case pack-shared | an extent two volumes are on is left alone however little of it is occupied | "every extent that slots of exactly one volume point into, and that has twice its pointed-at blocks fewer than its size, is rewritten" |
| `tests/cases.py:152` case pack-order | two extents made eligible by one op are rewritten in increasing extent number | "Within one op the write's line comes first, then a line for each extent given up in increasing extent number, then the rewrites in increasing number of the extent being rewritten" and "Extents are numbered from 1 in the order they are allocated. A write takes its number before it touches a slot, and each rewrite takes one as it runs" |
| `tests/cases.py:163` case pack-dup | two slots on one block land on one block of the new extent | "a new extent is allocated with exactly as many blocks as were pointed at, those blocks keep the order they were in, every pointer into the old extent moves to the block of the new one that its own block became" and "A block is pointed at or it is not. Two slots on one block are one block and not two" |
| `tests/cases.py:174` case pack-one | a two block extent with one block occupied is not under half | "every extent that slots of exactly one volume point into, and that has twice its pointed-at blocks fewer than its size, is rewritten" |
| `tests/cases.py:185` case drop-gone | dropping a volume gives up what only it was on, and the drop question said so first | "removes a volume and every pointer in it" and "`own v` prints how much smaller that total would be if `rm v` ran next" |
| `tests/cases.py:198` case drop-cascade | a drop leaves an extent single-held and it is rewritten in that same op | "After the pointer changes of an op, and not partway through them, the store settles" and "every extent that slots of exactly one volume point into, and that has twice its pointed-at blocks fewer than its size, is rewritten" |
| `tests/cases.py:211` case drop-keeps | dropping a snapshot leaves a fully occupied extent alone | "removes a volume and every pointer in it" and "every extent that slots of exactly one volume point into, and that has twice its pointed-at blocks fewer than its size, is rewritten" |
| `tests/cases.py:224` case own-solo | the drop question counts the extents only that volume is on | "`own v` prints how much smaller that total would be if `rm v` ran next" |
| `tests/cases.py:232` case own-pair | the drop question carries the rewrite the drop would leave behind in the other volume | "`own v` prints how much smaller that total would be if `rm v` ran next" and "every extent that slots of exactly one volume point into, and that has twice its pointed-at blocks fewer than its size, is rewritten" |
| `tests/cases.py:246` case own-three | an extent three volumes are on gives nothing back | "`own v` prints how much smaller that total would be if `rm v` ran next" and "every extent that slots of exactly one volume point into, and that has twice its pointed-at blocks fewer than its size, is rewritten" |
| `tests/cases.py:262` case own-nogain | a shared extent whose survivor is on half or more gives nothing back | "`own v` prints how much smaller that total would be if `rm v` ran next" and "every extent that slots of exactly one volume point into, and that has twice its pointed-at blocks fewer than its size, is rewritten" |
| `tests/cases.py:275` case own-dup | the other volume's occupancy is counted in blocks, not in pointers | "`own v` prints how much smaller that total would be if `rm v` ran next" and "A block is pointed at or it is not. Two slots on one block are one block and not two" |
| `tests/cases.py:290` case own-snap | a fresh snapshot leaves both volumes with nothing to give back | "makes a volume `w` holding, for every file of `v`, a file of the same name with the same pointers" and "`own v` prints how much smaller that total would be if `rm v` ran next" |
| `tests/cases.py:304` case cp-before | an overlapping copy takes the pointers as they stood before it started | "it reads them as they stood before the copy started, and where the source slot is empty the slot it lands in is emptied too" |
| `tests/cases.py:317` case cp-empty | an empty source slot empties the slot it is copied into | "it reads them as they stood before the copy started, and where the source slot is empty the slot it lands in is emptied too" and "`at v f i` prints what slot `i` of file `f` of volume `v` points at" |
| `tests/cases.py:328` case line-order | what was given up is printed before what was rewritten, in extent number order | "Within one op the write's line comes first, then a line for each extent given up in increasing extent number, then the rewrites in increasing number of the extent being rewritten" |
| `tests/cases.py:338` case line-quiet | a bulk prints nothing and an op that changes nothing prints nothing | "nothing at all is printed for it" and "Nothing else is printed" |
| artifact `/app/st/ext.py` | only the declared files are collected | "Those six files are the only ones taken from your container" |
| artifact `/app/st/pt.py` | only the declared files are collected | "Those six files are the only ones taken from your container" |
| artifact `/app/st/pk.py` | only the declared files are collected | "Those six files are the only ones taken from your container" |
| artifact `/app/st/step.py` | only the declared files are collected | "Those six files are the only ones taken from your container" |
| artifact `/app/st/tot.py` | only the declared files are collected | "Those six files are the only ones taken from your container" |
| artifact `/app/st/own.py` | only the declared files are collected | "Those six files are the only ones taken from your container" |
| `tests/test.sh:40` a 60 s clock on the half that executes submitted code | the whole graded set has to finish inside the wall clock, which is the execution limit | "the whole of it has to run inside 60 seconds in the 2048 MB the container is given" |
| `tests/seal/model.py:25-45` M | the store the model keeps: slots, extents, per-block and per-volume tallies | "a slot is either empty or points at one block of one extent" |
| `tests/seal/model.py:47-51` M.parts, the use term | an extent contributes its whole size to every volume on it, once | "is the whole size of every extent it is on, each counted once however many of its slots are inside" |
| `tests/seal/model.py:52-53` M.parts, the solo term | an extent only one volume is on is what the drop gives back outright | "`own v` prints how much smaller that total would be if `rm v` ran next" |
| `tests/seal/model.py:54-58` M.parts, the pair term | an extent shared with exactly one other volume gives back what its rewrite would, measured on the other volume's occupancy | "`own v` prints how much smaller that total would be if `rm v` ran next" and "every extent that slots of exactly one volume point into, and that has twice its pointed-at blocks fewer than its size, is rewritten" |
| `tests/seal/model.py:68-81` M.attach | a pointer put on a block, and the tallies it moves | "allocates one extent with a block for each slot from `lo` to `hi` and points those slots at its blocks in order, dropping whatever they held" |
| `tests/seal/model.py:73-75` M.attach, occupancy | a block already pointed at does not become occupied twice | "A block is pointed at or it is not. Two slots on one block are one block and not two" |
| `tests/seal/model.py:76-80` M.attach, presence | a volume counts as on the extent for as long as one of its slots is | "A volume is on an extent while any slot of that volume points into it" |
| `tests/seal/model.py:83-109` M.detach | a pointer taken off a slot, and the tallies it moves back | "A trim, `tr v f lo hi`, empties the named slots" |
| `tests/seal/model.py:111-119` M.born | extent numbers come from one counter in allocation order | "Extents are numbered from 1 in the order they are allocated. A write takes its number before it touches a slot, and each rewrite takes one as it runs" |
| `tests/seal/model.py:121-129` M.buried | an extent leaves the store and stops being charged | "given up the moment no slot anywhere points into it" |
| `tests/seal/model.py:131-139` M.after | the settle runs after an op's pointer changes and gives up what nothing points into, in extent number order | "After the pointer changes of an op, and not partway through them, the store settles" and "First every extent no slot points into is given up" |
| `tests/seal/model.py:140-143` M.after, eligibility | exactly one volume on it and twice the occupied blocks under its size | "every extent that slots of exactly one volume point into, and that has twice its pointed-at blocks fewer than its size, is rewritten" |
| `tests/seal/model.py:145-158` M.rewrite | the new extent, the renumbering of surviving blocks, the moved pointers and the line printed | "a new extent is allocated with exactly as many blocks as were pointed at, those blocks keep the order they were in, every pointer into the old extent moves to the block of the new one that its own block became" and "an extent given up because nothing points into it prints `gone <extent>`, a rewrite prints `pack <old> <new> <blocks>` and nothing else for the extent it replaced" |
| `tests/seal/model.py:162-169` M.wr | the write allocates first, then points the slots, dropping what they held | "allocates one extent with a block for each slot from `lo` to `hi` and points those slots at its blocks in order, dropping whatever they held" and "Extents are numbered from 1 in the order they are allocated. A write takes its number before it touches a slot, and each rewrite takes one as it runs" |
| `tests/seal/model.py:171-178` M.cp | the copy reads its source before it writes anything, and an empty source empties the target | "it reads them as they stood before the copy started, and where the source slot is empty the slot it lands in is emptied too" |
| `tests/seal/model.py:180-183` M.tr | the trim empties the named slots | "A trim, `tr v f lo hi`, empties the named slots" |
| `tests/seal/model.py:185-193` M.sn | the snapshot copies every file and every pointer of the volume | "makes a volume `w` holding, for every file of `v`, a file of the same name with the same pointers" |
| `tests/seal/model.py:195-203` M.rm | the drop takes away every pointer of the volume | "removes a volume and every pointer in it" |
| `tests/seal/model.py:205-214` M.bulk | the import shorthand writes n extents of w blocks and prints nothing | "makes file `f` with `n * w` slots and writes `n` extents of `w` blocks, the i-th covering the i-th run of `w` consecutive slots" and "nothing at all is printed for it" |
| `tests/seal/model.py:236-237` M.ex, use | what a volume is charged | "`use v` prints what `v` is charged" |
| `tests/seal/model.py:238-239` M.ex, own | how much smaller the store would be without the volume | "`own v` prints how much smaller that total would be if `rm v` ran next" |
| `tests/seal/model.py:240-241` M.ex, tot | the size of everything the store still holds | "`tot` prints the total size of the extents the store is still holding" |
| `tests/seal/model.py:242-246` M.ex, at | what a slot points at, or that it points at nothing | "`at v f i` prints what slot `i` of file `f` of volume `v` points at" and "with `none` standing in for the extent and block when the slot points at nothing" |
| `tests/seal/model.py:251-257` expect | one program driven op by op, returning the lines in the order they were printed | "`/app/run_st.py` takes one and prints a line for each thing that happens" |

## Readings

| Reading | Sentence or published example that rules it out | Case that separates it |
|---|---|---|
| own-solo-only | "`own v` prints how much smaller that total would be if `rm v` ran next" | own-pair |
| own-as-use | "`own v` prints how much smaller that total would be if `rm v` ran next" and "`use v` prints what `v` is charged" | own-pair |
| own-no-threshold | "`own v` prints how much smaller that total would be if `rm v` ran next" and "every extent that slots of exactly one volume point into, and that has twice its pointed-at blocks fewer than its size, is rewritten" | own-nogain |
| own-pair-self | "`own v` prints how much smaller that total would be if `rm v` ran next" | own-dup |
| own-pair-on-use | "`own v` prints how much smaller that total would be if `rm v` ran next" and "a new extent is allocated with exactly as many blocks as were pointed at, those blocks keep the order they were in, every pointer into the old extent moves to the block of the new one that its own block became" | own-pair |
| use-by-pointer | "is the whole size of every extent it is on, each counted once however many of its slots are inside" | use-once |
| use-by-block | "An extent takes up its whole size for as long as any block of it is pointed at" and "is the whole size of every extent it is on, each counted once however many of its slots are inside" | use-whole |
| tot-by-block | "An extent takes up its whole size for as long as any block of it is pointed at" and "`tot` prints the total size of the extents the store is still holding" | pack-half |
| occ-by-pointer | "A block is pointed at or it is not. Two slots on one block are one block and not two" | hold-dup |
| vol-as-set | "A volume is on an extent while any slot of that volume points into it" | hold-twice |
| vocc-by-pointer | "`own v` prints how much smaller that total would be if `rm v` ran next" and "A block is pointed at or it is not. Two slots on one block are one block and not two" | own-dup |
| pack-at-most-half | "every extent that slots of exactly one volume point into, and that has twice its pointed-at blocks fewer than its size, is rewritten" | pack-half |
| pack-shared-too | "every extent that slots of exactly one volume point into, and that has twice its pointed-at blocks fewer than its size, is rewritten" | pack-shared |
| pack-no-shrink | "a new extent is allocated with exactly as many blocks as were pointed at, those blocks keep the order they were in, every pointer into the old extent moves to the block of the new one that its own block became" | pack-under |
| pack-desc-blocks | "a new extent is allocated with exactly as many blocks as were pointed at, those blocks keep the order they were in, every pointer into the old extent moves to the block of the new one that its own block became" | pack-under |
| cand-skip-drop | "After the pointer changes of an op, and not partway through them, the store settles" and "removes a volume and every pointer in it" | drop-cascade |
| pack-before-gone | "Within one op the write's line comes first, then a line for each extent given up in increasing extent number, then the rewrites in increasing number of the extent being rewritten" | line-order |
| pack-desc-id | "Within one op the write's line comes first, then a line for each extent given up in increasing extent number, then the rewrites in increasing number of the extent being rewritten" | pack-order |

## Shortcuts

| Strategy | Result |
|---|---|
| the shipped tree unchanged (the nop) | reward 0 in the container: it fails 29 of the 30 tests, and on the large programs it also runs past the clock |
| constant: the commonest number in the frozen answers, 4, for every question | `cheat-const-four.sh`, reward 0, caught by `cp-before` |
| positional: the drop question answered with what the volume is on | `cheat-own-as-use.sh`, reward 0, caught by `own-dup`; it moves 71 per cent of a generated population |
| the worked example replayed: the frozen answers carried and handed back for every program they match | `cheat-forge-key.sh`, reward 0; it passes all 27 enumerated programs and dies on the first drawn one |
| the answer key read out of the verifier at run time | `cheat-probe-answer-key.sh`, reward 0; `/tests/seal` is root-only 700 and the submitted half runs as uid 1002, which gets PermissionError on the model, on gt.json and on the directory listing |

## Tolerances

| Tolerance or limit | Independent implementation | Measured |
|---|---|---|
| `tests/test.sh:40` the 60 s clock on the graded run | `authoring/extent-share-pack/variants/ok-flat` and `authoring/extent-share-pack/variants/ok-lazy`, both written apart from the reference, and the naive pair under `authoring/extent-share-pack/slow` | reference 8.3 s for the whole graded set in a verifier container held to one CPU and 2048 MB, against the 60 s clock; both variants pass inside the clock in the container; `slow/scan` needs 50.8 s and `slow/walk` 31.9 s on one large program alone, so three of each carry the run past 60 s and both score 0 |
