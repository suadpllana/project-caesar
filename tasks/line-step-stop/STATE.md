# Task state

Working memory for this task. The assistant updates it after every stage. Assume the next
session starts with no memory of this one - anything not written here is lost.

## Current stage

`Stage 7 - Pre-flight and packaging`. The bundle is built, every local gate below has been
run on it, and it is packaged. The two-container gates cannot be run in this session: Docker's
daemon starts, but the egress policy refuses Docker Hub's blob CDN (`production.cloudfront.docker.com`,
403 Forbidden on the layer download, checked at 17:03 and again at 19:07 on 2026-09-22), so
no base image can be pulled and no image can be built; `harbor` 0.23.0 is installed and
blocked by the same pull. Every trial row below is host emulation: the real `tests/test.sh`
runs on the host with the same absolute paths and the same two unprivileged users the
verifier image creates, after an agent phase on a fresh `/app` and a hand-over of only the
declared files. Read those rows as evidence about the verifier's logic and isolation, not
about the container build. The easiness probe is the platform's and has not run.

## Assistant's assigned role

You are a debugger engineer who has worked on the run-control half of a source-level
debugger: the part that turns step, next, finish and continue into target operations, reads
line tables with statement flags and inlined-subroutine records, keeps frame identity across
recursion, and decides what frame list the user sees at a stop. Comfortable with the
difference between an engine that is correct when it single-steps and one that is usable on a
target where every stop is a round trip.

## Source repository (repo-based tasks only)

- Repo URL: none - idea-based task
- Task shape chosen (authored-on-top / ablation per docs/ABLATION.md): not applicable, no repository
- Contributor's relationship to it: not applicable
- License, and why vendoring it is permitted: not applicable, nothing is vendored
- Pinned commit vendored into environment/app_src/ (.git stripped): none
- Load-bearing couplings found during research (file paths): written, not vendored - see
  "Facts an agent must correlate"
- Identifier degradation done? The tree is authored in a terse register from the start
  (`tgt/`, `dbg/`, `mach`, `link`, `marks`, `steps`); there is no upstream to convert from
- Proper-noun sweep done? Nothing in the tree names a debugger, a vendor, a person or a
  file format other than plain text
- Upstream-diff check: there is no upstream to diff against

## Task summary

The agent is given a small source-level debugger for a stack machine. The program runs in a
separate target process; the debugger reaches it through a link that can report the program
counter and the return addresses, execute one instruction, or let the target run until it
reaches one of a set of addresses, and every one of those is a round trip. The debugger reads
an image holding functions, code, line-table rows (with a statement flag and line 0 for code
with no line) and inlined-call instances. A script of `break`, `run`, `cont`, `step`, `next`
and `finish` prints one line per command: the addresses a breakpoint resolved to, or the stop
kind, the stop address and the frame list innermost first. Three files under `/app/dbg/`
decide those lines and all three ship wrong: breakpoint resolution, the frame list, and the
run-control engine, which single-steps and so cannot finish the long loops the graded
sessions contain.

Definition of done: all 369 graded sessions print exactly the expected lines, inside one
300-second clock for the debugger's processes, with only the three declared files changed.

## Why it is hard

The rules are stated. What is not stated is which engine survives all of them at once under
the limit. The stop rules are row-based: a step stops on arriving at the first address of a
statement row whose line differs from the line being stepped; arriving part-way into a row
makes that row's line the line being stepped; an inlined instance's entry is stepped into,
stepped over or stopped at by comparing its call line with the line being stepped; a stop at
a call site hides the instances starting there, so the frame list is not a function of the
program counter. The limit forces running the target to planted addresses, which moves every
one of those decisions onto what was planted, and recursion fires planted return addresses
and row exits in deeper frames of the same function.

- Expert time estimate: 10 hours
- Why a frontier agent cannot one-shot the plan (the strategic answer - required): the recalled debugger design is wrong at four stated points and the limit forbids the loop that makes the rest easy. The recalled design - single-step, stop when the line changes, read inline frames off the program counter, step over a call with a return-address breakpoint trusted on first hit - is wrong at same-line row starts, part-way adoption, hidden call-site depth and recursion, and the stated limit forbids the single-step loop, so the engine has to be designed as modes over planted addresses rather than patched.
- Tactics making that true (docs/DIFFICULTY.md - prong A poison / prong B withholding / prong C late failure): A1, A3, B2, C1, C2, C3 and C4. A1 (the recalled
  line-changed, chain-from-pc, trust-the-return-breakpoint debugger is wrong where it is
  specific), A3 (no single technique fits: planting on every line breaks recursion and misses
  part-way landings, range stepping needs a stub that steps ranges, run-to-next-branch stops
  once per loop iteration), B2 (twelve graded decisions that interact), C1 (plain sessions
  must print exactly, so hide-everything and reveal-everything both fail), C2 (no real
  debugger runs this machine, gdb and lldb disagree on inline stepping, no sample output
  ships beyond the six lines of the worked example), C3 (loops of up to 700,000 iterations
  inside one row, inside calls and inside instances, one 300-second clock), C4 (every line of
  every session, 63 frozen sessions plus 306 nonce sessions shaped at each decision).
- Assistant's attack on the plan (its first plan, and where that plan is wrong): my first plan
  is to keep the shipped single-step loop, stop when a statement row of a different line is
  reached in the same frame, compare depths for next and finish, collect every instance whose
  range holds the pc as inline frames, and resolve breakpoints to the lowest row per function.
  It is wrong in five places: a same-line row start must not stop but a part-way landing must
  adopt its line; instance entries are judged by call line, and a call site hides the
  instances starting at it; caller frames are shown at the call instruction; breakpoints
  resolve per scope, not per function; and it cannot finish inside the limit. Replacing the
  loop with planted addresses then breaks recursion, which the single-step loop handled for
  free.
- Estimated solves out of 8 (design for 1, the hard edge; the realized rate drifts up): 2 (range 1 to 3, designed for the hard edge)
- Difficulty record score (tools/difficultycheck.py on authoring/<slug>/difficulty.toml, before
  Stage 2; every attempt's score and what changed, until it reaches the band in
  docs/DIFFICULTY-SCORE.md): attempt 1 on 2026-09-22 scored 97/100, in band, no hard stop;
  the three points lost were the shape axis measuring an empty task folder. Re-scored on the
  built tree at Stage 7: 100/100 with the tree measured rather than read (468 environment
  lines, 3 editable files, 306 reference lines including `solve.sh`, 46 cheats of which 33
  semantic, 3 variants) and the gate recorded as measured.
- Difficulty score anchor (50 at first complete submission, approved by contributor): not yet anchored
- Score history (date, score, what moved, and any pipeline re-anchor): 2026-09-22 first record, 97; 2026-09-22 built tree, 100 (shape measured, gate measured)
- Leak audit (docs/DIFFICULTY.md): for each mechanism, what in the bundle could let an agent
  discover, name or verify it without reasoning? Answer must be "nothing": the image holds
  only function ranges, code, rows and instances as parsed primitives; the link returns only
  the program counter and the return addresses; no sample session ships its expected output,
  and the brief quotes six lines of one; no shipped helper names adoption, hiding or
  recursion checks; the tape stays with the target. The six quoted lines decide two of the 29
  readings (`ret-address`, `run-skips-entry`), both rules the brief states in words; every
  prefix of every sample that shows a stop decides at least one reading, and the prefixes
  that decide only one show no step line or give away the per-instance breakpoint rule, which
  is subtler than the two this one confirms.
- Expert path, described step by step: read the image parser and the link to learn the
  primitives and the round-trip cost; build the scope model with caller frames at the call
  instruction and hidden depth as state; resolve breakpoints per scope; write one row-arrival
  rule; drive the target by modes (row exits, return address with a frame check, instance
  exit); apply the landing rules after returns and finishes; compare the fast engine with a
  slow single-stepping one on generated sessions; time the largest samples.
- Originality check: searched 2026-09-22 (six queries, recorded in
  authoring/line-step-stop/originality.toml). Nearest public work: Sy Brand's Writing a Linux
  Debugger part on source-level stepping (no inline frames, no statement flag, no adoption,
  no frame check on recursion); gdb's inline-frame and stepping sources (different rules on
  line-zero code and on the line a hidden call site shows); an LLVM issue showing gdb and lldb
  step into inlined calls differently. No twin found.
- Distinctness record score (tools/originalitycheck.py on authoring/<slug>/originality.toml):
  attempt 1 on 2026-09-22 scored 100/100; nearest ledger mechanism expert-defer-shed at cosine
  0.10; no tag or substrate overlap. Crowded archetype named: exception unwinding and stack
  trace construction (on the Languages list; departure recorded). Re-run at Stage 7 with the
  built brief: 100/100, nearest instruction in `tasks/` focus-return-point at cosine 0.240
  (ceiling 0.28), shingle 0.000; with `--corpus` pointed at the 67 instructions on the
  contributor's other remote branches (extracted with `git show`, none of them in `tasks/`):
  nearest `sheet-block-place` at cosine 0.209, shingle 0.001, over 80 documents.
- Nearest already-submitted task (from authoring/submissions.toml or the platform's own flag),
  what overlaps, and which of the five surfaces separate them: guard-mark-unwind - both replay a
  program in a small runtime and grade an exact trace; separated on all five surfaces
  (mechanism, substrate, graded output, failure mode, interaction).

## Instruction contract (docs/INSTRUCTION-CONTRACT.md, read before anything else)

Every graded assertion traces to a sentence in the instruction. Walk the tests, the sealed model
and test.sh line by line into authoring/<slug>/trace.md, start it with
`python tools/tracecheck.py <slug> --skeleton`, and keep `python tools/tracecheck.py <slug>` clean.
`preflight.py` errors while any line below is unanswered.

- Instruction trace (authoring/<slug>/trace.md; rows walked, NOT STATED left, tracecheck result): authoring/line-step-stop/trace.md, written by `write_trace.py`, which refuses a quote not found verbatim in instruction.md and a cited line range that no longer holds the def or constant it names; 47 verifier, harness and model sites, 63 frozen sessions and 29 readings walked, 0 NOT STATED, `tracecheck` clean
- Identifiability (readings enumerated, which survived the published evidence, what separated them): 29 readings in authoring/line-step-stop/readings.py, each the reference with one rule read the other way and every edit asserted to fire; none survives the published evidence (the quoted example decides two, the rules decide all); `tools/readingcheck.py` finds every one separated by the 39 small frozen sessions, none blind and none equivalent; on 2,700 generated sessions each moves 0.3% (`inrow-call-unplanted`) to 30.7% (`ret-address`)
- Shortcut strategies scored (nop, constant, positional, replayed example; score and cases matched): every one scores 0 in the host trial; exact matches over the 38 small frozen sessions and 306 generated ones (`shortcut_report.py`): the shipped tree 130 of 344 (37.8%), constant 0 (0.0%), first location only 191 (55.5%), one instruction per step 61 (17.7%), innermost frame only 135 (39.2%), the worked example replayed 4 (1.2%); the near-miss is V2 before its in-row call fix, 343 of 344 (99.7%), stopped by its own frozen case
- Independent implementation behind every tolerance and limit (path, measured headroom): the 300 s clock against authoring/line-step-stop/variants/v2 (24.3 s for the whole set) and the reference (24.4 s); the single-stepping variants/slow and variants/half both stopped at 300 s on sample-long, and variants/half alone took 157 s on the lightest frozen heavy session; the 400-address and 700,000-iteration bounds measured over every frozen session and 900 generated ones by `timing_report.py`
- Undecided decisions from the cold-reader pass (author-run or fresh session; sentence or example added for each): author-run on 2026-09-22 after the final rewording (a fresh session is not available: the brief forbids subagents); no undecided decision found. Checked in particular: a hit at the called function's first address during a step (decided: "It ends the command there" and "The kind is `hit` at a breakpoint"); a finish from the outermost function (never issued, stated); a jump back to the start of the row it is in (not a different row, not judged); a stepping frame in a function without rows (no row, no stop, no adoption, runs to its return)

## Verifier contract - FROZEN after Stage 2

Once agreed, this does not change without the contributor's explicit approval.

- Artifacts the agent produces: `/app/dbg/marks.py`, `/app/dbg/frames.py`,
  `/app/dbg/steps.py`. Nothing else is collected; every other file the debugger imports is the
  verifier's pristine copy.
- What is checked: for every graded session, the exact list of lines the session driver prints,
  one per command, compared line for line. Hand sessions are checked against expected lines
  frozen before the grading file was written; generated sessions are checked against a sealed
  model that single-steps its own machine with the tape, and the model is first checked against
  the frozen hand lines. The debugger runs as an unprivileged user connected to a target the
  verifier starts under a different user; the whole graded set runs under one wall clock that
  the brief states.
- Tolerances: none. Exact string equality on every line, all-or-nothing.
- Ground truth, and where it lives: `tests/seal/` (the model, the generator and `gt.json` with
  the frozen sessions, tapes and lines), root-owned and `chmod 700` before any submitted code
  runs.
- As built: 4 samples, 29 enumerated cases (one per reading), 6 fences, 24 heavy sessions, all
  in `tests/seal/gt.json`; 306 nonce sessions (nine families, `PER_FAMILY = 34` in
  `tests/judge.py`) generated from `os.urandom` after the agent is gone; `LIMIT = 300.0`
  seconds of debugger time for all 369; the model re-derives the 38 small frozen sessions
  before anything is graded, and `tests/cases.py` must name exactly the sessions `gt.json`
  holds.

### The frozen rules

Image and machine (frozen code the agent reads; stated in the brief because output depends on it):

1. An image declares functions `fn NAME LO HI [L1 L2]` in address order covering every address
   from 0; the first is where the program starts; `L1..L2` are the function's source lines and a
   function without them has no rows. Line numbers are never shared between functions.
2. One instruction per address: `nop`, `set R K`, `in R` (next tape value), `dec R`,
   `jnz R A`, `jmp A`, `call A` (A is a function's first address; pushes the next address),
   `ret` (returns, or ends the program when nothing is on the stack). Registers `a b c d` belong
   to the call and start at 0.
3. `row A L [x]` starts a row at A for line L; `x` marks a row that is not a statement; line 0
   is code with no line. A row runs up to the next row of its function or the function's end.
   A function with lines has a statement row with a nonzero line at its first address.
4. `inl ID F P C LO HI`: addresses LO..HI hold F's body inlined into P (a function or an
   earlier instance) from P's line C. An instance lies inside its parent, siblings do not
   overlap, an instance is entered only at LO from its parent's code and left only by falling
   from HI to HI+1, which starts a row; an instance holds no `ret`; LO starts a statement row of
   F's lines; rows inside an instance carry F's lines or 0.

Link (frozen): `pc()`, `stack()` (return addresses, outermost first), `step()` (one
instruction), `go(stops)` (at least one instruction, then on until the pc is in `stops` or the
program ends). Each is one round trip; the tape belongs to the target.

Output:

5. `break L` numbers breakpoints from 1 and prints `bN` followed by its addresses ascending.
   Its locations: every statement row with line L belongs to the innermost scope (function body
   or instance) holding its address; each scope holding such rows gets one location at the
   lowest of them. Every `break` names a line with at least one statement row.
6. Stops print `KIND PC` then the frames, innermost first, each `NAME:LINE`; KIND is `hit`,
   `step` or `done`. The program ending prints `exit`, and no command follows it.
7. Frames: each real frame is looked at at the pc (innermost frame) or at its return address
   minus one (every caller frame). At that address its scopes are the function followed by
   every instance holding the address, outermost first; an instance prints its function's
   name. A scope with a deeper scope below it at that address shows that deeper scope's call
   line; the deepest shows the line of the row holding the address, or 0. In the innermost
   frame, the innermost `hidden` scopes are not printed; the frame shows from the first
   visible scope outward, and a visible scope with a hidden one below it still shows the
   hidden one's call line.

Run control:

8. A hit happens when execution arrives at a location address, at any depth; the instruction a
   command starts at runs without that check, except that `run` stops at once if the first
   address holds a location. A hit leaves nothing hidden. `cont` runs to a hit or the end.
9. The stepping frame is the innermost frame, its scope the innermost visible scope, and the
   line being stepped is the line that scope shows.
10. `step` with something hidden reveals the outermost hidden scope, executes nothing and stops.
    `next` with something hidden steps over the outermost hidden instance as rule 13 does when
    the call line equals the line being stepped.
11. A call from the stepping frame: `next` runs it until it returns to the stepping frame; `step`
    stops at the called function's first address if it has lines (instances starting there are
    hidden) and otherwise runs it until it returns. A call that returns counts as having moved
    from the call instruction to the return address.
12. Within the stepping frame, each time execution passes into a different row: arriving at the
    row's first address, a statement row whose line is nonzero and differs from the line being
    stepped stops (`step`); arriving anywhere else in a row whose line is nonzero makes that line
    the line being stepped; non-statement and line-0 rows neither stop nor change it otherwise.
13. Passing into instances that start at the arrival address and lie below the stepping scope:
    with I the outermost of them, if I's call line equals the line being stepped, `step` stops
    with I revealed and any deeper ones hidden, and `next` runs until execution leaves I and then
    judges where it lands; otherwise both stop there with all of them hidden.
14. Leaving the stepping scope makes its nearest enclosing scope that holds the new address the
    stepping scope, and the arrival is then judged by rules 12 and 13.
15. The stepping frame returning makes the caller the stepping frame and its innermost scope at
    the return address the stepping scope (instances starting exactly there count as entered);
    the arrival is judged by rules 12 and 13 with the line being stepped unchanged.
16. `finish` from an instance runs until execution leaves it; from a function it runs until that
    frame returns; either stops (`done`) where it lands with the instances starting there hidden.
    `finish` is never issued in the first function's own scope of the outermost frame.
17. After any stop other than a hit or a reveal, the instances starting at the stop address
    and lying below the scope stopped in are hidden, except as rule 13 reveals one.

Scale and limit (stated in the brief; fixed from measurement): images of up to 400 addresses;
loops of up to 700,000 iterations inside one row, inside called functions and inside inlined
instances; one 300-second clock for the debugger's processes across all 369 graded sessions.

## Facts an agent must correlate (Stage 3)

- `environment/app_src/dbg/sess.py` (frozen) fixes the interface: `marks.resolve(img, line)`
  returns a breakpoint's addresses; `steps.Engine(img, link, locs)` runs each command and returns
  its kind or None, and keeps `hid`; `frames.show(img, pc, link.stack(), eng.hid)` prints a stop.
  The engine is handed `locs`, the one set of breakpoint addresses, which the driver updates.
- `environment/app_src/tgt/link.py` and `tgt/serve.py` (frozen): four calls, each one request
  and one reply over a socket; `go` executes at least one instruction before testing `stops`,
  so a command starting on a breakpoint address does not stop there - the same rule the brief
  states for hits. Nothing on the target side knows about rows or instances.
- `environment/app_src/tgt/mach.py` (frozen): what `call` pushes (the next address), that `ret`
  with an empty stack ends the program, that registers are per call. The debugger needs this
  to compute where control can leave a row.
- `environment/app_src/dbg/image.py` (frozen): rows carry `at`, `line`, `stmt`; instances carry
  `fn`, `up` (the parent object), `call`, `lo`, `hi`; nothing derived.
- `environment/app_src/samples/long.*`: the heavy sample, the only way to feel the limit
  locally. It crosses 14,984,670 instructions inside a stepping frame and 22,649,734 in all;
  no frozen heavy session exceeds it on either count, which is what the brief's "as heavy as
  the heaviest one we grade" claims.

## Stage 7 re-attack

The cold self-attack was not run as a solve, and is recorded as not run. By the time the
environment existed I had written the sealed model, the reference and a second engine (V2), so
a "cold" solve would have measured memory; a self-probe reported as passed by a contaminated
author is worse than none (CLAUDE.md, `reach-pair-sweep`). What stands in its place:

- the first plan was written before any code (above) and every one of its five errors is a
  reading with a frozen case that fails it;
- V2 was written apart from the reference to a different design (it plants every decision
  address of the stepping function and filters each stop, where the reference computes the
  current row's exits), and its first version was wrong: it missed call targets that lie
  inside the current row. That bug is kept as the reading `inrow-call-unplanted`, and it is
  the one wrong engine that comes close - 99.7% of generated sessions right - which is the
  shape of a late failure, not an early one;
- `tools/onelinecheck.py` over 1,159 arrivals, 1,647 stops, 590 breakpoints and 1,400 caller
  frames from 225 generated sessions: no exact rule of two terms or fewer for whether an
  arrival stops, how many scopes a stop hides, or how many addresses a breakpoint takes. The
  one short rule it finds is the caller line (`= line_at_call`), which the brief states in
  words and `read-ret-address` covers;
- `tools/readingcheck.py`: every reading separated by the small frozen set;
- which rules an agent can confirm on its own: two. The six quoted lines confirm that callers
  are read at the call instruction and that `run` stops at a breakpoint on address 0, both
  stated in words; no other expected line ships, the samples ship without output, and the
  target reports only addresses, so every other rule is confirmed by reasoning from the brief
  or not at all.

Estimated solves out of 8 after the re-attack: 2 (honest range 1 to 3).

## Decisions and their reasons

- **Out-of-process target with a round-trip link.** Measured on a two-process prototype on
  2026-09-22: 32 us per single-step round trip, 55 ns per instruction when the target runs to a
  planted address. The ratio (about 580) is what makes the naive family die whatever machine
  grades it, and it is the real reason debuggers plant breakpoints.
- **A tape only the target reads.** Without it, a debugger could simulate the program itself in
  process at Python speed and meet a Python-speed limit, which would retire the planted-address
  design the limit exists to force. The verifier runs the target under its own uid with the tape
  on its stdin; the debugger gets the image, the script and a socket.
- **One row per address; no call-site rows.** Shared addresses would make "which scope does a
  row belong to" a second rule the brief must carry. With one row per address, a location's scope
  is always the innermost scope at its address, so a hit never hides anything, and hidden depth
  arises only from step and finish stops - one rule instead of gdb's breakpoint-symbol test.
- **Instances are single ranges, single entry, single exit.** Non-contiguous ranges and jumps
  into the middle of an instance are realistic in optimized code, but each adds a rule (entering
  mid-instance) whose statement would cost a paragraph and whose realism gdb and lldb resolve
  differently. The generator never produces them; the brief states the guarantee.
- **Line numbers unique per function.** Makes "which function owns a row" trivial and keeps the
  whole program in one source numbering, as a single-file program has.
- **Heavy sessions are frozen, not generated.** The sealed model single-steps with the tape, and
  building the 24 heavy sessions with it took 1,641 seconds (`make_heavy.py`, about 68 s a
  session with the searches that miss the floor), so generating them inside the verifier would
  spend most of the verifier's own timeout. The 24 heavy
  sessions are in `gt.json`, root-only, and every one crosses at least 3.0M instructions inside
  a stepping frame. Two of them were rebuilt with their own seeds (`replace_heavy.py`): index
  11, built before the generator capped a heavy tape at 20,000 values, carried 560,583; index 12
  executed 31.7M instructions in all, more than `sample-long`, which would have made the
  brief's "as heavy as the heaviest one we grade" false for an engine that single-steps
  everything. The 39 small frozen sessions came out byte-identical across the rebuild.
- **Ground truth is `tests/seal/gt.json`.** It was `fixed.json` until the final gates; the kit's
  `forgecheck` and `hintcheck` look for `gt.json` in `tests/seal/`, and the kit and the bundle
  should agree about where truth lives.
- **The answer-key carrier falls back to the shipped engine.** `cheat-forge-answer-key` holds
  every frozen session's commands and lines keyed by a hash of the program, prints them without
  running the target, and passes all 63 frozen sessions; the first nonce session stops it.
  `cheat_report.py` asserts both halves, not only the zero.
- **`environment/Dockerfile` plays the short sample at build time.** A broken link or target
  then fails the build rather than the first session; it also sets `PYTHONDONTWRITEBYTECODE`,
  because the target is a second Python process that would otherwise leave bytecode in `/app`.
- **The worked example stays `sample-calls`' first six commands.** Measured, it decides two
  readings, both rules the brief states in words; no sample prefix that shows a stop decides
  fewer than one (see the leak audit).
- **The brief was reworded for cadence after the contract froze, without changing a rule.**
  `textcheck` read the variable `I` in the instance rule as first person and possessives as
  contractions, and sentences opening with a backtick did not split, so the cadence measured
  more even than it read. Every rule was re-read against the frozen list above after the
  rewording, and `write_trace.py` re-checked every quote.

## Known limits a reviewer should see

- **The clock is carried by frozen sessions.** The nonce population is small-loop by
  construction, because the model that computes its expected lines single-steps. A submission
  that held the sealed heavy answers could pass the clock with a slow engine; those answers are
  root-only in the verifier image and never in the agent's container, and holding every frozen
  answer is not enough to pass (the carrier above).
- **`textcheck` is clean against `focus-return-point`, not against every passed brief.** Against
  alias-settle-report, delta-view-retraction, guard-mark-unwind, note-carry-forward and
  share-register-screen, burstiness 0.775 sits under 0.9 of their 0.87 to 0.92, and the
  type-token ratio (0.236) is under theirs, which falls with length: this brief is 1,346 words,
  focus-return-point (1,734 words) sits at 0.258. Pushing further meant splitting rules across
  sentences for a proxy.
- **`inrow-call-unplanted` moves 0.3% of generated sessions.** It is caught by its own frozen
  case every time; the nonce population alone would catch it in about 60% of runs.

## Validation status

| Check | Status | Notes |
|---|---|---|
| Reference vs sealed model | pass | every frozen session and 306 nonce sessions in each of the host trials below; V2 the same |
| Frozen answers held through the heavy rebuild | pass | 4 samples, 29 cases, 6 fences byte-identical to the file they replaced |
| Wrong readings separated | pass | 29 readings, each by a named frozen session; `tools/readingcheck.py` separated 29, blind 0, equivalent 0 |
| Execution boundaries measured | pass | reference 24.4 s and V2 24.3 s of the 300 s clock; slow and half-way engines stopped at 300 s on sample-long; half-way engine 157 s on the lightest frozen heavy session with every line right |
| `tools/onelinecheck.py` | pass | three of four graded decisions have no rule of two terms or fewer; the short one is stated |
| `tools/imagecheck.py` | pass | image audit from the Dockerfile's WORKDIR and COPY |
| `tools/catcheck.py` | pass | Software vocabulary in the environment (191) and the prose (160) |
| `tools/deadfieldcheck.py` | pass | clean |
| `tools/extraneouscheck.py` | pass | every shipped file reachable, distinct and host-free |
| `tools/solvecheck.py` | pass | clean |
| `tools/hintcheck.py` | pass | none |
| `tools/structcheck.py` | pass | none |
| `tools/textcheck.py` | pass with note | no findings against `focus-return-point`; see the known limits |
| `tools/simcheck.py` | pass | no shipped file close to another bundle's; conceptually distinct |
| `tools/forgecheck.py` | pass | `cheat-forge-answer-key` carries the ground truth and scores 0, stopped by the nonce population |
| `tools/originalitycheck.py` | pass | 100/100; nearest brief 0.240 in `tasks/`, 0.209 with the branch corpus |
| `tools/difficultycheck.py` | pass | 100/100 on the built tree |
| `tools/tracecheck.py` | pass | see the instruction contract above |
| `cheat_report.py` | pass | 46 of 46 score 0 in the final run: 27 stopped by a sample, 16 by a frozen case, the two single-stepping engines by the clock on sample-long, and the answer-key carrier by the second nonce session after passing all 63 frozen ones |
| host trial oracle = 1 | pass | 10 tests passed, 369 of 369 sessions, 24.4 s of the 300 s clock |
| host trial nop = 0 | pass | fails the worked example's fifth line (`main:3` for `main:2`) |
| Correct variant V2 = 1 | pass | 10 tests passed, 369 of 369 sessions, 24.3 s |
| Isolation probes | pass | uid 2201; `PermissionError` on `tests/seal/gt.json`, the model, the verdict and the reward; the double-forked daemon is reaped before it writes; kill attempts denied; the target's `/proc` stdin, memory and environment refused, and no other user's process read |
| `package.py` + `tools/zipcheck.py` | pass | `tasks/line-step-stop.zip`, 92 entries, one `line-step-stop/` prefix, every `.sh` executable, no CR, no scratch; `zipcheck` none |
| `preflight.py` | pass | no errors; 12 warnings - eleven "unused" entry points that `sess.py`, `serve.py`, `run_dbg.py` and the verifier's worker call through attributes (`link.pc()`, `frames.show(...)`), and the reward-tamper reminder the daemon, verdict-planting and plant-then-crash probes answer |
| Docker oracle/nop | BLOCKED | image pull refused by the egress policy (403 on Docker Hub's blob CDN) |
| `harbor check` rubric | BLOCKED | installed; needs the images the pull cannot fetch |
| Easiness probe (exit gate) | PENDING | the platform's probe has not run against this build |

## Open questions and next steps

Submit, record the verdicts in `authoring/submissions.toml`, and run the Docker oracle and nop
gates on a machine whose egress reaches Docker Hub.

Packaged 2026-09-22 with `scripts/package.py` into `tasks/line-step-stop.zip` (92 entries,
164,885 bytes); `tools/zipcheck.py` found nothing. The ledger entry is in
`authoring/submissions.toml` with verdict `pending`.
