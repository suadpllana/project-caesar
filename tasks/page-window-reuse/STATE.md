# Task state

Working memory for this task. The assistant updates it after every stage. Assume the next
session starts with no memory of this one - anything not written here is lost.

## Current stage

`Stage 7 - Pre-flight and packaging`

## Assistant's assigned role

Inference-serving engineer on the memory manager of a token-generation service: the part that
decides which request is resident, which pages of a request's cache stay in the pool, which
prompt work a later request gets for free, and which page the pool takes back when it runs
dry. Comfortable with fixed-page allocators, with residency that is narrower than history,
and with the difference between a structure that is correct and one that is affordable at the
size the service actually runs at.

## Source repository (repo-based tasks only)

- Repo URL: none - idea-based task
- Task shape chosen (authored-on-top / ablation per docs/ABLATION.md): not applicable, no repository
- Contributor's relationship to it: not applicable
- License, and why vendoring it is permitted: not applicable, nothing is vendored
- Pinned commit vendored into environment/app_src/ (.git stripped): none
- Load-bearing couplings found during research (file paths): authored, listed under "Why it is hard"
- Identifier degradation done? Conversion table lives at solution/names (never in environment/);
  names referenced by instruction/verifier left untouched: yes, written at Stage 3
- Proper-noun sweep done? The tree is authored, carries no project, product or person name, and
  no distinctive error string; checked at Stage 3 and again before packaging
- Upstream-diff check: nothing upstream to diff against

## Task summary

`/app` is the page manager and admission loop of a token-generation service, cut down to the
part that decides what is resident and what the pool hands out. A pool holds fixed pages, a
page holds a fixed number of tokens of one request's cache, and a request arrives with a
prompt and the tokens it will emit. A step decodes one token for every resident request and
then fills waiting prompts, inside a token budget. A resident request keeps only the pages
holding its first tokens and the pages holding its last tokens, and lets the middle go. A
full page is named by its tokens and the page before it, so a later request with the same
prompt takes those pages instead of writing them again - as far as the walk from the start of
the prompt gets before it meets a page that is gone. When the pool has no free page it takes
back the page released longest ago, which puts everything under that page out of reach.

The service was rewritten and has been wrong since. Six files under `/app/kv/` are editable
and are the artifacts; everything else is the verifier's own copy. The graded work is the
exact trace of a set of programs, three of them at a scale where the naive-but-correct
structures run out of the stated limit.

## Why it is hard

The first plan is a paged-cache block manager as every public serving stack builds one, and
four of its structures are specifically wrong here: residency is not the whole history, a
take-back is allowed to strand what sits under it, reuse is a walk that stops at a gap rather
than a match on a chain of content hashes, and preemption is the last resort rather than the
first. The second finding, which invalidates the implementation of the first rather than
adding a case to it, is that a single take-back removes a group from the reusable set - every
page under it that nobody holds goes back to the pool at once, and every page under it that
somebody does hold stops being reusable forever, so the reusable set is not a queue pages
leave one at a time and the free count, the reuse index and the age order are one structure.

- Expert time estimate: 10 hours
- Why a frontier agent cannot one-shot the plan (the strategic answer - required): the retrievable design for this exact component is coherent, complete and wrong in four places at once, and the
  rule that breaks it - a request holds only its first and last tokens - has a consequence no
  amount of care at plan time produces: the pages a fill releases in the middle are the oldest
  unheld pages in the pool, so the first thing pressure takes back is the middle of a request that
  is still running, which strands that request's own tail and shortens what the next request with
  the same prompt may reuse, tens of steps later and in a program the agent did not write.
- Tactics making that true (docs/DIFFICULTY.md - prong A poison / prong B withholding / prong C late failure): A1 the paged-cache prior is inverted at four points; A2 residency, reuse and the strand are
  stated operationally and never named; B2 ten rules hold at once and five pairs change each
  other's meaning; C1 both sides of every fence are graded; C2 the only local check is the
  shipped server, which is wrong in six places, and the graded programs are generated after the
  agent's container is gone; C3 three naive-but-correct structures are measured against a stated
  limit at a stated scale; C4 exact traces, all-or-nothing, over enumerated and generated programs.
- Assistant's attack on the plan (its first plan, and where that plan is wrong): my first plan is
  a page table per request, a reuse index keyed by the chain of page contents, a reference count
  per page, eviction of the least recently used unreferenced page that has nothing under it, and
  preemption of the newest request when the pool runs dry. It is wrong at residency (the middle of
  a request is not held), at the walk (a stranded page still matches by content and must not be
  reused), at the take-back (pages with something under them are exactly what gets taken, and the
  strand goes back to the pool in a group), and at the order of supply (a take-back comes before a
  preemption, and a preemption yields reusable pages rather than free ones). I would not have
  committed to the right structure without running programs that put the pool under pressure.
- Estimated solves out of 8 (design for 1, the hard edge; the realized rate drifts up): 2 (design target 1 to 3)
- Difficulty record score (tools/difficultycheck.py on authoring/<slug>/difficulty.toml, before
  Stage 2; every attempt's score and what changed, until it reaches the band in
  docs/DIFFICULTY-SCORE.md): attempt 1 on 2026-09-15 scored 100 of 100, in band, one warning -
  gate.measured is false until the wide families are timed, which Stage 3 does before the design
  depends on the limit.
- Difficulty score anchor (50 at first complete submission, approved by contributor): not yet submitted
- Score history (date, score, what moved, and any pipeline re-anchor): 2026-09-15 difficulty record 100
- Leak audit (docs/DIFFICULTY.md): for each mechanism, what in the bundle could let an agent
  discover, name or verify it without reasoning? Answer must be "nothing": a page record carries
  its tokens and the page before it and nothing derived - no holder count, no reusable flag, no
  age, no strand size; no op reports the free count, the reusable set, a holder count or how far a
  walk reached; the shipped programs exercise the op language and the one wrong line the brief
  names and never put the pool under enough pressure to take back a page whose holder is still
  running; the model, the frozen answers and the pristine tree exist only in the verifier image,
  in a directory locked to root before any submitted code runs.
- Expert path, described step by step (the harder the aim, the more this guard must hold):
  1 run the shipped server on the small program in the brief and reproduce the wrong line;
  2 read the frozen step loop and learn that decodes run before fills and a fill stops on a page
  boundary; 3 work out that residency is the first and last tokens, so the pages a fill releases
  are the oldest in the pool; 4 rebuild the reuse index so a walk stops at the first page that is
  gone rather than matching content; 5 make a take-back drop the pages under it and let a fill ask
  for one page at a time, because one take-back can supply several; 6 work the case where a
  preemption supplies reusable pages rather than free ones; 7 handle a decode that completes a
  page whose tokens already sit under the same previous page; 8 generate wide programs at the
  stated scale and time the three naive families against the stated limit.
- Originality check: searched 2026-09-15 for the paged-cache-with-windowed-residency combination
  and for exercise-shaped versions of a block allocator. What exists is the design material this
  task poisons - a serving stack's own notes on block tables, reference counts, publishing full
  blocks to a reuse index, leaf-only eviction and preemption by recompute - plus papers on
  block-level eviction and one agent skill that simulates a block table. None of them describes
  residency narrowed to the first and last tokens, a take-back that strands what is under it, or a
  reuse walk that stops at a gap; no page plans this task, and the better the page the more
  confidently wrong the plan built on it.

## Instruction contract (docs/INSTRUCTION-CONTRACT.md, read before anything else)

Every graded assertion traces to a sentence in the instruction. Walk the tests, the sealed model
and test.sh line by line into authoring/<slug>/trace.md, start it with
`python tools/tracecheck.py <slug> --skeleton`, and keep `python tools/tracecheck.py <slug>` clean.
`preflight.py` errors while any line below is unanswered.

- Instruction trace (authoring/<slug>/trace.md; rows walked, NOT STATED left, tracecheck result): 106 rows walked - 4 test functions, 32 enumerated cases, 6 artifacts, the 60 second clock and 31 rules of the sealed model, each split out with its line range; no NOT STATED row survived, two sentences were added to the instruction during the walk (the release order of several pages at once, and what `at` prints for a token a request has not reached); `python tools/tracecheck.py page-window-reuse` is clean.
- Identifiability (readings enumerated, which survived the published evidence, what separated them): 25 readings were built as cheats and run against the enumerated set by `tools/readingcheck.py`. Two came back BLIND - a fill that releases its middle as it goes, and a released page kept as reusable when no walk can reach it - and two came back equivalent because the cheat did not express the reading (a sink-less residency whose release pointer still started at the sink, and a queue jump that only left the loop). Both cheats were fixed and two enumerated cases added (`fill-holds-middle`, `rest-strand-frees`); all 25 are now separated by a named case.
- Shortcut strategies scored (nop, constant, positional, replayed example; score and cases matched): the nop scores 0 with 27 of 33 tests failing; a constant line for every program, printing nothing at all, and the worked example replayed all score 0 and match at most one of 426 programs; the forgery carrying all 32 frozen answers passes every enumerated program and fails the 396 generated ones. Recorded in the Shortcuts table of trace.md.
- Independent implementation behind every tolerance and limit (path, measured headroom): the only limit is the 60 second wall clock on the worker. Validated against `authoring/page-window-reuse/variants/ok-heap` and `variants/ok-kids`, both written apart from the reference and both agreeing with the sealed model over 200 generated programs; the reference settles the whole graded set in 5.5 s, and the three naive-but-correct families measure 110 s, 144 s and 203 s.
- Undecided decisions from the cold-reader pass (author-run or fresh session; sentence or example added for each): author-run, mechanically over every printed token. Four decisions the first draft left open, each now stated: the order several pages released together are released in, which decides their age and so the next take-back; what `at` prints for a token the request has not reached; whether a prompt taken up but unable to write still prints a fill line; and whether a page still being written is below a take-back. The fresh-session form was not run - this session wrote the model, and a self-probe reported as cold by a contaminated author is worse than none.

## Verifier contract - FROZEN after Stage 2

Once agreed, this does not change without the contributor's explicit approval.

- Artifacts the agent produces: the six editable files, taken at their original paths -
  `/app/kv/pool.py`, `/app/kv/keep.py`, `/app/kv/live.py`, `/app/kv/fill.py`, `/app/kv/turn.py`,
  `/app/kv/put.py`. Nothing else is read from the agent's container.
- What is checked: the verifier lays those six files over its own pristine copy of `/app`, runs
  every graded program through the frozen driver, and compares the printed trace line for line.
  All or nothing, exact string equality, no tolerance. Hand programs are compared with frozen
  answers in `tests/seal/gt.json`; generated programs are compared with a sealed model written
  apart from the reference. The grader asserts the model still reproduces the frozen answers
  before it grades anything.
- Tolerances: none. The only limit is the wall clock on the stage that runs the submitted
  service, which is the execution limit stated in the brief.
- Ground truth, and where it lives: `tests/seal/model.py` and `tests/seal/gt.json`, in a
  directory locked to root before the submitted code runs.

### The ten graded decisions, frozen

1. A fill holds every page of its prompt, reused or written, until the prompt is complete, and
   then releases the pages outside its first and last tokens.
2. Residency is the pages holding the first `A` tokens together with the pages holding the last
   `S` tokens of the request's current length, recomputed as the length grows.
3. Reuse walks from the start of the prompt and stops at the first page that is gone, whatever
   still sits below it.
4. A page whose last holder releases it is reusable when the walk can still reach it, and goes
   back to the pool at once when it cannot.
5. A take-back takes the page released longest ago and returns, with it, every page below it that
   nobody holds; the pages below it that somebody holds stop being reusable for good.
6. A page is supplied by the lowest-numbered free page, failing that by a take-back, failing that
   by a preemption; a fill asks for one page at a time.
7. A preemption takes the request that became resident most recently, discards its progress, and
   ends the step; the pages it releases are reusable, not free.
8. A decode that completes a page whose tokens already sit below the same page gives its own page
   back to the pool and takes the one already there.
9. A step decodes one token for each resident request in residency order, then fills waiting
   prompts in arrival order, inside the token budget; reused tokens cost no budget and a fill
   stops on a page boundary.
10. A request that finishes, is cancelled, or is preempted releases everything it holds; a
    cancelled request that was never resident releases nothing and prints nothing.

### Prong C tactics in this contract, and the route-around guard

- C1: every decision above is graded from both sides - the ordinary case that an over-conservative
  service fails is enumerated beside the adversarial one.
- C2: no op reports the free count, the reusable set, a holder count or the depth a walk reached;
  the shipped server is wrong in six places, and the graded programs are generated from a seed
  drawn after the agent's container is gone.
- C3: three naive-but-correct structures are timed against the stated limit at the stated scale.
- C4: exact traces, all-or-nothing, enumerated programs per decision plus generated families.
- Guard: only the six files are artifacts. The driver, the op language, the program reader, the
  request table and the trace writer are the verifier's pristine copy, so the task cannot be
  reshaped into one the default plan handles.

## What was built, and what was measured

The environment is 377 lines of Python across ten files: a frozen driver, op language, page and
request records, and the six editable files under `/app/kv/`. The reference is 362 lines. The
sealed model is a second settlement of the same contract written apart from it - one class over
plain dicts, the window edge derived arithmetically, the reusable order a heap of stamps with
lazy deletion, the strand walked breadth first - and the two agree over 1,500 generated programs
across the ten small families. Two further correct variants (`authoring/page-window-reuse/variants/`)
agree over 300 each.

The execution limit is 60 seconds for the whole graded set. Measured on this machine: the
reference settles all 428 programs in about five seconds, and the three naive-but-correct
structures come in at 110 s (residency recomputed over every page of a request on each token),
144 s (the oldest release found by scanning the reusable pages) and 203 s (the reach of a
take-back found by sweeping the page table). All three produce exactly the reference's traces on
everything they finish.

Five defects were found by the local gates before any of this was packaged, and each is worth
recording:

- The first differential run disagreed on 6 of 200 programs. The cause was a page id being
  reused while an older page still named it as the page before it, with the reference and the
  model differing only by luck. The contract now says a page joins the tree when it is made
  rather than when it completes, which removes the ambiguity and makes the strand reach a page
  that is still being written.
- `tools/readingcheck.py` found two readings no enumerated case separated, and two cheats that
  did not express their reading at all: a sink-less residency whose release pointer still started
  at the sink, and a queue jump that only left the loop it was already leaving. Two cases were
  added and both cheats rebuilt.
- All eight isolation probes scored 0 while doing nothing: a double-escaped newline had left them
  with a SyntaxError. `emit.py` now parses every file it writes, which caught a ninth cheat with
  a `continue -1` in it on the next run.
- The first `wide` family made no take-back at all, because each request's single page never
  filled and an incomplete page is never reusable. Measured, not assumed.
- The first scale families were too small to separate anything: the naive residency reading came
  in at 3.4 s against a 60 s limit. The shapes changed until all three families were measured
  over the limit.

## Decisions and their reasons

- Category `ML` / subcategory `Inference`: the graded work is the memory manager of a serving
  stack - pages of token cache, residency, prompt reuse, admission and preemption. The vocabulary
  is in the tree, not only in the story.
- The event language is deliberately coarse: a fill line carries tokens reused and tokens
  written, a take-back carries the page and how many pages came back with it, and the only
  pointwise question is which page holds a given token of a given request. Nothing reports the
  pool's state directly, so a wrong structure is not confirmable one decision at a time.
- Programs are text, and the two wide families are written with a `bulk` shorthand so the
  shipped programs stay small.

## Stage 7 re-attack (D7)

Read cold against the built tree rather than against the plan.

Is the first plan still wrong? Yes, and in the same four places: whole-sequence residency, an
index matched on content, eviction of a page with nothing under it, and preemption before a
take-back. Nothing in the tree hints at any of the four; the shipped service commits three of
them, which is the confirmation an agent is most likely to take.

Are the load-bearing facts still distributed? The agent has to correlate what the frozen driver
reaches for (`ops.py` calls exactly four entry points), what a page record can hold (`store.py`
carries the tokens and the page before it, and nothing derived), the phase order and budget in
`turn.py`, and six files that ship wrong in six different ways. The brief states every rule; what
it cannot state is which structure survives all of them at once, which is the work.

Did the instruction come to telegraph the method? The sentence added during the trace walk about
a take-back reaching a page that is still being written is the closest, and it is a graded rule
that has to be stated. It names the consequence rather than the structure: nothing says the
reach of a page is inherited when the page is made, which is what an implementation has to work
out.

Estimated solves, unchanged: 2 of 8. The residual risk is the one the doctrine names for a task
aimed at the hard edge - a large conjunction graded all or nothing returns zero more often than
it returns one - and the scale gate sits on top of it, so a semantically correct service with a
sweep in the wrong place still fails.

## Quality self-review (docs/QUALITY-REVIEW.md, criterion by criterion)

Instruction against verifier, both directions: `authoring/page-window-reuse/trace.md` carries a
row for every test function, enumerated case, artifact, clock and rule of the sealed model, each
against the sentence that states it; `tools/tracecheck.py` checks the quotes are still in the
file. The six artifacts are named with absolute paths in the second paragraph of the brief. The
printed format is specified line kind by line kind in the seventh. Boundaries and conventions
that are settled in the text: pages numbered from 1, the lowest numbered free page, the page
released longest ago, residency as any of the first `a` and any of the last `s` tokens, the order
several pages released at once go in, reuse costing no budget, and what `at` prints for a token a
request has not reached. Counts in the prose were re-derived from `gen.programs` and `cases.ORDER`
after the last generator change: 32 enumerated, 396 generated, 428 in all.

Instruction prose: read end to end against a retained brief that passed the screen
(`tools/textcheck.py tasks/note-carry-forward/instruction.md ...`) - no finding on any axis after
one pass that broke three long sentences and merged two paragraphs. No run of same-structured
sentences survives; each requirement is stated once.

Verifier rigor: the tests read a trace the submitted service printed while running 428 programs,
not a claim about itself; `tests/test_outputs.py` documents the frozen contract and each section
names the behaviour it checks; the only clock is the stated execution limit and the generated
population is seeded.

Environment hygiene: `environment/Dockerfile` copies `app_src/` and nothing else; the verifier
image installs pytest 9.1.1 and the CTRF plugin at build time and `tests/test.sh` touches no
network; every path the brief names exists in the tree under that spelling.

Solution quality: `solution/solve.sh` copies the six reference modules into `/app/kv/` and runs
the shipped programs; nothing is echoed into an artifact the verifier reads.

Anti-cheating: the model and the frozen answers live in `tests/seal/`, `chmod 700` before any
agent code runs, and `cheat-probe-answer-key` records the `PermissionError`; no page record
carries a holder count, a reusable flag, an age or a strand size; the 37 cheats include the
shipped tree, a constant, a positional strategy, the replayed example and the answer key.

Metadata: `ML` / `Inference` with the machinery in the tree rather than in the story
(`tools/catcheck.py`: 25 environment hits); six tags naming the mechanisms, none restating the
taxonomy; `difficulty_explanation` names the four structures the prior gets wrong and says the
naming register is deliberate; `expert_time_estimate_hours = 10` matches the eight-step expert
path.

Known risk a reviewer should weigh: the oracle, nop and cheat evidence is host emulation rather
than container evidence, for the reason recorded below.

## Validation status

| Check | Status | Notes |
|---|---|---|
| Difficulty record scored | pass | 100/100 before any code, and again at Stage 7 with the tree measured |
| Reference against the sealed model | pass | 1,500 generated programs over ten families, 0 differ |
| Correct variants against the model | pass | `ok-heap` and `ok-kids`, 300 programs each |
| Agent image builds | not run | no Docker daemon in this session; `tools/imagecheck.py` assembles what the image would hold and runs the shipped programs in it - clean |
| No answer leaked into agent image | pass | `environment/Dockerfile` copies `app_src/` only; `extraneouscheck` and `imagecheck` clean |
| oracle = 1 | pass, host emulation | `authoring/page-window-reuse/host_trial.py oracle`, test.sh run verbatim as root with the real privilege drop; harbor is not installed here |
| nop = 0 | pass, host emulation | 27 of 33 tests fail |
| Cheats all score 0 | pass, host emulation | 37 of 37, plus oracle and nop, in one sweep |
| Which layer catches each cheat | pass | `cheat_report.py`: every reading named by an enumerated program, the three naive families measured over the limit, the forgery reproducing all 32 enumerated programs and none of the generated ones |
| `readingcheck.py` | pass | 25 readings, all separated by a named case |
| `onelinecheck.py` | pass | no graded quantity has an exact rule at depth <= 2 |
| `tracecheck.py` | clean | 106 rows, no NOT STATED |
| `preflight.py` | pass | no errors; 18 warnings, all of the class the retained bundles carry |
| `catcheck`, `structcheck`, `textcheck`, `hintcheck`, `deadfieldcheck`, `simcheck`, `forgecheck`, `solvecheck`, `imagecheck`, `extraneouscheck` | pass | |
| `harbor check` rubric | not run | harbor is not installed in this session |
| Cold self-attack | not run, deliberately | this session wrote the model; a self-probe reported as cold by a contaminated author is worse than none (CLAUDE.md). The reading separations, the shortcut scores and the no-oracle property stand in its place |

## Open questions and next steps

Packaged and delivered. What a reviewer should know:

- Docker has no daemon in this session and harbor is not installed, so the oracle, nop and cheat
  results are host emulation - `tests/test.sh` run verbatim as root, with the real privilege drop
  to uid 1002, the real wall clock, the real reap and the real reward channel, but without an
  image build or filesystem isolation between the two stages. Container evidence is container
  evidence; this is not it, and the Stage 4 and Stage 7 harbor runs remain to be done wherever
  Docker works.
- The 60 second limit was measured on this machine. The reference has roughly an order of
  magnitude of headroom, so a slower runner is not a risk to solvability; the naive families sit
  at 1.8x to 3.4x over the limit, so a much faster runner would be.
- The easiness probe has not run. The design is aimed at the hard edge of the band (2 of 8), and
  the honest residual risk is the one the doctrine names: a task aimed at 1 comes back 0 about a
  third of the time.
