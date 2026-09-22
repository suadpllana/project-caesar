# Task state

Working memory for this task. The assistant updates it after every stage. Assume the next
session starts with no memory of this one - anything not written here is lost.

## Current stage

`Stage 2 - verifier contract` (Stage 1 closed 2026-09-22: originality 100, difficulty 97)

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
  "Facts an agent must correlate" once Stage 3 is built
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
  ships), C3 (million-instruction loops inside one row and inside calls, one limit), C4 (every
  line of every session, hand sessions plus a nonce population shaped at each decision).
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
  docs/DIFFICULTY-SCORE.md): attempt 1 on 2026-09-22 scored 97/100, in band, no hard stop.
  The three points lost are the shape axis measuring an empty task folder; warnings: gate not
  yet measured on the built tree.
- Difficulty score anchor (50 at first complete submission, approved by contributor): not yet anchored
- Score history (date, score, what moved, and any pipeline re-anchor): 2026-09-22 first record, 97
- Leak audit (docs/DIFFICULTY.md): for each mechanism, what in the bundle could let an agent
  discover, name or verify it without reasoning? Answer must be "nothing": the image holds
  only function ranges, code, rows and instances as parsed primitives; the link returns only
  the program counter and the return addresses; no sample session ships its expected output;
  no shipped helper names adoption, hiding or recursion checks; the tape stays with the target.
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
  trace construction (on the Languages list; departure recorded). The 73 task folders on the
  contributor's other remote branches, which the ledger does not carry, were inventoried by
  hand: none is a debugger, none grades stops, line tables or inline frames.
- Nearest already-submitted task (from authoring/submissions.toml or the platform's own flag),
  what overlaps, and which of the five surfaces separate them: guard-mark-unwind - both replay a
  program in a small runtime and grade an exact trace; separated on all five surfaces
  (mechanism, substrate, graded output, failure mode, interaction).

## Instruction contract (docs/INSTRUCTION-CONTRACT.md, read before anything else)

Every graded assertion traces to a sentence in the instruction. Walk the tests, the sealed model
and test.sh line by line into authoring/<slug>/trace.md, start it with
`python tools/tracecheck.py <slug> --skeleton`, and keep `python tools/tracecheck.py <slug>` clean.
`preflight.py` errors while any line below is unanswered.

- Instruction trace (authoring/<slug>/trace.md; rows walked, NOT STATED left, tracecheck result): TODO
- Identifiability (readings enumerated, which survived the published evidence, what separated them): TODO
- Shortcut strategies scored (nop, constant, positional, replayed example; score and cases matched): TODO
- Independent implementation behind every tolerance and limit (path, measured headroom): TODO
- Undecided decisions from the cold-reader pass (author-run or fresh session; sentence or example added for each): TODO

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
- Ground truth, and where it lives: `tests/seal/` (the model, the frozen hand lines, the tapes),
  root-owned and `chmod 700` before any submitted code runs.

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

Scale and limit (stated in the brief; numbers fixed at Stage 4 from measurement): images of up
to a few hundred addresses; commands that execute up to a million instructions inside one row
or inside called functions; one wall clock for the whole graded set.

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
- `environment/app_src/samples/long.*`: the heavy sample, the only way to feel the limit locally.

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

## Validation status

| Check | Status | Notes |
|---|---|---|
| Agent image builds | not run | Docker Hub blob storage is denied by this session's egress policy (403 on production.cloudfront.docker.com); no base image can be pulled |
| No answer leaked into agent image | not run | |
| `harbor run -a oracle` = 1 | not run | harbor 0.23.0 installed; blocked by the image pull above |
| `harbor run -a nop` = 0 | not run | same |
| Cheats all score 0 | not run | |
| `tracecheck.py` (every graded assertion traced) | not run | |
| `preflight.py` | not run | |
| `harbor check` rubric | not run | |

## Open questions and next steps

Stage 3: build the environment (machine, target, link, image parser, session driver, three
shipped decision modules, sample sessions). Then the sealed model, the generator and the
verifier plumbing, written fresh.
