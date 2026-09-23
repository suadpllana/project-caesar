# Task state - stale-line-spin

Working memory for this task. Updated after every stage. The next session starts with no
memory of this one; anything not written here is lost.

## Current stage

`Easiness recovery 1 - rebuilt and locally validated, PENDING the external easiness probe`
(2026-09-23: the easiness probe solved the delivered bundle 3 of 3; the failure is captured and
classified below, the replan was selected, the task was rebuilt from Stage 2 with one contract
change made on the contributor's instruction - rule 12, streaming sums - and every local gate
passes on the rebuilt bundle. It is not ready and must not be presented as ready until an
external easiness probe passes; that probe cannot be run from an authoring session. Previous
stage: `Delivered - submission pending`, 2026-09-22.)

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
atomics, fences, spin-waits, streaming sums that read one line per issue through the cache,
and timed work. `/app/run_launch.py` runs a launch file and
prints, for every block, where it ran, when it was placed and when it exited and what it
printed; when a launch hangs, the cycle it hung and every stuck block with the word it spins
on; and chosen words of final memory. The shipped model is the coherent-machine model most
engineers carry in their heads, and it is wrong in six files. The agent repairs the six
files so that every launch prints exactly what the stated machine does, and so that the
graded set (large launches included) finishes inside 60 seconds. Since easiness recovery 1
the graded set includes persistent launches that keep sums streaming on most multiprocessors
for up to 16 million cycles while the rest issue every few cycles, so the clock has to carry
each multiprocessor forward on its own, and doing that exactly needs a rule for which stores a
carried stream can observe.

## Why it is hard

The difficulty is not the amount of code. It is that the model every engineer carries is a
coherent one, and that the natural way to make the simulation fast is exactly the way that
breaks the incoherent one.

- Expert time estimate: 16 hours (10 before easiness recovery 1)
- Why a frontier agent cannot one-shot the plan (the strategic answer - required): since easiness recovery 1 the plan that solved the delivered task 3 of 3 - literal stepping plus generic repeat detection plus a self-built stepper - is correct and far too slow: a running sum never repeats a state, and the persistent kind keeps sums streaming on most multiprocessors for millions of cycles while the rest issue every few cycles. The next plan, advancing streams in bulk between device-wide events, is also correct and also too slow, because the device is never quiet for long. What fits is to carry each multiprocessor forward on its own, which is exact only with a derived observation rule: a store reaches a carried stream only if it lands before the stream's issue on that line (cycle, then multiprocessor number) and only through memory (a cached copy hides it); a store to a line already read changes nothing read; which cached lines survive the stream's fills is first-in-first-out arithmetic. The priors underneath are unchanged: coherent memory, per-block caches, round-robin dispatch, spin-as-wait, and a reduction as one read of memory.
- Tactics making that true (docs/DIFFICULTY.md - prong A poison / prong B withholding / prong C late failure): A1 (coherent memory, per-block caches, round-robin dispatch, spin-as-wait, a reduction as one read, memory static between events), A2 (the brief never names coherence, staleness, livelock, lookahead or which stores a stream can see), B2 (placement, rotation, fill order, bypass drops, store updates, atomic bypass, fences, spin attempts, sums, work and exit timing interact in one trace), C1 (ordinary launches and small reduce launches must be cycle-exact), C2 (no expected output ships; a stepper written from the brief cannot run the persistent kind), C3 (measured, three tiers: 306 s and over 450 s for stepping every sum line, 231 s and over 450 s for device-wide bulk, about 15 s for the whole set with per-multiprocessor lanes), C4 (exact all-or-nothing over 42 hand and 369 nonce launches), plus the guard (six collected files, pristine parser/reporter/runner).
- Assistant's attack on the plan (its first plan, and where that plan is wrong): author-run and contaminated (the author wrote the model first), recorded as such. From the brief alone the plan I would write first is the probes' plan with sums stepped literally; timing the persistent sample kills it. The second plan is to bulk-advance streams between device-wide events using range sums over memory - it is what one does after seeing that sums never repeat - and it is correct but still minutes per launch. The third, per-multiprocessor lanes, is where I would get the observation rule wrong first: my own first model settled a carried stream after the store that cut it had landed (a stream reading a line in the storing cycle saw the new value), and the fuzz caught it in 122 of 9000 runs (3000 launches, each in three plan modes). That is the late failure the design depends on, and it happened to the author.
- Estimated solves out of 8 (design for 1, the hard edge; the realized rate drifts up): 3 (range 2-4). The delivered design was estimated at 2 and realized 3 of 3; the estimate for the rebuild is raised, not lowered, because an author who wrote the model cannot put a cold number on it (see the recovery section).
- Difficulty record score (tools/difficultycheck.py on authoring/<slug>/difficulty.toml, before Stage 2; every attempt's score and what changed): attempt 1, 2026-09-22, 100/100 IN BAND, one warning (gate not yet measured). Attempt 2, 2026-09-23, after easiness recovery 1 rewrote the record for the rebuilt design: 100/100 IN BAND on the measured tree (410 environment lines, 6 editable files, 781 reference lines, 55 cheats of which 44 semantic, 2 variants).
- Difficulty score anchor (50 at first complete submission, approved by contributor): not set - no submission yet.
- Score history (date, score, what moved, and any pipeline re-anchor): 2026-09-22 originality 100, difficulty 100 (record only). 2026-09-22 difficulty 100 on the built tree. 2026-09-23 easiness probe: solved 3 of 3 (failed). 2026-09-23 rebuilt: originality 100 (nearest ledger entry alias-settle-report at cosine 0.14), difficulty 100 on the rebuilt tree.
- Leak audit (docs/DIFFICULTY.md): the launch files carry only device shape, initial words and programs; no expected output, placement or cycle ships; the two new samples (tile_reduce, persistent_reduce) are inputs to run and time; the worked example is unchanged and decides only stated conventions; the shipped sum is one call to a memory-range helper (the reduction prior) and no helper exists that only the correct rules would call; the engine prints only the graded format. tools/onelinecheck.py over the rebuilt model: only load_from_cache has a short exact rule; store_in_sum (254 samples), hangs_here, frozen and spin_passes have none at depth 2. tools/leakcheck.py on the three probe trajectories: nothing above the floor.
- Expert path, described step by step: (1) run the samples, time the three large ones, read the engine end to end; (2) per-multiprocessor FIFO caches that outlive blocks, with the stated fill, drop, store, atomic and fence rules; (3) placement and rotation fixes; (4) sums literally, one line per issue read the way the matching load reads it, and the hang rules with a summing block not spinning; (5) profile the persistent launch and give each multiprocessor its own stretch of regular issues, carried forward by arithmetic (turns per block, range sums of memory, surviving old lines plus the last fills); (6) derive what ends a stretch from outside (a store to a line one of its sums reads from memory or a bypassing spinner watches, applied after the stretch is carried up to it in cycle and multiprocessor order) and from inside (a cached line reached before it is pushed out, a waiter's line evicted or dropped, a sum's last line); (7) diff against a plain stepper on small launches and on the persistent pattern shrunk until the stepper can run it, then time the whole set.
- Originality check: searched six queries (recorded in authoring/stale-line-spin/originality.toml). Found: Alglave et al. ASPLOS 2015 (stale L1 reads in message passing on real GPUs), Sorensen et al. OOPSLA 2016 (co-residency deadlock of inter-workgroup barriers), the GPGPU-Sim manual (atomics modelled as skipping L1), LightScan (ld.cg bypasses and evicts L1 lines), a dispatch study (placement by resource availability, not round robin). None states a complete model or computes placements, cycles, values or hangs for a launch. No twin.
- Distinctness record score: 2026-09-22 100/100 DISTINCT (tags overlap nothing in the ledger, substrate new, mechanism sentence nearest ledger entry alias-settle-report at cosine 0.14). Crowded archetype named: occupancy tuning (Kernels list), departure recorded.
- Nearest already-submitted task: guard-mark-unwind (ledger) - both are turn-taking execution models with an exact trace where waiters may never be released; all five surfaces separate (mechanism, substrate, graded output, failure mode, interaction). Also checked against every task on every remote branch (about seventy) and the nine per-label seed prompts: no GPU memory model anywhere; the Kernels seed (a warp execution model with divergence, barriers and bank conflicts) is intra-multiprocessor and grades barrier release steps and bank cycles, this is inter-multiprocessor and grades cache visibility, placement and hangs.

## Instruction contract (docs/INSTRUCTION-CONTRACT.md, read before anything else)

- Instruction trace (authoring/<slug>/trace.md; rows walked, NOT STATED left, tracecheck result): rewalked in full on 2026-09-23 after the rebuild: every test function, the 42 hand cases, the six artifacts, the worker's collection and import, the frozen interface and the parser's sum rule, the 60 s clock, and each rule of the rebuilt sealed model split by line range (sum start, sum line, sum end, plans, settling, observation); no NOT STATED row; tracecheck clean.
- Identifiability (readings enumerated, which survived the published evidence, what separated them): 38 wrong readings built as file sets from the reference (authoring/stale-line-spin/readings.py, the same files the cheats ship), eleven of them new for sums and for carried streams (sum-one-issue, sum-coherent, sum-no-fill, sum-cg-keeps, sum-word-issues, sum-first-issue, sum-last-issue, sum-fills-at-end, sum-is-spin, lane-late-read, lane-same-cycle); every one is ruled out by a quoted sentence and failed by a named hand case (tools/readingcheck.py: 38 separated). Readings whose rules the fast path cannot model step every cycle, so several stall on the large launches after failing their hand case.
- Shortcut strategies scored (nop, constant, positional, replayed example; score and cases matched), rebuilt set, seed `report`: nop 0 (fails 29 of 42 hand cases, all twelve sum cases among them, and 296 of 369 generated); const-none 0 (fails all 42 and all 369); pos-serial 0 (fails 38 of 42 and all 369); forge-hand (frozen answers replayed by launch key, the constant answer otherwise) 0 - passes all 42 hand cases, fails all 369 generated. The worked example is not in the graded set; replaying known answers is what forge-hand does for all 42 frozen ones. Before the rebuild: nop 17 of 30 and 253 of 326, pos-serial 27 of 30 and all 326.
- Independent implementation behind every tolerance and limit (path, measured headroom): the 60 s clock - authoring/stale-line-spin/variants/ok-model (the sealed model's clock behind the frozen interface, written apart from solution/) 27.1 and 28.6 s, and ok-edges (the reference with a fast path that never computes when a cached line goes) 14.4 and 14.7 s, against the reference's 14.7 and 15.1 s: the whole 411-launch set in the verifier image at --cpus=1, fresh nonce each run (authoring/stale-line-spin/container_time.py). Both variants score 1 in the two-container run.
- Undecided decisions from the cold-reader pass (author-run or fresh session; sentence or example added for each): author-run, mechanically (trace.md header). Sentences added for: the comparison order, the mod range, operands read before writes, the rotation remembering the slot not the block, an atomic touching no cache, the frozen interface and the fields say.py reads, one process for all launches; for sums (2026-09-23): which line comes first, one line per issue, what an issue reads and does to the cache, when rd is written, that a summing block is ready, and that it does not count toward a hang. The one decision prose leaves loose - whether a block reaching its spin during cycle t sits at it at t - is settled by the worked example (hang 6, not 5).

## Verifier contract - FROZEN after Stage 2

- Collected: exactly `/app/sim/{line,mem,place,turn,step,clock}.py`; everything else under /app is
  the verifier's pristine copy (tests/pristine, synced by authoring/stale-line-spin/sync_pristine.py).
- Interface: `clock.run(launch)` returns `(blocks, hang, left, gm)`; frozen `say.py` prints.
- Graded set: the 42 hand launches in tests/cases.py against tests/seal/gt.json, and
  `gen.programs(nonce, 40)` - nine small families x 40 and three large x 3 = 369 - against the
  sealed model, nonce drawn in test.sh at grading time. Exact, all-or-nothing.
- Clock: the worker, all 411 launches in one process, under `timeout 60` at one CPU.
- Isolation: worker as uid 1002 via setpriv, own session, reaped by uid; /tests/seal and
  /logs/verifier chmod 700 before it runs; reward written 0 first, 1 only if both halves pass.
- Additive changes since freeze, each proved by build_gt.py leaving every frozen answer
  byte-identical: the spin-tests hand case (2026-09-22) - no rule changed, a stated rule gained a
  test.
- CONTRACT CHANGE, easiness recovery 1 (2026-09-23), made on the contributor's instruction to make
  the task substantially harder after the 3/3 easiness failure: rule 12 is new - `sum.ca rd [a] n`
  and `sum.cg rd [a] n`, n issues of one line each through the per-multiprocessor cache, the
  total into rd at the n-th issue, a block at a sum ready and not at a spin. Every earlier rule
  is unchanged: build_gt.py kept all 30 frozen answers byte-identical and added 12 sum cases, and
  the rebuilt sealed model reproduces the delivered model on the 30 answers and on 978 generated
  launches of the ten earlier families (three seeds). New families: `reduce` (small, 40 per
  nonce) and `stream` (large, 3 per nonce). What "correct" means for any launch without a sum is
  exactly what it was.

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

Sum (2026-09-23): `sum.ca rd [a] n` / `sum.cg rd [a] n`, n a positive literal. The block's next
n issues read lines L, L+1, ..., L+n-1, where L is the line holding word a at the first issue;
each reads its line as the matching load would (sum.ca: the cached copy, else a fill that drops
the earliest-filled line when C are held; sum.cg: global memory, dropping the multiprocessor's
own copy if held) and adds its four words; the n-th issue writes the total to rd and moves on. A
block at a sum is ready every cycle and is not at a spin.

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

- 2026-09-23, easiness recovery 1, the persistent family's shape: roles come from the
  multiprocessor (three in four reduce, one in four runs workers) because persistent kernels that
  dedicate multiprocessors to a job is the real pattern and because it puts the worker events on
  multiprocessors without streams - which is exactly where a device-wide bulk step pays for every
  stream at every event and a per-multiprocessor lane pays nothing. The worker loop was cut to four
  instructions (work, store, step, branch) so the reference's cost per event stays small while
  the number of events - what the device-wide plan pays for - stays near two hundred thousand.
- 2026-09-23, stale hits at scale are fresh: instrumented, the persistent kind has 840 to 936
  prefetch hits per launch in some seeds and none stale, because nothing stores into a prefetched
  line in the few cycles before the stream reaches it. Accepted rather than engineered: the stale
  sum rules are graded by the reduce family and five hand cases, and what the persistent kind
  must carry is the observation rule, which it exercises over a thousand times per launch
  (stores landing in a tile while it is summed).
- 2026-09-23, readings the lane arithmetic cannot model (coherent, per-block-cache, broadcast,
  LRU, drop-all, fence-all, line-word, rotate-from-zero, park-spinners) are built with lanes off
  and step every cycle; the sum readings that change what one issue reads step every sum line.
  Each is caught by its hand case long before it stalls, and the cheat report says both.
- 2026-09-23, the variants ok-heap and ok-list were retired: they implemented the delivered
  contract and treat a sum as doing nothing. ok-model (the sealed model's clock behind the frozen
  interface) is the independent implementation; ok-edges is the reference with a different fast
  path, kept to show the verifier does not require the eviction arithmetic.
- 2026-09-23, the isolation probes and the forgeries moved off the shipped model onto the
  constant answer (the shipped files with const-none's clock). The rebuild made the shipped
  engine need 177.7 s for the graded set, and potency.py then showed probe-privilege and
  probe-disarm-grader disarming the grader of the defence-free verifier copy ("1 passed") and
  still scoring 0, because the worker ran out of the clock: a probe that cannot reach 1 without
  its defence attests nothing. The constant answer is wrong on every launch and instant, so the
  attack is the only way to 1; forge-hand is now caught by the generated launches (all 369)
  instead of by the clock.
- 2026-09-23, verification_explanation corrected: it said every one of the ten probes had been
  run against a verifier copy with its defence removed and scored 1 there. Five had - the five
  whose defence is a line of test.sh or the Dockerfile; the other five meet defences that are not
  a line to remove (the judge re-derives every answer, rejects a malformed record, and keeps its
  own seed and a floor on the generated count, and only six files are collected). The claim was
  already in the delivered bundle.

## Validation status

The rebuilt bundle, easiness recovery 1 (2026-09-23). The delivered bundle's table is in git
history (commit ef7a40e). Harbor is not available here: every two-container run below is
tools/docker_trial.py, which builds both images and runs the agent and verifier containers the way
the platform does; anything marked "host" is emulation outside any container.

| Check | Status | Notes |
|---|---|---|
| External easiness probe | NOT RUN - pending | cannot be run from this session; the recovery is not complete without it (RAISE-DIFFICULTY exit gate) |
| Originality record | 100 | rebuilt design; mechanism nearest ledger entry alias-settle-report at cosine 0.14 |
| originalitycheck with --corpus | 100 | rebuilt brief against 384 documents (371 saved from the remote branches plus the local bundles); nearest cosine 0.175, shingle 0.000 |
| Difficulty record | 100 | on the rebuilt tree: 410 environment lines, 6 editable files, 781 reference lines, 55 cheats (44 semantic), 2 variants |
| Agent image builds | yes | docker, python:3.12-slim via the mirror.gcr.io registry mirror (Docker Hub's CDN is refused by the sandbox proxy with 403) |
| No answer leaked into agent image | yes | launches carry inputs only; imagecheck assembled the image and ran six shipped launches with the reference |
| Oracle = 1 | 1 | two-container, images rebuilt from the final tree: 45 passed |
| Nop = 0 | 0 | two-container: 43 tests in error - the shipped engine needs 177.7 s for the set (host), so the 60 s clock stops the worker before it writes its record; host: also wrong on 29 of 42 hand and 296 of 369 generated |
| Correct variants = 1 | 1, 1 | ok-model and ok-edges, two-container on the rebuilt images, 45 passed each; whole set at --cpus=1: 27.1/28.6 s and 14.4/14.7 s against the reference's 14.7/15.1 s |
| Cheats all score 0 | 0 | final tools/docker_trial.py --all on the final tree and images: 57 of 57 trials as required - oracle 1 (45 passed in 26.0 s), nop 0, all 55 cheats 0; 36 fail on answers (forge-hand and probe-shrink-set by the generated set alone, 1 failed; the other isolation probes 43 failed), 19 leave no record the judge accepts (the engines too slow for the clock, probe-malformed's rejected record, probe-uncollected-file's import error). The first sweep, before the probes moved, was also 57 of 57 (recovery section 6) |
| Probe potency | yes | potency.py after the move: answer-key, privilege, late-reward, disarm-grader and cwd-plant score 1 against the defence-free copy, all seven score 0 against the real image; before the move privilege and disarm-grader were not potent (recovery section 6) |
| Host cheat report | caught | all 46 cheats graded on the host caught, each at a named layer (recovery section 6) |
| forgecheck | clean | carriers forge-hand and probe-shrink-set; run twice, before and after the probes moved, each re-running the whole cheat report three at a time: all 46 caught both times, the two reports identical except forge-hand (0/296 on the shipped engine, 0/369 on the constant answer) |
| Old winning plan | fails | cheat-old-plan (the delivered reference) fails all twelve sum hand cases, 39 of 40 reduce launches and all three persistent launches; literal-sums and device-bulk are right and too slow (249.1 s and 161.5 s on the persistent sample alone) |
| `readingcheck.py` | clean | 38 readings, 38 separated, none blind |
| `tracecheck.py` | clean | |
| `preflight.py` | 0 errors | 17 warnings are attribute calls its pattern does not see (each checked; the new one is `mem.lines`, called from step.py) |
| simcheck, structcheck, textcheck, hintcheck, catcheck | clean | textcheck against publish-settle-order's brief |
| deadfieldcheck, extraneouscheck, solvecheck, imagecheck | clean | |
| onelinecheck | OK | only load_from_cache is short; store_in_sum (254 rows), hangs_here, frozen and spin_passes have no rule at depth 2 |
| leakcheck on the probe trajectories | clean | nothing above the floor with the brief stripped |
| Manual quality review | walked | recovery section 6; three metadata claims and one cheat description fixed |
| Ledger entry | updated | authoring/submissions.toml, verdict pending, note on the 3/3 failure and the rebuild |
| Package | built | scripts/package.py after the last change to a shipped file: tasks/stale-line-spin.zip, 114 entries, 468 KB; tools/zipcheck.py clean; no cache, STATE.md or scratch entry. Built for the external probe - not to be submitted for review before that probe passes |
| `harbor check` rubric | not run | no harbor here; manual quality review instead |

## Measurements (2026-09-22, the delivered bundle; the rebuilt bundle's are in recovery section 6)

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

## Easiness recovery - 2026-09-23

### 1. The failure, captured before editing

- Probe result: easiness failed, 3 of 3 trials solved the bundle at commit ef7a40e. The
  contributor supplied the three transcripts; they are under `probes/stale-line-spin/`
  (`2026-09-23-easiness-1.txt`, `-2.txt`, `-3.txt`, brief stripped from the top of each) with
  `notes.md` beside them. The transcripts carry no reward lines; "solved" is the contributor's
  report and each transcript ends with a finished, self-verified repair.
- Trial 1. First plan (line 254, after one read of the tree): the defect list - per-block caches,
  LRU, stores syncing every cache, no-op fence, round-robin placement, a wait-based hang - and a
  rewrite of the six files. Decisive discovery (line 447): while every ready block spins, memory
  cannot change, so each multiprocessor's state cycles; detect the period, jump to the next wake,
  use the repeat as the hang test. Line 740 adds a closed form for all-bypassing spinners. Final
  method: that clock, then a brute-force stepper from the brief and 2471 random plus 2000
  structured launches diffed against it with no disagreement (lines 795-849); large launches
  1.8 s and 2.1 s at the stated bounds.
- Trial 2. First plan (line 678): the same defect list and "add cycle skipping for large
  launches". Decisive discovery (line 1027): freeze each multiprocessor whose ready blocks all
  spin, waking it only on a relevant store, a wake or a placement - per-multiprocessor laziness
  keyed on (rotation, cache) repeats. One real bug found by its own fuzzing (line 1794: a spin
  passing into another spin left the repeat key unchanged). Final method: 4200 fuzzed launches, no
  disagreement; large launches 0.7-2.4 s.
- Trial 3. First plan (line 712): the same list. Decisive discovery (line 1313): track each
  multiprocessor's cache-plus-rotation state until it repeats and replay the remainder of the
  period at a wake. One bug found by fuzzing (line 1165: the hang cycle when a block leaves its
  work straight onto a spin). Final method: about 6800 fuzzed launches; large launches 1.5-2.7 s.
- Earliest commit point: the first read. Every trial had the complete semantic plan before
  running a single program, and the complete fast path after one profile of the shipped samples.
- Where the plan came from: the instruction (every rule is stated operationally and each shipped
  file maps onto one group of rules), the project tree (the six files are short enough to diff
  against the brief by eye), and a self-built oracle (a literal stepper written from the brief).
  Not from internet retrieval, not from a public helper, not from a verifier loophole.
- Tactics on record and which failed: A1 failed - the coherent, per-block, round-robin and
  spin-as-wait priors were each read off the brief and dropped at once; A2 did not matter - the
  frozen condition was never named, and none of the three needed it, because detecting a repeated
  state answers the same question without deriving it; B2 failed - the interactions are absorbed
  by literal simulation; C2 failed - a self-written stepper is a complete oracle for a fully
  specified deterministic machine; C3 failed - generic repeat detection made the scale families
  fast. C1 and C4 held (each trial fixed one real bug its own oracle found) but only slow the
  plan down.
- Estimated solves out of 8 for the delivered bundle: 8 (the realized rate is 3 of 3).

### 2. Classification of the winning route

- **The default plan was correct.** A literal stepper of the stated rules is right on every graded
  launch, and all three wrote it first (trial 1 line 254, trial 2 line 678, trial 3 line 712).
  Direction: a specified interaction that makes that plan, and its obvious speed-up, wrong.
- **The naive method was fast enough.** The design's C3 assumed the fast path had to come from
  the frozen-attempt derivation; `tests/gen.py` `fixup(big)` and `chain(big)` put all the time in
  stretches where every ready block spins, and any state that stops changing can be detected as a
  repeat without knowing why it stopped. Measured by the agents at 0.7-2.9 s per large launch.
  Direction: a scale regime in which nothing repeats, so the fast path has to be derived.
- **The agent confirmed each step independently.** No oracle ships, but the brief is complete, so
  a literal stepper is one. This cannot be removed from a fully specified machine; the direction
  is that the literal stepper must be unable to run the regime that decides the grade, and the
  fast path that can must rest on decisions a small fuzz does not settle by accident.
- **The instruction delivered the plan** only in the sense the contract requires: every rule is
  stated. Nothing is to be hidden. The repair is to make stating the rules insufficient.
- Not a verifier defect: no trial exploited grading.

### 3. The semantic replan - candidates, attacked

**Candidate A: counted loops with a clock operand.** Blocks read `%clk` and spin in ordinary
loops against a deadline, so no stretch is all-spinning and nothing freezes. Attacked: an affine
loop in a steady rotation repeats up to its counter, and "repeat modulo a counter" is the same
generic trick one step further; a timeout is also an arbitrary constant. Rejected.

**Candidate B: preemption and migration.** A block spinning longer than a quantum is taken off
its slot and requeued, so it may land on another multiprocessor with another cache. Attacked:
the quantum is an arbitrary constant, each preemption is a scheduled event exactly like a wake,
and the probes' freeze-until-event clock absorbs it unchanged. Rejected.

**Candidate C: streaming reductions, device-wide.** New `sum.ca rd [a] n` and `sum.cg rd [a] n`:
one line per issue through the per-multiprocessor cache, n issues, the total into rd at the end.
A running sum never repeats a state, so repeat detection is useless and the fast path must be
derived: range sums over memory for the lines read, the cache after a stream as its last fills,
and the exceptions - a stale copy still cached when the stream reaches it, a waiter's line
evicted at an exact fill count, a bypassing sum dropping a line. Attacked: with events rare, the
probes' global clock survives with one new bulk step - step the first C fills after each event
literally (that settles every stale copy and every eviction), then add range sums. One discovery,
not two; estimated 5-6 of 8. Kept as the first half of the selection.

**Candidate X (selected): streaming reductions on a device that is never quiet.** Candidate C
plus a large family in which some multiprocessors run streams for millions of cycles while
others issue ordinary instructions every few cycles (persistent kernels that dedicate
multiprocessors to reduction and the rest to tiles, the pattern of communication-dedicated
kernels). What it does to each plan:

1. The probes' plan - a literal stepper with a generic freeze - steps every multiprocessor every
   cycle, because a running sum is never frozen. Correct, and too slow by an order of magnitude.
2. The second plan - between device-wide events, advance every multiprocessor's streams in bulk
   - is correct and still too slow: a wake lands somewhere every few dozen cycles, so the bulk is
   re-derived for every multiprocessor at every one of hundreds of thousands of events.
3. The third plan keeps one plan per multiprocessor alive across other multiprocessors' events,
   which is exact only with a new derivation: which stores a plan can observe. A store is seen by
   a stream only if it lands before the stream reaches the line - cycle first, then
   multiprocessor number, because an earlier multiprocessor's issue in the same cycle comes first
   - and only if the line is not cached there when the stream reaches it; a store to a line the
   plan already read changes nothing it read; a bypassing waiter sees a store to its word at its
   next attempt; a cached waiter sees none, and is released only when its line is evicted or
   dropped, at an exact fill count or an exact turn of a neighbour's sum. Plan 2's assumption that
   memory is static between events is what plan 3 has to give up.

Attacked: (a) can the third plan be reached by a generic trick? Per-multiprocessor repeat
detection (trial 2's clock) does not apply: a stream's state never repeats, and the stores that
end a stretch are other multiprocessors' ordinary instructions. (b) Can the literal transient
stand in for the eviction arithmetic? Yes, inside a plan, cheaply - which is fine; the transient
settles the local exceptions, and what it cannot settle is the cross-multiprocessor visibility.
(c) Is it one-shot? The planning attack below says no: the first two plans are each reasonable and
each measured wrong only at the stated scale. (d) Is there an expert path? Yes, step by step:
literal sums; profile; bulk streams with range sums and the FIFO's last fills; profile again;
per-multiprocessor plans with an observation test for stores; diff every tier against the plain
stepper on launches it can still run. (e) Fairness: every rule is one sentence in the brief, the
scale is stated, and the samples include one launch of the new kind.

Tactics after the repair: A1 (a reduction is one read of memory - the shipped engine does that;
memory is static between events - plan 2; a stream sees the latest store - plan 3's first draft),
B2 (stream fills, stale copies, waiter evictions, bypass drops, store order within a cycle and the
rotation all decide the same totals and cycles), C1 (ordinary small launches still grade every
sum rule exactly), C3 (measured, both wrong tiers, before the contract is frozen - see section 6),
C4 (exact all-or-nothing over hand launches and nonce launches, the new family included), plus
the guard.

Intake answers (docs/PASSING-TASK-RESEARCH.md): (1) first plan: literal stepper plus generic
freeze; (2) what breaks it: a sum's state never repeats, and the new family is millions of cycles
of sums; (3) second discovery: the device is never quiet, so memory is not static between the
events the second plan bulks across, and per-multiprocessor plans need the store-observation rule;
(4) leak audit: no shipped helper, field or sample output shows a turn, a fill or a plan; the
samples carry inputs only; (5) ordinary cases that stop an overconservative solution: small
`reduce` launches where a sum reads stale copies, is released early by eviction, or sees and
misses stores by a cycle; (6) late failure: a store to a line a stream passed a million cycles
earlier; a waiter released by a neighbour's sum at an exact fill; (7) the invariant: a plan's
cache is its initial lines minus the evicted ones plus its last fills, and a store is observable
only by the rule in (3); (8) cheats: the shipped one-issue sum, a coherent sum, the probes' plan
with literal sums (too slow), the device-wide bulk (too slow), and a lazy plan that reads memory
at the end of the plan instead of when each line is reached; (9) variants: the sealed model ported
to the six files, and a second lazy clock written apart; (10) the expert sequence in (d).

### 4. What was rebuilt

Measured before the contract was frozen, as RAISE-DIFFICULTY requires: a prototype of the
persistent kind (authoring/stale-line-spin/proto_stream.py) timed under the three tiers of one
engine - per-multiprocessor plans 7.4 s, plans only while the device is quiet over 240 s, spinner
plans only (every sum line stepped) 136 s - and the three agreed where they finished. Only then
was rule 12 frozen (test_outputs.py docstring and the verifier contract section above).

- Contract: rule 12, sums. The 30 frozen answers are byte-identical (build_gt.py), 12 sum hand
  cases were added (42 in all), and two generated families: `reduce` (small, 40 per nonce: a
  stale prefetch read or not, a waiter released by a neighbour's sum, writers racing a sum from
  lower and higher multiprocessors, two sums trailing each other) and `stream` (large, 3 per
  nonce: persistent reducers on three multiprocessors in four, workers looping on the rest, stores
  sweeping the tile region, watchers on bypassing multiprocessors). 369 generated per nonce.
- Sealed model: rebuilt around per-multiprocessor plans, with a `mode` switch that runs the same
  engine as the two slower tiers for measurement. It reproduces the delivered model on all 30
  hand answers and on 978 generated launches of the earlier ten families (three seeds), and the
  plain stepper (naive.py, now with literal sums) in every mode on 20000 unshaped sum launches,
  3000 reduce launches and 40 persistent launches shrunk until the stepper can run them.
- Environment: the frozen parser accepts `sum.ca`/`sum.cg` with a positive literal count; the
  shipped engine reads a whole sum from global memory in one issue (the reduction prior); two
  samples, `tile_reduce.txt` and `persistent_reduce.txt`; pristine copy synced.
- Reference: per-multiprocessor lanes written apart from the model (different memory sums,
  different end computation, different cache rebuild), a before-write hook with an interval index
  over lane ranges, and a one-issuer fast path. It agrees with the model on 1233 graded launches
  over three seeds and on 12000 fuzzed small launches, and with the plain stepper on the shrunk
  persistent launches.
- Bugs found on the way, each by a differential test: the model settled a plan after the store
  that cut it had landed (122 of 9000 fuzz runs; the exact failure the design rests on); the
  reference's fast path advanced the rotation and then declined to issue a store (a block starved
  forever); it ran a cycle while a freed slot waited to be filled (a placement four cycles late);
  it skipped the all-spinning check on its first cycle (hang dates one late in 264 of 12000). A
  sed patch mis-indented four authoring scripts (CLAUDE.md warns against shell-patching Python;
  repaired line by line and compiled), and `pkill -f` twice killed its own shell because the
  pattern was in its own command line (use a bracketed pattern or PIDs).
- Brief: a sum paragraph, "A block at a spin or a sum is ready", "A block at a sum does not sit
  at a spin", the new counts and the persistent kind's scale, re-derived from the generator
  (small bounds over 60 seeds; the longest of 24 persistent launches 14.5 million cycles, the
  construction bound 15.3 million). 8221 characters.
- Trace rewalked in full; readings 38; cheats 55; variants ok-model and ok-edges replace ok-heap
  and ok-list, which knew nothing of sums; metadata, difficulty and originality records and the
  ledger entry rewritten.

### 5. The old winning implementation, kept as a cheat

`cheat-old-plan.sh` ships the delivered reference (commit ef7a40e) unchanged: the literal stepper
with the frozen-stretch skip that all three trials converged on. It treats a sum as doing nothing.
`cheat-literal-sums.sh` is the same plan carried into the new contract - every sum line stepped,
spinners still skipped - and is correct and too slow. `cheat-device-bulk.sh` is the second plan -
streams advanced in bulk only while no multiprocessor issues anything else - and is correct and
too slow. The hand case that proves the old plan wrong is `sum-issues` (and every other sum case):
see the cheat report in the validation table.

### 6. Measurement of the repair

- Scale gate, current family, one persistent launch each (authoring/stale-line-spin/tiers.py,
  host): sealed model with plans 6.9 s and 4.9 s; every sum line stepped over 450 s and 305.7 s;
  device-wide bulk over 450 s and 230.7 s. Whole graded set, verifier image, --cpus=1: reference
  14.7 and 15.1 s, ok-edges 14.4 and 14.7 s, ok-model 27.1 and 28.6 s.
- The two slow tiers as cheat trees, on the shipped `persistent_reduce.txt` alone (host, other
  jobs running): `literal-sums` 249.1 s and `device-bulk` 161.5 s, both with the right output,
  against the reference's 2.6 s.
- First two-container sweep (tools/docker_trial.py --all, probes still on the shipped engine): 57
  of 57 trials as required - oracle 1 (45 passed in 30.8 s), nop 0 (43 tests in error: the
  shipped engine needs 177.7 s for the whole set on the host and raises nothing, so the 60 s
  clock stops the worker before it writes its record), all 55 cheats 0. Wrong answers fail by
  name (old-plan 13 tests failed, sum-one-issue 13, pos-serial 39, const-none and
  placed-next-cycle 43); engines too slow for the clock leave no record (device-bulk,
  literal-sums, slow-step, the shipped engine under forge-hand then, and the readings built to
  step every cycle or every sum line); probe-crash-worker and probe-plant-report failed all 43
  judged tests and the other eight probes left no record the judge accepts - several of them for
  the wrong reason, the clock, which is what the potency run below exposed. Its images were built
  a minute before the ungraded persistent sample was regenerated and two docstrings re-wrapped;
  the oracle, nop and variant runs were repeated on rebuilt images, and the eleven cheats changed
  afterwards were re-run on their own (validation table).
- Probe potency (authoring/stale-line-spin/potency.py, test.sh started from /work, after the
  probes moved to the constant answer): against a copy of the verifier with the privilege drop,
  the root-only seal and verdict directory, the reaper, `cd /tests` and `python3 -I` undone,
  answer-key, privilege, late-reward, disarm-grader and cwd-plant each score 1 (markers: `gt.json
  read, model imported`; `uid 0`); plant-report (43 failed) and shrink-set (1 failed: the judge's
  own count of generated launches) score 0 there as well, stopped by defences that copy keeps.
  Against the real image all seven score 0 on wrong answers, with the markers `gt.json
  PermissionError, model ModuleNotFoundError` and `uid 1002`. Before the move, privilege and
  disarm-grader scored 0 against the defence-free copy with the grader already disarmed ("1
  passed"), because the shipped engine under them ran out of the clock (Decisions, 2026-09-23).
- Host cheat report (authoring/stale-line-spin/cheat_report.py, seed `report`, run by
  tools/forgecheck.py three cheats at a time; hand launches failed / generated launches failed of
  369): const-none 42/369, placed-next-cycle 42/369, pos-serial 38/369, forge-hand 0/369 (on the
  constant answer; 0/296 on the shipped engine before the probes were moved), work-plus-one
  29/337, place-first-free 11/250, coherent 18/173, park-spinners 12/139, cmp-reversed
  4/134, free-same-cycle 3/132, sm-reverse 5/130, skip-no-rotate 10/102, per-block-cache 9/97,
  place-mod 1/75, lane-same-cycle 1/63, store-broadcast 13/60, skip-any-spin 1/59, line-word
  10/58, store-leaves-copy 2/47, old-plan 12/42, sum-one-issue 12/42, sum-word-issues 12/40,
  atom-updates-own 5/36, store-allocates 1/27, sum-first-issue 3/17, hang-last-start 1/16,
  fence-noop 2/15, sum-last-issue 4/15, sum-is-spin 6/14, lru 2/9, sum-coherent 5/9, sum-no-fill
  3/9, cg-keeps 4/6, fence-all 1/5, hang-no-store 1/5, lane-late-read 1/5 (all three persistent
  launches among them), sum-fills-at-end 1/5, sum-cg-keeps 2/1, and caught only by their hand
  case: cg-drops-all 1/0, hang-at-detect 1/0, lt-inclusive 1/0. device-bulk, literal-sums and
  slow-step are right wherever they finish and stall on a large launch; rotate-from-zero fails 4
  hand cases and then starves a block; probe-uncollected-file dies on import. All 46 graded on the
  host caught; forgecheck found the answer-key carriers forge-hand and probe-shrink-set and passed.
  Several sum readings move few generated launches (sum-cg-keeps 1, sum-fills-at-end 5): under
  all-or-nothing grading the hand case that names each is what decides it.
- Quality review walk (docs/QUALITY-REVIEW.md, 2026-09-23, on the rebuilt bundle). Instruction
  and verifier agree both ways: trace.md walks every test and every model rule to a quoted
  sentence (tracecheck clean), each sum sentence has a hand case (sum-issues ... sum-not-spin),
  the six files are named with absolute paths in paragraph 2, the interface and printed fields in
  paragraphs 2 and 7, the clock and the one-process run in the last paragraph; every count in the
  brief was re-derived from gen.programs over 60 seeds (40 x 9 small, 3 x 3 large; small bounds 4
  multiprocessors, 8 slots, 6 lines, 20 blocks; persistent sums up to 49,888 lines). Prose:
  textcheck, structcheck and hintcheck clean. Verifier: the judge re-derives every answer from the
  model and trusts nothing the run stage says beyond the lines printed for a launch whose digest
  matches (test_outputs.py Records). Environment: imagecheck clean on the assembled image;
  preflight's 17 unused-function warnings are attribute calls its pattern cannot see (each
  checked, the new one is `mem.lines`, called from step.py). Metadata: found and fixed three
  claims - the probe-potency sentence said all ten probes had been shown potent (five were, the
  five whose defence is a line of test.sh or the Dockerfile; this was already in the delivered
  bundle), both variants were said to be written apart from the reference (ok-edges is the
  reference with another fast path), and the cheat list left out the plain stepper; one cheat
  description (lane-same-cycle) named sums only where the reading also moves bypassing spinners;
  two docstring lines ran past the wrap and were re-wrapped (ok-model regenerated).
- Cold self-attack: author-run and contaminated; see "Assistant's attack" above. It does say the
  thing the exit gate asks for - I can see where to start, and I got the observation rule wrong
  the first time I wrote it - but a contaminated author's attack is not the probe.
- Not done, and cannot be done here: the external easiness probe. Recovery is not complete.

## Open questions and next steps

- Blocker for completing easiness recovery 1: the external easiness probe (normal frontier model,
  internet, the full 14400 s, the platform environment) has not been run on the rebuilt bundle and
  cannot be run from an authoring session. Until it reports a pass the recovery is pending and the
  task is not ready.
- When the probe answers: on a pass, record the realized result here (RAISE-DIFFICULTY exit gate
  item 4), set the stage, and update `verdict` and `note` in authoring/submissions.toml. On a
  fail, put the new trajectories under probes/stale-line-spin/ and repeat from section 1 of
  RAISE-DIFFICULTY - diagnose the new winning route before adding anything.
- What to look for in a new trajectory: whether the solver reaches per-multiprocessor stretches at
  all, and if so whether its observation rule was derived or fuzzed into place. A solve that fuzzes
  a lane engine against a self-built stepper on shrunk persistent launches is the expert path this
  design expects; a solve that fits the clock without carrying multiprocessors apart would mean a
  scale boundary this session did not find.
- Not run in this session: `harbor run` and `harbor check` (no harbor here; the two-container runs
  used tools/docker_trial.py) and any external probe. The self-probe was not run because the
  author wrote the model first (CLAUDE.md, reach-pair-sweep); the tier timings, the reading
  separations and the cold attack are the evidence available here, and none of them is a
  substitute for the probe.
