# Instruction trace: stale-line-spin

Walked from the verifier toward the instruction (docs/INSTRUCTION-CONTRACT.md). Cite the
instruction word for word in double quotes, four words or more. Write NOT STATED where it
says nothing, then write the sentence or stop grading it. Split each model row into one
row per rule it applies, citing its lines. Check with `python tools/tracecheck.py stale-line-spin`.

Rewalked in full on 2026-09-23 for easiness recovery 1: the sealed model was rebuilt around
per-multiprocessor plans, so every model row below was re-derived from the current file rather
than carried over, and the sum rules, the twelve sum cases, the eleven new readings and the new
large kind were walked for the first time.

The cold-reader pass was run by the author, mechanically, and is recorded as author-run: every
printed token was listed, every model branch that decides it, and the four clusters put to each
(bases, strict against non-strict, ties, empty and zero). Each decision is answered below by a
quote or by the worked example. The one decision prose leaves loose - whether a block that
reaches its spin during cycle t already sits at it at t - is settled by the example, where block
2 issues `out r0` at 5, sits at its spin from 6, and the launch prints `hang 6`. For the sums the
questions were: which line comes first (the line that holds word a), how many issues (n, one
line each), what one issue reads (the words `ld.ca` or `ld.cg` would read, from the same place,
with the same fill or drop), when rd is written (at the n-th issue), whether a summing block is
ready (yes) and whether it counts toward a hang (no); each has its sentence below.

## Graded assertions

| Verifier site | What it grades | Instruction sentence |
|---|---|---|
| `tests/test_outputs.py:121` test_frozen_answers_are_the_models | the sealed side agrees with itself before grading; no agent-facing rule, it fails only on a verifier fault | "There are 42 fixed launches and 369 generated fresh for the run" |
| `tests/test_outputs.py:129` test_hand_launch | every hand launch prints exactly its frozen lines | "A launch that raises or prints one wrong line fails the run" |
| `tests/test_outputs.py:135` test_generated_launches | every generated launch prints exactly the model's lines, all or nothing | "A launch that raises or prints one wrong line fails the run" |
| `tests/test_outputs.py:148` test_generated_set_covers_every_family | the generated set holds every pattern, nine small and three large | "40 of each of nine patterns" |
| `tests/worker.py:58` import once, `run` per launch, one process | state must not leak between launches | "Grading imports `/app/run_launch.py` once and calls its `run` on every launch in turn" |
| `tests/worker.py:68` a raising launch records no lines | an exception is a wrong launch | "A launch that raises or prints one wrong line fails the run" |
| `tests/cases.py:54` case plain-apart | exact cycles on unshared lines: placement, first issue at the placing cycle, rotation | "A block placed at cycle t can issue at t" |
| `tests/cases.py:69` case place-most-free | the next block goes to the multiprocessor with most free slots, not number mod S | "goes to the multiprocessor with the most free slots at that moment" |
| `tests/cases.py:82` case place-spread | at the start blocks go one to each multiprocessor, lower number first on ties | "ties to the lower number, into its lowest free slot" |
| `tests/cases.py:90` case place-next-cycle | an exit frees its slot from the next cycle, and the successor issues at once | "A slot whose block exited at cycle u is free from cycle u+1" |
| `tests/cases.py:97` case turn-after-last | each multiprocessor issues from the slot after the last issuer, wrapping | "from the first ready block in slot order after the slot that issued last on that multiprocessor" |
| `tests/cases.py:107` case turn-spinner | a spinning block keeps its turn and delays its neighbour | "A block at a spin or a sum is ready" |
| `tests/cases.py:125` case sm-order | a store on multiprocessor 0 is seen by 1 in the same cycle | "so a store on multiprocessor 0 is seen by multiprocessor 1 in the same cycle" |
| `tests/cases.py:139` case work-wake | work of v issued at t makes the block ready at t+v | "It issues nothing more before cycle u+x" |
| `tests/cases.py:151` case fill-whole-line | a fill copies four words as they stand, a neighbour word read later is old | "it copies the whole line from global memory as it stands at that moment" |
| `tests/cases.py:169` case stale-elsewhere | a store on one multiprocessor leaves another's copy old | "but it never brings a line in and other caches are left as they were" |
| `tests/cases.py:188` case store-own-copy | a store updates the storer's own cached copy | "if the cache of its multiprocessor holds the line, the word in that copy" |
| `tests/cases.py:201` case store-no-fill | a store that misses does not fill | "it never brings a line in" |
| `tests/cases.py:218` case inherit-line | a block placed later reads the stale line its predecessor fetched | "blocks arriving and leaving never empty it" |
| `tests/cases.py:241` case fifo-drop | the line filled earliest goes, however recently it was hit | "first dropping the held line that was filled earliest if C lines are already held" |
| `tests/cases.py:264` case cg-drops-own | a bypassing load drops its own multiprocessor's copy | "It drops the line from the cache of its own multiprocessor if it is there" |
| `tests/cases.py:282` case cg-leaves-others | a bypassing load leaves other copies alone | "Other caches keep theirs" |
| `tests/cases.py:301` case atom-no-cache | an atomic leaves the issuer's own copy as it was | "The atomic `atom.add` works on global memory alone and never reads, fills, updates or drops a cached line" |
| `tests/cases.py:314` case fence-own | a fence empties only the issuer's cache | "A `fence` empties the cache of its own multiprocessor" |
| `tests/cases.py:336` case fence-refresh | after a fence the next cached load fetches again | "A `fence` empties the cache of its own multiprocessor" |
| `tests/cases.py:356` case spin-cg-store | a bypassing spin sees a store made on another multiprocessor | "the load that `ld.ca` or `ld.cg` would do, into rd" |
| `tests/cases.py:371` case spin-tests | lt is strict, ne is not-equal, the loaded value on the left | "for equal, not equal, less than and at least, with the loaded value on the left" |
| `tests/cases.py:393` case spin-evicted | a stale spinner is released when a neighbour's fill pushes its line out | "first dropping the held line that was filled earliest if C lines are already held" |
| `tests/cases.py:412` case spin-dropped | a stale spinner is released when a neighbour's bypassing spin drops the line | "It drops the line from the cache of its own multiprocessor if it is there" |
| `tests/cases.py:436` case spin-fenced | a stale spinner is released when a neighbour fences | "A `fence` empties the cache of its own multiprocessor" |
| `tests/cases.py:454` case skip-rotation | after a long all-failing stretch the rotation is where one issue per cycle leaves it | "make one attempt each time they issue" |
| `tests/cases.py:472` case skip-not-frozen | a stretch whose spins miss is stepped, and its misses change what the others read | "A hit changes nothing, not even the order lines will be dropped in" |
| `tests/cases.py:499` case sum-issues | a sum takes n issues of its block and shares the rotation with its neighbours | "read n lines, one each time they issue" |
| `tests/cases.py:519` case sum-start-line | a sum starts at the whole line holding its address, not at the word | "first the line that holds word a, then the next line up" |
| `tests/cases.py:533` case sum-stale-copy | a cached sum adds a stale copy; a bypassing one reads memory, drops the copy, and a cached one after it fetches | "Each issue reads its line the way `ld.ca` or `ld.cg` would read a word of it, with the same effect on the cache" |
| `tests/cases.py:554` case sum-fills | a cached sum fills every line it misses, the earliest fill dropped first | "with the same effect on the cache" |
| `tests/cases.py:576` case sum-cg-no-fill | a bypassing sum fills nothing, so it pushes no line out | "with the same effect on the cache" |
| `tests/cases.py:596` case sum-releases-spinner | a stale spinner is let go at the exact fill of a neighbour's sum that evicts its line | "first dropping the held line that was filled earliest if C lines are already held" |
| `tests/cases.py:619` case sum-cg-releases | a stale spinner is let go when a neighbour's bypassing sum reaches its line and drops it | "It drops the line from the cache of its own multiprocessor if it is there" |
| `tests/cases.py:642` case sum-race-order | a store lands in a sum only if made before the sum's issue on that line, multiprocessor order deciding within a cycle | "Every instruction takes full effect before the next one issues" |
| `tests/cases.py:663` case sum-trailing | a sum behind another on the same lines reads the leader's copies | "Each issue reads its line the way `ld.ca` or `ld.cg` would read a word of it" |
| `tests/cases.py:688` case sum-evicts-prefetch | a prefetched stale line survives to the sum on a quiet multiprocessor and is pushed out first where a neighbour streams | "first dropping the held line that was filled earliest if C lines are already held" |
| `tests/cases.py:714` case sum-interrupted | blocks waking mid-sum join the rotation and stretch the sum | "A block at a spin or a sum is ready" |
| `tests/cases.py:732` case sum-not-spin | no hang while a block is still summing; the hang is dated from when the last sum ends | "A block at a sum does not sit at a spin" |
| `tests/cases.py:750` case hang-residency | a barrier larger than the device hangs with blocks never placed | "Then `left n` gives the number of blocks never placed" |
| `tests/cases.py:760` case hang-stale | a cached spin nothing refreshes hangs | "Nothing keeps the caches in agreement with global memory or with each other" |
| `tests/cases.py:779` case hang-thrash | spinners that keep pushing each other out, all failing, hang from the start of the stretch | "The hang is the earliest such t" |
| `tests/cases.py:790` case hang-after-pass | an attempt that succeeds inside an all-spin stretch moves the hang later | "no attempt at or after t succeeds" |
| artifact `/app/sim/line.py` | only the declared files are collected | "The files you may change are `/app/sim/line.py`, `/app/sim/mem.py`, `/app/sim/place.py`, `/app/sim/turn.py`, `/app/sim/step.py` and `/app/sim/clock.py`" |
| artifact `/app/sim/mem.py` | only the declared files are collected | "The files you may change are `/app/sim/line.py`, `/app/sim/mem.py`, `/app/sim/place.py`, `/app/sim/turn.py`, `/app/sim/step.py` and `/app/sim/clock.py`" |
| artifact `/app/sim/place.py` | only the declared files are collected | "The files you may change are `/app/sim/line.py`, `/app/sim/mem.py`, `/app/sim/place.py`, `/app/sim/turn.py`, `/app/sim/step.py` and `/app/sim/clock.py`" |
| artifact `/app/sim/turn.py` | only the declared files are collected | "The files you may change are `/app/sim/line.py`, `/app/sim/mem.py`, `/app/sim/place.py`, `/app/sim/turn.py`, `/app/sim/step.py` and `/app/sim/clock.py`" |
| artifact `/app/sim/step.py` | only the declared files are collected | "The files you may change are `/app/sim/line.py`, `/app/sim/mem.py`, `/app/sim/place.py`, `/app/sim/turn.py`, `/app/sim/step.py` and `/app/sim/clock.py`" |
| artifact `/app/sim/clock.py` | only the declared files are collected | "The files you may change are `/app/sim/line.py`, `/app/sim/mem.py`, `/app/sim/place.py`, `/app/sim/turn.py`, `/app/sim/step.py` and `/app/sim/clock.py`" |
| `tests/worker.py:39-48` pristine tree with six files laid over it | anything else under /app is discarded, frozen files restored | "The rest of `/app` is replaced by a pristine copy before grading" |
| `tests/test.sh:39` a 60 s clock | the whole graded set in one run inside 60 seconds | "So does taking more than 60 seconds for all of it" |
| `environment/app_src/run_launch.py:7` `say.lines(launch, *clock.run(launch))` | the frozen interface: what clock.run returns | "must return `(blocks, hang, left, gm)`" |
| `environment/app_src/sim/say.py:16-18` stuck blocks read `pc`, `reg`, `at is not None` | fields the printer reads | "and `pc` and `reg` for a block stuck at a spin, `at` staying `None` for a block never placed" |
| `environment/app_src/sim/load.py:103-107` sum operands | a sum takes a positive literal count, the parser refuses others | "where n is a positive integer" |
| `tests/seal/model.py:81` BadLaunch | a launch the parser refuses; no graded launch is refused | "Every graded launch ends one way or the other" |
| `tests/seal/model.py:85-88` _reg | registers r0 to r7 | "Each block has registers r0 to r7. They start at 0" |
| `tests/seal/model.py:91-100` _value | an operand is a register, an integer or a special | "An operand is a register, an integer, or `%bid`" |
| `tests/seal/model.py:103-113` _address | `[rN+k]`, `[rN]`, `[k]` | "An address is `[rN+k]`, `[rN]` or `[k]`, meaning the value of rN plus k" |
| `tests/seal/model.py:124-135` parse, header lines | dev, grid, mem, show | "lines `mem a v` that set word a of global memory to v, with every other word starting at 0" |
| `tests/seal/model.py:142-147` parse, labels | label lines | "with `name:` lines as labels" |
| `tests/seal/model.py:174-180` parse, spin operands | a spin never reads its own destination | "A spin never uses rd for its address or for x" |
| `tests/seal/model.py:161-165` parse, mod | mod takes a positive literal | "`mod rd x k`, which takes a positive literal k and gives 0 to k-1" |
| `tests/seal/model.py:181-185` parse, sum | a sum's count is a positive literal | "where n is a positive integer, read n lines" |
| `tests/seal/model.py:287-297` Machine.val | %bid, %sm, %nb | "`%sm` (the multiprocessor it was placed on) or `%nb` (G)" |
| `tests/seal/model.py:299-301` Machine.ea | effective address | "the value of rN plus k" |
| `tests/seal/model.py:315-317` Machine.words | four-word lines | "Line k of memory is words 4k to 4k+3" |
| `tests/seal/model.py:322-325` Machine.read_line, cached hit | a hit answers from the copy and changes nothing | "A hit changes nothing, not even the order lines will be dropped in" |
| `tests/seal/model.py:326-327` Machine.read_line, drop on a full cache | the line filled earliest goes first | "first dropping the held line that was filled earliest if C lines are already held" |
| `tests/seal/model.py:328-330` Machine.read_line, fill | four words from memory as they stand | "it copies the whole line from global memory as it stands at that moment" |
| `tests/seal/model.py:331-335` Machine.read_line, bypassing | memory, and the own copy dropped | "The bypassing load `ld.cg` answers from global memory. It drops the line from the cache of its own multiprocessor if it is there" |
| `tests/seal/model.py:367-380` Machine.issue, arithmetic | mov, add, sub, mul, slt, mod | "`slt rd x y`, which sets rd to 1 if x < y and to 0 otherwise" |
| `tests/seal/model.py:369-370` Machine.issue, operands first | operands are read before the write | "Every instruction reads all its operands before it writes anything" |
| `tests/seal/model.py:381-384` Machine.issue, ld | loads into rd | "Memory is reached through the loads `ld.ca rd [a]` and `ld.cg rd [a]`" |
| `tests/seal/model.py:385-391` Machine.issue, st | memory and the own copy if held | "The store `st` writes global memory and, if the cache of its multiprocessor holds the line, the word in that copy" |
| `tests/seal/model.py:392-397` Machine.issue, atom.add | old value to rd, memory only | "adds x to the word in global memory and sets rd to the value it had before" |
| `tests/seal/model.py:398-399` Machine.issue, fence | own cache emptied | "A `fence` empties the cache of its own multiprocessor" |
| `tests/seal/model.py:400-409` Machine.issue, spin | one attempt, rd written, advance only on success | "the block moves on to the next instruction only if the loaded value c x holds" |
| `tests/seal/model.py:410-415` Machine.issue, sum start | the first issue starts at the line holding the address | "first the line that holds word a, then the next line up, and so on" |
| `tests/seal/model.py:416-419` Machine.issue, sum line | each issue reads one line as the matching load would and adds its four words | "and adds the line's four words to a running total" |
| `tests/seal/model.py:420-424` Machine.issue, sum end | the n-th issue writes the total to rd and moves on; before it the block stays | "The issue that reads the n-th line writes the total to rd and moves the block on. Until then the block stays at the sum" |
| `tests/seal/model.py:60-65` CMP | the four comparisons | "Here c is `eq`, `ne`, `lt` or `ge`, for equal, not equal, less than and at least" |
| `tests/seal/model.py:425-429` Machine.issue, work | busy until t + max(1, v) | "or u+1 if x is below 1" |
| `tests/seal/model.py:430-439` Machine.issue, branches | bra, brz, brnz | "with `brz x L` jumping there only when x is 0 and `brnz x L` only when it is not" |
| `tests/seal/model.py:440-441` Machine.issue, out | values printed in order | "`out x` appends x to the values the block prints" |
| `tests/seal/model.py:442-449` Machine.issue, exit | exit cycle recorded, slot freed next cycle | "u the cycle it exited" |
| `tests/seal/model.py:642-669` Machine.place | frees, then most-free placement, ties low, lowest slot | "while a slot is free and blocks remain, the lowest-numbered block not yet placed goes to the multiprocessor with the most free slots" |
| `tests/seal/model.py:455-456` Machine.ready | placed, not exited, not busy; a spinning or summing block included | "A block is ready when it is placed, has not exited and is not busy" |
| `tests/seal/model.py:701-708` Machine.run, wake first | work that has run out ends before placement | "First, blocks whose work has run out are ready again" |
| `tests/seal/model.py:709-714` Machine.run, placement then end | a launch ends when all blocks exited | "A launch ends when every block has exited, or when it hangs" |
| `tests/seal/model.py:715-730` Machine.run, hang | all spinning (a summing block is not), none busy, no success from the phase start | "It hangs at cycle t when, from t on, every placed block that has not exited sits at a spin with none of them busy, and no attempt at or after t succeeds" |
| `tests/seal/model.py:754` Machine.run, success resets | a success moves the hang later | "The hang is the earliest such t" |
| `tests/seal/model.py:468-576` Machine.make_plan | exact; decides no token by itself, only how many cycles are carried at once: each issue in a plan is one the stepped machine would make | "make one attempt each time they issue" |
| `tests/seal/model.py:578-628` Machine.settle | a carried stretch leaves each block, each cache and each rotation where one issue per cycle would | "read n lines, one each time they issue" |
| `tests/seal/model.py:630-638` Machine.observe | a store is let into a carried sum only at its place in cycle and multiprocessor order | "Every instruction takes full effect before the next one issues" |
| `tests/seal/model.py:739-756` Machine.run, issue order | multiprocessors in number order, one instruction each | "the multiprocessors in number order each issue at most one instruction" |
| `tests/seal/model.py:261` Machine, rotation start | the first issue starts at slot 0 | "Before the first issue on a multiprocessor, slot 0 comes first" |
| `tests/seal/model.py:747-753` Machine.run, rotation state | the rotation keeps the slot | "The rotation remembers the slot, not the block in it" |
| `tests/seal/model.py:259` Machine, caches start empty | no line is held before the first fill | "Each multiprocessor has its own cache, which starts empty" |
| `tests/seal/model.py:259` Machine, cache per multiprocessor | caches outlive blocks | "belongs to the multiprocessor, not to the blocks on it" |
| `tests/seal/model.py:783-790` Machine.report, blk | exited blocks in block order | "for each block that exited, in block order, where s is its multiprocessor" |
| `tests/seal/model.py:790-798` Machine.report, hang lines | hang, stuck blocks, left | "Then comes `spin b sm s at t on a` and its out values for each placed block that had not exited" |
| `tests/seal/model.py:799-801` Machine.report, mem | shown words from global memory | "`mem a v` is printed for each shown address, in the order given, from global memory at the end" |
| `tests/seal/model.py:783-802` Machine.report, nothing more | the report holds only these lines | "Nothing else is printed" |
| `tests/seal/model.py:804-808` expect | the whole report, compared line for line | "the output must be exactly these seven lines, in this order" |

## Readings

| Reading | Sentence or published example that rules it out | Case that separates it |
|---|---|---|
| coherent | "Nothing keeps the caches in agreement with global memory or with each other" | fill-whole-line |
| per-block-cache | "belongs to the multiprocessor, not to the blocks on it" | inherit-line |
| store-broadcast | "but it never brings a line in and other caches are left as they were" | fill-whole-line |
| store-leaves-copy | "if the cache of its multiprocessor holds the line, the word in that copy" | store-own-copy |
| store-allocates | "it never brings a line in" | store-no-fill |
| atom-updates-own | "The atomic `atom.add` works on global memory alone and never reads, fills, updates or drops a cached line" | atom-no-cache |
| lru | "A hit changes nothing, not even the order lines will be dropped in" | fifo-drop |
| cg-keeps | "It drops the line from the cache of its own multiprocessor if it is there" | cg-drops-own |
| cg-drops-all | "Other caches keep theirs" | cg-leaves-others |
| fence-all | "A `fence` empties the cache of its own multiprocessor" | fence-own |
| fence-noop | "A `fence` empties the cache of its own multiprocessor" | fence-refresh |
| line-word | "Line k of memory is words 4k to 4k+3" | fill-whole-line |
| sum-one-issue | "read n lines, one each time they issue" | sum-issues |
| sum-coherent | "Each issue reads its line the way `ld.ca` or `ld.cg` would read a word of it, with the same effect on the cache" | sum-stale-copy |
| sum-no-fill | "with the same effect on the cache" | sum-fills |
| sum-cg-keeps | "It drops the line from the cache of its own multiprocessor if it is there" | sum-stale-copy |
| sum-word-issues | "and adds the line's four words to a running total" | sum-issues |
| sum-first-issue | "Each issue reads its line the way `ld.ca` or `ld.cg` would read a word of it" | sum-releases-spinner |
| sum-last-issue | "Each issue reads its line the way `ld.ca` or `ld.cg` would read a word of it" | sum-releases-spinner |
| sum-fills-at-end | "with the same effect on the cache" | sum-releases-spinner |
| sum-is-spin | "A block at a sum does not sit at a spin" | sum-stale-copy |
| lane-late-read | "Each issue reads its line the way `ld.ca` or `ld.cg` would read a word of it" | sum-race-order |
| lane-same-cycle | "so a store on multiprocessor 0 is seen by multiprocessor 1 in the same cycle" | sum-race-order |
| place-mod | "goes to the multiprocessor with the most free slots at that moment" | place-most-free |
| place-first-free | "goes to the multiprocessor with the most free slots at that moment" | plain-apart |
| free-same-cycle | "A slot whose block exited at cycle u is free from cycle u+1" | place-most-free |
| placed-next-cycle | "A block placed at cycle t can issue at t" | plain-apart |
| rotate-from-zero | "from the first ready block in slot order after the slot that issued last on that multiprocessor" | plain-apart |
| sm-reverse | "the multiprocessors in number order each issue at most one instruction" | sm-order |
| work-plus-one | "It issues nothing more before cycle u+x" | plain-apart |
| lt-inclusive | "for equal, not equal, less than and at least, with the loaded value on the left" | spin-tests |
| cmp-reversed | "for equal, not equal, less than and at least, with the loaded value on the left" | spin-cg-store |
| park-spinners | "A block is ready when it is placed, has not exited and is not busy" | turn-spinner |
| skip-any-spin | "A hit changes nothing, not even the order lines will be dropped in" | hang-after-pass |
| skip-no-rotate | "make one attempt each time they issue" | spin-evicted |
| hang-no-store | "no attempt at or after t succeeds" | hang-after-pass |
| hang-at-detect | "The hang is the earliest such t" | hang-thrash |
| hang-last-start | "The hang is the earliest such t" | hang-thrash |

`work-zero-skips` (busy until u+x with no floor at one) was built, scored 1 on every hand case and
every generated launch, and was dropped as a reading: a block issues at most one instruction a
cycle, so being ready at or before u is being ready at u+1. It is the rule, not a reading of it.

The case column names the first hand case that separates each reading, as tools/readingcheck.py
reports it (38 of 38 separated, none blind, none equivalent). Readings whose rules the fast path does not model (the cache readings, and
the sum readings that change what one issue reads) are built without plans and step every cycle:
they are caught by their hand case before time matters.

## Shortcuts

| Strategy | Result |
|---|---|
| the shipped tree unchanged (nop) | host emulation: see the cheat report in STATE.md, recorded after the sweep |
| constant: the most common value of every graded field | `const-none` (every block on multiprocessor 0, placed and ended at cycle 0, no hang, memory as loaded): see STATE.md |
| positional: always the first candidate | `pos-serial` (one block at a time on multiprocessor 0, in number order): see STATE.md |
| the worked example's output replayed | the example is not graded; `forge-hand` replays all 42 frozen hand answers keyed by launch and runs the shipped engine otherwise: see STATE.md |
| the delivered plan, which the easiness probe converged on | `old-plan` treats every sum as doing nothing: fails every sum hand case |
| correct but stepping every line of every sum | `literal-sums` (the delivered plan with sums stepped): over 450 s on one `persistent_reduce` launch against the 60 s clock for the whole set |
| correct but carrying streams only while the whole device is quiet | `device-bulk`: 387.5 s on one `persistent_reduce` launch |

## Tolerances

| Tolerance or limit | Independent implementation | Measured |
|---|---|---|
| `tests/test.sh:39` a 60 s clock | `authoring/stale-line-spin/variants/ok-model/clock.py`, the sealed model's own clock written apart from `solution/`, and `authoring/stale-line-spin/variants/ok-edges/clock.py`, a different fast path that never computes when a cached line goes | host, whole 411-launch set: reference 13.4 s, ok-edges 13.8 s, ok-model 25.6 s; container figures at --cpus=1 in STATE.md |
