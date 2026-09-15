# Instruction trace: page-window-reuse

Walked from the verifier toward the instruction (docs/INSTRUCTION-CONTRACT.md).
Re-run `python tools/tracecheck.py page-window-reuse` after any change to the
instruction, the tests, the model, the generator or the environment.

## Graded assertions

| Verifier site | What it grades | Instruction sentence |
|---|---|---|
| `tests/test_outputs.py:120` test_frozen_truth_matches_the_model | the sealed model still reproduces the frozen answers, so a drifted model cannot redefine correct; grades nothing the agent wrote | "The graded set is three programs of each of those sizes and four hundred and twenty-two smaller ones" |
| `tests/test_outputs.py:130` test_hand_case | the whole printed trace of each enumerated program, line for line, and that the program was not altered | "Every line is printed when it happens." |
| `tests/test_outputs.py:139` test_every_nonce_program_matches | the whole printed trace of every generated program, line for line | "Every line is printed when it happens." |
| `tests/test_outputs.py:158` test_every_family_is_represented | the generated population covers every family, including the two scale families | "The graded set is three programs of each of those sizes and four hundred and twenty-two smaller ones" |
| `tests/cases.py:30` case fill-hold-all | the rule this program pins | "While a prompt is being written its request holds every page of it, reused or written alike" |
| `tests/cases.py:43` case fill-lets-go | the rule this program pins | "the request keeps only the pages holding any of its first `a` tokens and the pages holding any of its last `s` tokens" |
| `tests/cases.py:56` case fill-short-keeps | the rule this program pins | "the request keeps only the pages holding any of its first `a` tokens and the pages holding any of its last `s` tokens" |
| `tests/cases.py:67` case fill-holds-middle | the rule this program pins | "While a prompt is being written its request holds every page of it, reused or written alike" |
| `tests/cases.py:79` case live-sink-stays | the rule this program pins | "the request keeps only the pages holding any of its first `a` tokens and the pages holding any of its last `s` tokens" |
| `tests/cases.py:92` case live-no-sink | the rule this program pins | "the request keeps only the pages holding any of its first `a` tokens and the pages holding any of its last `s` tokens" |
| `tests/cases.py:104` case live-window-edge | the rule this program pins | "That same rule is applied again each time it emits a token" |
| `tests/cases.py:118` case walk-whole | the rule this program pins | "the request takes that page and the walk goes on, whether or not somebody else is holding it" |
| `tests/cases.py:129` case walk-held | the rule this program pins | "the request takes that page and the walk goes on, whether or not somebody else is holding it" |
| `tests/cases.py:140` case walk-stops-at-gap | the rule this program pins | "The walk stops at the first page that is gone, whatever still sits below that one" |
| `tests/cases.py:155` case walk-part-page | the rule this program pins | "Only a complete page is ever reused." |
| `tests/cases.py:167` case rest-reusable | the rule this program pins | "the page stays in the pool as reusable if a walk can still reach it, and goes back to the free pool at once if it cannot" |
| `tests/cases.py:181` case rest-free-at-once | the rule this program pins | "the page stays in the pool as reusable if a walk can still reach it, and goes back to the free pool at once if it cannot" |
| `tests/cases.py:195` case rest-strand-frees | the rule this program pins | "those nobody holds going back to the free pool with it and those somebody holds staying until their holder lets go, never to be reached again, complete at the time or not" |
| `tests/cases.py:213` case back-oldest | the rule this program pins | "A page for a request to write is taken from the lowest numbered free page; when there is none, the pool takes back the page released longest ago" |
| `tests/cases.py:225` case back-strand | the rule this program pins | "those nobody holds going back to the free pool with it and those somebody holds staying until their holder lets go, never to be reached again, complete at the time or not" |
| `tests/cases.py:234` case back-under-part | the rule this program pins | "those nobody holds going back to the free pool with it and those somebody holds staying until their holder lets go, never to be reached again, complete at the time or not" |
| `tests/cases.py:251` case kick-newest | the rule this program pins | "the request that became resident most recently, or the request that asked for the page when none is resident, lets go of everything it holds and starts again from nothing later, keeping its place in arrival order" |
| `tests/cases.py:262` case kick-alone | the rule this program pins | "the request that became resident most recently, or the request that asked for the page when none is resident, lets go of everything it holds and starts again from nothing later, keeping its place in arrival order" |
| `tests/cases.py:270` case kick-ends-turn | the rule this program pins | "the request that became resident most recently, or the request that asked for the page when none is resident, lets go of everything it holds and starts again from nothing later, keeping its place in arrival order" |
| `tests/cases.py:283` case twin-hands-back | the rule this program pins | "When a page fills and the same tokens already sit below the same page, the request hands its own page back to the free pool and takes the one that is already there." |
| `tests/cases.py:302` case twin-other-prev | the rule this program pins | "When a page fills and the same tokens already sit below the same page, the request hands its own page back to the free pool and takes the one that is already there." |
| `tests/cases.py:322` case turn-decode-first | the rule this program pins | "A step decodes before it fills." |
| `tests/cases.py:333` case turn-page-edge | the rule this program pins | "A budget too small to reach the next boundary therefore takes nothing at all, and that ends the filling for that step" |
| `tests/cases.py:344` case turn-no-jump | the rule this program pins | "A budget too small to reach the next boundary therefore takes nothing at all, and that ends the filling for that step" |
| `tests/cases.py:355` case turn-reuse-free | the rule this program pins | "hands it the pages it can reuse, which costs no budget" |
| `tests/cases.py:366` case back-free-first | the rule this program pins | "A page for a request to write is taken from the lowest numbered free page; when there is none, the pool takes back the page released longest ago" |
| `tests/cases.py:377` case back-order-of-release | the rule this program pins | "lets them go in the order of the tokens they hold" |
| `tests/cases.py:390` case end-done-frees | the rule this program pins | "A request that has emitted its last token lets go of everything and prints `done <request>`." |
| `tests/cases.py:402` case end-stop-waiting | the rule this program pins | "A cancelled request lets go of everything it holds." |
| `tests/cases.py:414` case end-stop-part | the rule this program pins | "A cancelled request lets go of everything it holds." |
| `tests/cases.py:428` case end-stop-live | the rule this program pins | "A cancelled request lets go of everything it holds." |
| artifact `/app/kv/pool.py` | only the declared files are collected | "The files you may change are `/app/kv/pool.py`, `/app/kv/keep.py`, `/app/kv/live.py`, `/app/kv/fill.py`, `/app/kv/turn.py` and `/app/kv/put.py`. Nothing else." |
| artifact `/app/kv/keep.py` | only the declared files are collected | "The files you may change are `/app/kv/pool.py`, `/app/kv/keep.py`, `/app/kv/live.py`, `/app/kv/fill.py`, `/app/kv/turn.py` and `/app/kv/put.py`. Nothing else." |
| artifact `/app/kv/live.py` | only the declared files are collected | "The files you may change are `/app/kv/pool.py`, `/app/kv/keep.py`, `/app/kv/live.py`, `/app/kv/fill.py`, `/app/kv/turn.py` and `/app/kv/put.py`. Nothing else." |
| artifact `/app/kv/fill.py` | only the declared files are collected | "The files you may change are `/app/kv/pool.py`, `/app/kv/keep.py`, `/app/kv/live.py`, `/app/kv/fill.py`, `/app/kv/turn.py` and `/app/kv/put.py`. Nothing else." |
| artifact `/app/kv/turn.py` | only the declared files are collected | "The files you may change are `/app/kv/pool.py`, `/app/kv/keep.py`, `/app/kv/live.py`, `/app/kv/fill.py`, `/app/kv/turn.py` and `/app/kv/put.py`. Nothing else." |
| artifact `/app/kv/put.py` | only the declared files are collected | "The files you may change are `/app/kv/pool.py`, `/app/kv/keep.py`, `/app/kv/live.py`, `/app/kv/fill.py`, `/app/kv/turn.py` and `/app/kv/put.py`. Nothing else." |
| `tests/test.sh:27` a 60 s clock | the whole graded set runs inside it | "all of it has to get through inside 60 seconds" |
| `tests/seal/model.py:42-43` | sink(): how many pages the first `a` tokens cover | "the request keeps only the pages holding any of its first `a` tokens and the pages holding any of its last `s` tokens" |
| `tests/seal/model.py:45-49` | take(): the lowest numbered free page | "A page for a request to write is taken from the lowest numbered free page; when there is none, the pool takes back the page released longest ago" |
| `tests/seal/model.py:51-59` | give(): a page goes back to the free pool with everything it carried | "the page stays in the pool as reusable if a walk can still reach it, and goes back to the free pool at once if it cannot" |
| `tests/seal/model.py:61-74` | strip(): the strand of a take-back - free what nobody holds, put the rest out of reach | "those nobody holds going back to the free pool with it and those somebody holds staying until their holder lets go, never to be reached again, complete at the time or not" |
| `tests/seal/model.py:76-83` | oldest(): the reusable page released longest ago | "A page for a request to write is taken from the lowest numbered free page; when there is none, the pool takes back the page released longest ago" |
| `tests/seal/model.py:85-96` | rest(): the last holder leaving decides reusable against free | "the page stays in the pool as reusable if a walk can still reach it, and goes back to the free pool at once if it cannot" |
| `tests/seal/model.py:98-102` | grip(): a page taken up stops being reusable | "the request takes that page and the walk goes on, whether or not somebody else is holding it" |
| `tests/seal/model.py:104-110` | unlist(): a page out of reach leaves the index | "The walk stops at the first page that is gone, whatever still sits below that one" |
| `tests/seal/model.py:112-119` | back(): the take-back and the line it prints | "A take-back prints `gone <page> <pages back in the pool>`." |
| `tests/seal/model.py:121-130` | page(): free, then a take-back, then nothing | "A page for a request to write is taken from the lowest numbered free page; when there is none, the pool takes back the page released longest ago" |
| `tests/seal/model.py:132-133` | size(): a request's length is its placed prompt plus what it has emitted | "`ask r p o` brings in request `r` with prompt `p` and output `o`, each written as comma separated `count:token` runs, or `-` for none." |
| `tests/seal/model.py:135-140` | edge(): the lowest page outside the first `a` tokens residency still wants | "the request keeps only the pages holding any of its first `a` tokens and the pages holding any of its last `s` tokens" |
| `tests/seal/model.py:142-149` | shed(): what the window has moved past is let go, in token order | "That same rule is applied again each time it emits a token" |
| `tests/seal/model.py:151-156` | loose(): everything a request holds goes, in token order | "lets them go in the order of the tokens they hold" |
| `tests/seal/model.py:158-172` | write(): a new page is taken and sits below the page written before it | "A page is named by its tokens and the page before it." |
| `tests/seal/model.py:173-191` | write(): a completed page meets its own content below the same page | "When a page fills and the same tokens already sit below the same page, the request hands its own page back to the free pool and takes the one that is already there." |
| `tests/seal/model.py:193-206` | walk(): reuse from the start of the prompt, stopping at the first gap | "The walk stops at the first page that is gone, whatever still sits below that one" |
| `tests/seal/model.py:208-211` | settle(): the prompt is complete, the middle goes, the request is resident | "A request becomes resident in the step that completes its prompt and emits its first token in the next one." |
| `tests/seal/model.py:213-222` | feed(): a prompt is taken up once and what it reuses costs no budget | "hands it the pages it can reuse, which costs no budget" |
| `tests/seal/model.py:223-232` | feed(): the chunk ends on a page boundary, or writes nothing at all | "A budget too small to reach the next boundary therefore takes nothing at all, and that ends the filling for that step" |
| `tests/seal/model.py:233-245` | feed(): the fill line, in tokens | "A prompt taken up prints `fill <request> <reused> <written>`, both counted in tokens, and prints that line again in any later step in which it writes." |
| `tests/seal/model.py:247-263` | stall(): who is preempted, what it loses, where it goes back to | "the request that became resident most recently, or the request that asked for the page when none is resident, lets go of everything it holds and starts again from nothing later, keeping its place in arrival order" |
| `tests/seal/model.py:265-280` | step(): the decode phase, in residency order, inside the budget | "Each resident request emits one token, in the order the requests became resident, until the budget of `b` tokens for that step is spent" |
| `tests/seal/model.py:281-291` | step(): the fill phase, in arrival order, stopping at the first stall | "What is left of the budget goes to the waiting prompts in arrival order." |
| `tests/seal/model.py:293-299` | born(): a request arrives waiting, in arrival order | "`ask r p o` brings in request `r` with prompt `p` and output `o`, each written as comma separated `count:token` runs, or `-` for none." |
| `tests/seal/model.py:301-310` | ex(): the pool line sets the pool, page width, sink, window and budget | "`pool n w a s b` sets the pool to `n` pages of `w` tokens each, `a` sink tokens, `s` window tokens and a budget of `b` tokens per step." |
| `tests/seal/model.py:311-316` | ex(): ask and bulk bring requests in | "`bulk x k p t o` is the import shorthand that brings in `k` requests named `x0` upward" |
| `tests/seal/model.py:317-324` | ex(): stop cancels a request and prints nothing | "A cancelled request lets go of everything it holds." |
| `tests/seal/model.py:325-331` | ex(): the at query and its none | "The question prints `at <request> <token> <page>`, with `none` in place of the page when that request is not holding a page for that token, including when it has not got that far." |
| `tests/seal/model.py:333-341` | spread(): count:token runs | "`ask r p o` brings in request `r` with prompt `p` and output `o`, each written as comma separated `count:token` runs, or `-` for none." |
| `tests/seal/model.py:343-348` | expect(): one line per thing that happens, in order | "takes a program and prints a line for each thing that happens" |

## Readings

| Reading | Sentence or published example that rules it out | Case that separates it |
|---|---|---|
| live-no-sink | "the request keeps only the pages holding any of its first `a` tokens and the pages holding any of its last `s` tokens" | `back-free-first` |
| live-sink-pages | "`pool n w a s b` sets the pool to `n` pages of `w` tokens each, `a` sink tokens, `s` window tokens and a budget of `b` tokens per step." | `back-oldest` |
| live-window-frozen | "That same rule is applied again each time it emits a token" | `back-under-part` |
| live-window-edge | "the request keeps only the pages holding any of its first `a` tokens and the pages holding any of its last `s` tokens" | `fill-hold-all` |
| fill-lets-go-early | "While a prompt is being written its request holds every page of it, reused or written alike" | `fill-holds-middle` |
| walk-past-gap | "The walk stops at the first page that is gone, whatever still sits below that one" | `back-free-first` |
| walk-free-only | "the request takes that page and the walk goes on, whether or not somebody else is holding it" | `back-under-part` |
| rest-keeps-unreachable | "the page stays in the pool as reusable if a walk can still reach it, and goes back to the free pool at once if it cannot" | `rest-strand-frees` |
| rest-frees-always | "the page stays in the pool as reusable if a walk can still reach it, and goes back to the free pool at once if it cannot" | `back-free-first` |
| back-lowest-page | "A page for a request to write is taken from the lowest numbered free page; when there is none, the pool takes back the page released longest ago" | `back-oldest` |
| back-newest | "A page for a request to write is taken from the lowest numbered free page; when there is none, the pool takes back the page released longest ago" | `back-oldest` |
| back-one-page | "those nobody holds going back to the free pool with it and those somebody holds staying until their holder lets go, never to be reached again, complete at the time or not" | `back-oldest` |
| back-leaf-only | "those nobody holds going back to the free pool with it and those somebody holds staying until their holder lets go, never to be reached again, complete at the time or not" | `back-oldest` |
| grab-back-first | "A page for a request to write is taken from the lowest numbered free page; when there is none, the pool takes back the page released longest ago" | `back-free-first` |
| grab-highest-free | "A page for a request to write is taken from the lowest numbered free page; when there is none, the pool takes back the page released longest ago" | `back-free-first` |
| grab-no-back | "A page for a request to write is taken from the lowest numbered free page; when there is none, the pool takes back the page released longest ago" | `back-oldest` |
| kick-oldest | "the request that became resident most recently, or the request that asked for the page when none is resident, lets go of everything it holds and starts again from nothing later, keeping its place in arrival order" | `kick-ends-turn` |
| kick-carries-on | "the request that became resident most recently, or the request that asked for the page when none is resident, lets go of everything it holds and starts again from nothing later, keeping its place in arrival order" | `kick-ends-turn` |
| kick-keeps-work | "the request that became resident most recently, or the request that asked for the page when none is resident, lets go of everything it holds and starts again from nothing later, keeping its place in arrival order" | `fill-holds-middle` |
| turn-past-edge | "A budget too small to reach the next boundary therefore takes nothing at all, and that ends the filling for that step" | `back-under-part` |
| turn-queue-jump | "A budget too small to reach the next boundary therefore takes nothing at all, and that ends the filling for that step" | `turn-no-jump` |
| turn-fill-first | "A step decodes before it fills." | `back-free-first` |
| turn-reuse-costs | "hands it the pages it can reuse, which costs no budget" | `fill-holds-middle` |
| twin-keeps-own | "When a page fills and the same tokens already sit below the same page, the request hands its own page back to the free pool and takes the one that is already there." | `twin-hands-back` |
| order-newest-first | "lets them go in the order of the tokens they hold" | `back-order-of-release` |

## Shortcuts

| Strategy | Result |
|---|---|
| the shipped tree unchanged (the nop) | reward 0; 27 of 33 tests fail, 6 pass |
| a constant: the most common line of the ground truth for every program | reward 0; no enumerated program's trace is a repeated constant, and the fill, gone and at lines carry per-program numbers |
| positional: print nothing at all | reward 0; every enumerated program prints at least one line, and 24 of the 32 print a fill line on their first step |
| the worked example replayed: the trace of `small.txt` for every program | reward 0; it matches only `small.txt`, one program of 426 |
| the previous revision of the reference (the shipped tree, six wrong readings) | reward 0; this is the nop, and the six readings are cheats `live-no-sink`, `walk-past-gap`, `back-lowest-page`, `back-one-page`, `turn-past-edge`, `turn-fill-first`, `twin-keeps-own` |
| the frozen answers for every enumerated program, replayed (cheat `forge-from-truth`) | reward 0; passes all 32 enumerated programs and fails the 396 it could not have seen |

## Tolerances

| Tolerance or limit | Independent implementation | Measured |
|---|---|---|
| the 60 second wall clock on the worker (`tests/test.sh:9`) | `authoring/page-window-reuse/variants/ok-heap` and `variants/ok-kids`, both written apart from the reference, and the three naive-but-correct families under `authoring/page-window-reuse/slow/` | reference 5.5 s over the whole graded set; ok-heap and ok-kids agree with the model over 200 generated programs each; residency recomputed per page 110 s, the oldest release by scanning 144 s, the strand by sweeping the page table 203 s |
