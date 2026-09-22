# Task state - stale-line-spin

Working memory for this task. Updated after every stage. The next session starts with no
memory of this one; anything not written here is lost.

## Current stage

`Stage 7 - Gates and delivery` (Stage 1 gates passed 2026-09-22: originality 100, difficulty 100;
built tree re-measured 2026-09-22: difficulty 100)

## Assistant's assigned role

A GPU kernel engineer who writes and debugs inter-block synchronisation in ML kernels -
split-K and stream-K fixups, last-block reductions, persistent tile queues, grid-wide
barriers - and who keeps a cycle model of the device's memory hierarchy to reproduce the
heisenbugs those patterns produce: stale reads through the per-multiprocessor L1, blocks
that inherit what an earlier block fetched, spin-waits that only succeed because something
else evicted a line, and launches that hang because the block being waited for can never be
made resident.

## Source repository (repo-based tasks only)

- Repo URL: none - idea-based task. The seed prompt carried no seed; the label and mechanism
  were chosen after reading the ledger and every task branch (see Decisions).
- Task shape chosen: not applicable (no repository).

## Task summary

`/app` is a cycle model of one kernel launch on a GPU: a device of S multiprocessors, each
able to hold R blocks at once and each with its own cache of C four-word lines over global
memory; a dispatcher that places blocks as residency slots free up; a per-multiprocessor
issue rotation; and a small instruction set with cached and bypassing loads, stores,
atomics, fences, spin-waits and timed work. `/app/run_launch.py` runs a launch file and
prints, for every block, where it ran, when it was placed and when it exited and what it
printed; when a launch hangs, the cycle it hung and every stuck block with the word it spins
on; and chosen words of final memory. The shipped model is the coherent-machine model most
engineers carry in their heads, and it is wrong in six files. The agent repairs the six
files so that every launch prints exactly what the stated machine does, and so that the
graded set (large launches included) finishes inside 60 seconds.

## Why it is hard

The difficulty is not the amount of code. It is that the model every engineer carries is a
coherent one, and that the natural way to make the simulation fast is exactly the way that
breaks the incoherent one.

- Expert time estimate: 10 hours
- Why a frontier agent cannot one-shot the plan (the strategic answer - required): its plan comes from the coherent-machine prior - answer every load from one array or from a cache kept in step, send blocks round robin, and, when the big launches crawl, park each spinning block until something stores to the word it watches. Two stated rules take that plan apart at different stages: the caches are per multiprocessor, incoherent and outlive their blocks, so values depend on placement history; and a spin attempt is a load, so fills, bypass drops and fences on the spinner's own multiprocessor release it without any store, which means the fast path and the hang test both have to be rebuilt around whether an attempt changes its cache.
- Tactics making that true (docs/DIFFICULTY.md - prong A poison / prong B withholding / prong C late failure): A1 (coherent-memory prior, per-block cache prior, round-robin dispatch prior, spin-as-wait prior), A2 (the brief never names coherence, staleness, livelock or when time may be skipped), B2 (placement, rotation, fill order, bypass drops, store updates, atomic bypass, fences, spin attempts, work and exit timing interact in one trace), C1 (ordinary launches must still be cycle-exact; answering from global memory, never skipping and never hanging all fail somewhere), C2 (no expected output ships; the only runner is the model being repaired), C3 (thousands of blocks in long work while others spin; a stepper that only skips idle cycles never skips), C4 (exact all-or-nothing grading over hand launches and hundreds of nonce-generated ones), plus the guard (six collected files, pristine parser/reporter/runner).
- Assistant's attack on the plan (its first plan, and where that plan is wrong): cold, my first plan is a cycle stepper with one cache per multiprocessor and spinners parked on the word they watch, woken by any store to it. The cache half of that plan is right only once caches are per multiprocessor, FIFO and kept across blocks; the parking half is wrong twice - a parked spinner no longer takes its turn, which moves every later cycle of its neighbours, and a spinner on a cached line is released by a neighbour's fill, a bypassing load or a fence on its own multiprocessor, none of which is a store to its word. My second plan (skip whenever every ready block is spinning) is still wrong wherever an attempt misses, because a miss fills and pushes out another spinner's line. I would not have committed to the correct frozen condition without first writing out what each attempt does to its cache.
- Estimated solves out of 8 (design for 1, the hard edge; the realized rate drifts up): 2 (range 1-3)
- Difficulty record score (tools/difficultycheck.py on authoring/<slug>/difficulty.toml, before Stage 2; every attempt's score and what changed): attempt 1, 2026-09-22, 100/100 IN BAND, one warning (gate not yet measured). No earlier attempt; the design was changed before the first record from "frozen when every ready block spins" to "frozen only when every attempt leaves its cache untouched" after the planning attack found the first version plannable in one shot.
- Difficulty score anchor (50 at first complete submission, approved by contributor): not set - no submission yet.
- Score history (date, score, what moved, and any pipeline re-anchor): 2026-09-22 originality 100, difficulty 100 (record only). 2026-09-22 difficulty 100 on the built tree (gate measured; shape 399 environment lines after two dead helpers were removed, 6 editable files, 391 reference lines by the tool's count, 41 cheats, 2 variants).
- Leak audit (docs/DIFFICULTY.md): the launch files carry only device shape, initial words and programs; no expected output, placement or cycle ships; the worked example in the brief was found by search (authoring/stale-line-spin/example_search.py) and, run against all 31 cheat trees that are not isolation probes, decides only three conventions the brief states outright (first issue in the placing cycle, a slot free the cycle after its exit, the loaded value on the left of a comparison) and the constant, positional and replay strategies, none of the cache, residency, skipping or hang readings; the engine prints only what the graded format prints (no per-cycle log that would show a fill, a drop or a skip); no helper exists that only the correct rules would call. Answer, re-checked on the built tree: nothing.
- Expert path, described step by step: (1) run the samples and read the engine end to end; (2) replace memory with a FIFO line cache per multiprocessor that outlives its blocks, with the stated fill, bypass-drop, store-update, atomic-bypass and fence rules; (3) fix placement (most free slots, ties to the lower number, slot free the cycle after exit) and the rotation (slot order after the last issuer, spinners take turns); (4) derive the frozen condition - every ready block is at a spin whose attempt fails and leaves its cache untouched - and skip to the next wake, advancing each rotation by the skipped cycles; (5) settle hangs from the same condition, stepping any unfrozen all-spinning stretch until it freezes, succeeds or repeats, and reporting the cycle it began; (6) time the large launches and diff the fast clock against a plain stepper on generated launches.
- Originality check: searched six queries (recorded in authoring/stale-line-spin/originality.toml). Found: Alglave et al. ASPLOS 2015 (stale L1 reads in message passing on real GPUs), Sorensen et al. OOPSLA 2016 (co-residency deadlock of inter-workgroup barriers), the GPGPU-Sim manual (atomics modelled as skipping L1), LightScan (ld.cg bypasses and evicts L1 lines), a dispatch study (placement by resource availability, not round robin). None states a complete model or computes placements, cycles, values or hangs for a launch. No twin.
- Distinctness record score: 2026-09-22 100/100 DISTINCT (tags overlap nothing in the ledger, substrate new, mechanism sentence nearest ledger entry alias-settle-report at cosine 0.14). Crowded archetype named: occupancy tuning (Kernels list), departure recorded.
- Nearest already-submitted task: guard-mark-unwind (ledger) - both are turn-taking execution models with an exact trace where waiters may never be released; all five surfaces separate (mechanism, substrate, graded output, failure mode, interaction). Also checked against every task on every remote branch (about seventy) and the nine per-label seed prompts: no GPU memory model anywhere; the Kernels seed (a warp execution model with divergence, barriers and bank conflicts) is intra-multiprocessor and grades barrier release steps and bank cycles, this is inter-multiprocessor and grades cache visibility, placement and hangs.

## Instruction contract (docs/INSTRUCTION-CONTRACT.md, read before anything else)

- Instruction trace (authoring/<slug>/trace.md; rows walked, NOT STATED left, tracecheck result): every test function, the 30 hand cases, the six artifacts, the worker's collection and import, the frozen interface, the 60 s clock and each rule of the sealed model split by line range; no NOT STATED row; tracecheck result recorded in the validation table below.
- Identifiability (readings enumerated, which survived the published evidence, what separated them): 27 wrong readings built as file sets from the reference (authoring/stale-line-spin/readings.py, the same files the cheats ship); every one is ruled out by a quoted sentence and failed by a named hand case (tools/readingcheck.py: 27 separated, 0 blind, 0 equivalent). One candidate, work-zero-skips (no floor at one cycle), survived everything and was proved the rule itself: a block issues at most once a cycle. The comparison conventions had no graded case until spin-tests was added (lt against at-most, operands reversed, ne against eq all separated).
- Shortcut strategies scored (nop, constant, positional, replayed example; score and cases matched): nop 0 (fails 17 of 30 hand cases, 253 of 326 generated); const-none 0 (fails all 30 and all 326); pos-serial 0 (fails 27 of 30 and all 326); forge-hand (frozen answers replayed by launch key, shipped engine otherwise) 0 - passes all 30 hand cases, fails 253 of 326 generated. The worked example is not in the graded set; replaying known answers is what forge-hand does for all 30 frozen ones.
- Independent implementation behind every tolerance and limit (path, measured headroom): the 60 s clock - authoring/stale-line-spin/variants/ok-heap (16.3-16.4 s) and ok-list (27.1-29.7 s), both written apart from solution/, plus the reference (10.4-11.4 s), each the whole 356-launch set in the verifier image at --cpus=1 (authoring/stale-line-spin/container_time.py). The per-cycle stepper (cheat slow-step) matches all 353 launches it reaches and has not finished the large chain launches after 240 s on the host.
- Undecided decisions from the cold-reader pass (author-run or fresh session; sentence or example added for each): author-run, mechanically (trace.md header). Sentences added for: the comparison order, the mod range, operands read before writes, the rotation remembering the slot not the block, an atomic touching no cache, the frozen interface and the fields say.py reads, one process for all launches. The one decision prose leaves loose - whether a block reaching its spin during cycle t sits at it at t - is settled by the worked example (hang 6, not 5).

## Verifier contract - FROZEN after Stage 2

- Collected: exactly `/app/sim/{line,mem,place,turn,step,clock}.py`; everything else under /app is
  the verifier's pristine copy (tests/pristine, synced by authoring/stale-line-spin/sync_pristine.py).
- Interface: `clock.run(launch)` returns `(blocks, hang, left, gm)`; frozen `say.py` prints.
- Graded set: the 30 hand launches in tests/cases.py against tests/seal/gt.json, and
  `gen.programs(nonce, 40)` - eight small families x 40 and two large x 3 = 326 - against the
  sealed model, nonce drawn in test.sh at grading time. Exact, all-or-nothing.
- Clock: the worker, all 356 launches in one process, under `timeout 60` at one CPU.
- Isolation: worker as uid 1002 via setpriv, own session, reaped by uid; /tests/seal and
  /logs/verifier chmod 700 before it runs; reward written 0 first, 1 only if both halves pass.
- Additive changes since freeze, each proved by build_gt.py leaving every frozen answer
  byte-identical: the spin-tests hand case (2026-09-22) - no rule changed, a stated rule gained a
  test.

## Machine model (frozen; the instruction states it)

Launch file: `dev S R C`, `grid G`, `mem A V` lines, `show A ...` lines, then `prog` and one
instruction per line with `name:` labels. Registers r0-r7 start at 0; `%bid`, `%sm`, `%nb`
read the block number, its multiprocessor and the grid size.

Each cycle t: (1) a block that issued `work v` at cycle u is ready again at u+max(1,v); (2) while a
slot is free and blocks remain, the lowest-numbered unplaced block goes to the
multiprocessor with the most free slots, ties to the lower number, into its lowest free
slot; a slot whose block exited at u is free from u+1; a block placed at t may issue at t;
(3) multiprocessors in number order issue at most one instruction each, from the first ready
block in slot order after the slot that issued last there (slot 0 first at the start), and
each instruction's effect is complete before the next multiprocessor issues.

Memory: global words default 0. Each multiprocessor caches at most C lines of four words
(line k = words 4k..4k+3). `ld.ca` answers from the cached line if present, else fills the
line with the four global words as they stand, dropping the line filled earliest when C
lines are present (hits do not reorder). `ld.cg` answers from global memory and drops the
line from its own multiprocessor's cache if present. `st` writes global memory and, if its
own multiprocessor caches the line, that copy of the word. `atom.add` returns the old global
word and adds, touching no cache. `fence` empties its own multiprocessor's cache. Caches
start empty and are never emptied by blocks arriving or leaving. `spin.ca` / `spin.cg` make
one attempt (the matching load into rd) per issue and move on when `rd cmp v` holds (`eq`,
`ne`, `lt`, `ge`). `work v` keeps the block busy for v cycles. `out v` appends to the block's
printed values. `exit` ends the block.

Hang: at cycle t if, from t on, every placed block that has not exited sits at a spin, none
is busy, and no attempt at or after t succeeds.

## Decisions and their reasons

- 2026-09-22, label: ML / Kernels. Evaluation and Kernels are the only labels no task uses in
  the ledger or on any of about seventy task branches; Kernels chosen because a GPU memory
  model is unmistakably kernel knowledge, while every Evaluation design found was either a
  public metric or bookkeeping a reviewer could call narrative (the alias-settle-report
  category rejection). The Kernels seed prompt (warp execution model) and the Evaluation
  seed (rerun report assembly) were deliberately not used: parallel sessions may run them,
  and the roster's async-copy pipeline was rejected because its graded output (when each
  wait releases) sits too close to the seed's barrier release steps.
- 2026-09-22, rejected designs (planning attack): CUDA graph replay pools (too long a
  contract), a fusion pass (public priority-fusion plans it), batch-dependent reduction bits
  (puzzle-like float emulation), collective matching (a direct simulation, one-shot plan),
  an async-copy race checker (vector clocks plan it in one shot), the same GPU model without
  cache capacity (spinners always freeze, so the fast path is one-shot).
- Blocks are single warps: the phenomenon is multiprocessor-level (L1 sharing across blocks),
  and leaving out intra-block barriers keeps this task away from the Kernels seed.
- `spin` is an instruction rather than a loop of loads and branches, so that "spinning" is a
  stated state and the hang definition is decidable from the stated rules.
- 2026-09-22, work-zero-skips dropped from the cheat set: it scored 1 on everything because a
  block issues at most once a cycle, so ready at or before u is ready at u+1. The brief keeps the
  floor sentence for completeness; no assertion rests on it.
- 2026-09-22, spin-tests added: the graded set used only `eq` and `ge`, so `lt` and `ne` were
  sentences with no test. One hand case now separates lt-inclusive, cmp-reversed and ne-as-eq.
- 2026-09-22, placed-next-cycle rebuilt: the first cheat delayed placed blocks without scheduling
  their wake and was caught by an IndexError, not by a wrong answer; it now schedules the wake and
  plain-apart fails it on output.
- 2026-09-22, readings.py follows the kit contract (REFERENCE, READINGS as file sets taken from
  emit.py's builders with the writer swapped for a collector, run, enumerated, generated); the
  switch stepper that sweeps populations is switches.py.
- 2026-09-22, verifier plumbing rewritten after tools/simcheck.py: tests/reap.py was
  byte-identical to expert-defer-shed's, and test.sh, both Dockerfiles and test_outputs.py sat at
  0.64 to 1.0 against the retained kit. Each was rewritten in its own structure with the same
  guarantees (reaping by real uid over rounds, a root-only verdict directory, a Records parser);
  the highest ratio is now 0.45 and simcheck reports no near file.
- 2026-09-22, two dead helpers removed from the shipped tree: `Lines.drop()` and `Lines.wipe()`
  were never called, and they named exactly what a bypassing load and a fence ought to do - a
  table of contents for two graded rules. preflight's other 16 unused-function warnings are calls
  through an attribute (`load.parse(`, `mem.ld(`), which its regex does not count; each was
  checked to be reached.
- 2026-09-22, isolation probes made potent: answer-key now answers every launch from the sealed
  model when it can import it, privilege disarms the grader when it runs as root, late-reward keeps
  rewriting the reward for 240 s, plant-report suppresses the worker's own record and plants one
  claiming success, shrink-set rides on the forged hand answers. authoring/stale-line-spin/potency.py
  runs them against a copy of the verifier with the defences removed (answer-key, privilege,
  late-reward and disarm-grader score 1 there) and against the real image (all 0; the markers read
  `gt.json PermissionError, model ModuleNotFoundError` and `uid 1002`).
- 2026-09-22, cold attack on the verifier found a real route: `python3 -m pytest` puts the
  working directory first on sys.path, and test.sh never set one, so a platform that started it
  from a directory the worker can write (/work) would import a planted `pytest.py` as root. The
  new probe-cwd-plant scored 1 against a copy started from /work without the fix. test.sh now
  runs `cd /tests` first and every root interpreter with `python3 -I`; the probe scores 0 there
  even when test.sh is started from /work. The retained bundles in this checkout run
  `python3 -m pytest` the same way and were not changed here.
- 2026-09-22, a shadowed name in emit.py: forge_hand's case loop reused `name`, so both forgeries
  were written as cheat-hang-after-pass.sh and forge-hand vanished from the directory while the
  count still said 40. Caught by listing the directory; the loop variable is now `case`.
- 2026-09-22, quality-review fixes to the brief: the small-launch bounds said 3 slots and 4 lines
  where the thrash family reaches 8 and 6 (re-derived from 60 seeds of gen.programs); a restated
  cache-ownership sentence was merged; `bra` is now defined; `ld.ca` and `ld.cg` are named inside
  the cache rules they follow; "Caches start empty" was a rule with no sentence and has one.
- 2026-09-22, the worked example was searched for, not chosen: of 60,000 random candidates showing
  every kind of output line, 676 decide no switches.py reading beyond four that date what the
  example must print; the 30 best were run against the cheat trees and the pick decides only
  stated conventions.

## Validation status

| Check | Status | Notes |
|---|---|---|
| Originality record | 100 | 2026-09-22 |
| Difficulty record | 100 | 2026-09-22, on the built tree, gate measured |
| Agent image builds | yes | docker, python:3.12-slim via the mirror.gcr.io registry mirror (Docker Hub's CDN is refused by the sandbox proxy with 403) |
| No answer leaked into agent image | yes | launches carry inputs only; no gt, model or cases in the environment |
| Oracle = 1 | 1 | tools/docker_trial.py two-container run, 33 passed (harbor not used: see notes) |
| Nop = 0 | 0 | two-container run, 18 of 33 tests failed |
| Correct variants = 1 | 1, 1 | ok-heap and ok-list, two-container run |
| Cheats all score 0 | pending | final two-container sweep of all 40 on the final bundle in progress; the previous full sweep (old plumbing) was 42/42 |
| Probe potency | yes | potency.py, both runs started from /work: answer-key, privilege, late-reward, disarm-grader and cwd-plant score 1 against a defence-free verifier copy; all seven score 0 against the real one |
| Host cheat report | caught | every semantic cheat fails a named hand case; slow-step and rotate-from-zero stall; probe-uncollected-file dies on import |
| `readingcheck.py` | clean | 27 separated |
| `tracecheck.py` | clean | |
| `preflight.py` | 0 errors | 16 warnings are attribute calls its regex does not count (each checked); the ledger warning cleared by the entry |
| simcheck, structcheck, textcheck, hintcheck, catcheck | clean | textcheck against publish-settle-order's brief |
| deadfieldcheck, extraneouscheck, solvecheck, imagecheck | clean | imagecheck ran six shipped launches on the assembled image |
| onelinecheck | OK | load_from_cache and spin_passes are short; frozen (234 rows) and hangs_here (73 rows) have no rule at depth 2 |
| forgecheck | clean | carriers: forge-hand, probe-shrink-set; its full host cheat report: all 32 cheats graded on the host caught, exit 0 |
| originalitycheck with --corpus | 100 | 384 documents from 108 remote branches; nearest cosine 0.177, shingle 0.002 |
| Ledger entry | added | authoring/submissions.toml, verdict pending |
| Package | built | scripts/package.py, tasks/stale-line-spin.zip, 96 entries; tools/zipcheck.py clean |
| `harbor check` rubric | not run | manual quality review instead |

## Measurements (2026-09-22)

- Whole graded set, verifier image, --cpus=1: reference 10.36 and 11.39 s; ok-heap 16.25 and
  16.38 s; ok-list 27.13 and 29.68 s; 356 launches, none raised.
- Per large launch on the host: sealed model 1.3-3.3 s, reference 1.2-2.3 s, the plain per-cycle
  stepper 33.6-61.0 s on each wide launch and still running after 120 s on each deep one.
- Shipped engine: fails 17 of 30 hand cases and 253 of 326 generated launches (seed `report`);
  on the worked example it prints `hang 7` for `hang 6`.
- Model against an independent plain stepper (authoring/stale-line-spin/naive.py): 0
  disagreements over three seeds of the small families.
- Host cheat report, seed `report` (hand cases failed / generated launches failed of 326): coherent
  11/161, place-first-free 6/207, work-plus-one 21/294, free-same-cycle 3/132, park-spinners 7/124,
  sm-reverse 3/121, cmp-reversed 4/116, per-block-cache 6/87, place-mod 1/75, store-broadcast 6/55,
  store-leaves-copy 2/47, atom-updates-own 5/35, skip-no-rotate 1/28, store-allocates 1/27,
  line-word 2/21, hang-last-start 1/16, fence-noop 2/12, skip-any-spin 2/12, cg-keeps 2/5,
  fence-all 1/5, hang-no-store 1/5, lru 1/4, and three caught only by their named hand case:
  cg-drops-all 1/0, hang-at-detect 1/0, lt-inclusive 1/0. rotate-from-zero fails 4 hand cases and
  then starves a block forever; slow-step is correct and runs out of time. Under all-or-nothing
  grading the hand case alone is decisive, and it names the rule that broke.

## Open questions and next steps

Stage 7: finish the container cheat run, run every gate, package, add the ledger entry, commit
and push.
