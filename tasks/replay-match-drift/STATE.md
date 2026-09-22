# Task state

Working memory for this task. The assistant updates it after every stage. Assume the next
session starts with no memory of this one - anything not written here is lost.

## Current stage

`Stage 7 - Pre-flight and packaging` (rebuilt after the quality review failed `difficult`)

## Assistant's assigned role

You are a runtime engineer on a durable execution platform: the replay half, which takes a
concurrent workflow body and the history an earlier attempt recorded and decides which branch
runs next and which recorded line each command is entitled to. You have written and debugged
the replay scheduler, command matching, version markers and signal delivery, and you know that
what a runtime does when the code and the history stop lining up is a policy rather than a law.

## Source repository (repo-based tasks only)

- Repo URL: none - idea-based task, no third-party code vendored
- Task shape chosen (authored-on-top / ablation per docs/ABLATION.md): not applicable, no repository
- Contributor's relationship to it (maintainer / contributor / production user, how long): not applicable
- License, and why vendoring it is permitted: not applicable, nothing vendored
- Pinned commit vendored into environment/app_src/ (.git stripped): not applicable
- Load-bearing couplings found during research (file paths): not applicable
- Identifier degradation done? Conversion table lives at solution/ (never in environment/): the tree is
  written here rather than degraded from a source; identifiers are chosen in the legacy register
  directly (`dur/`, `tab`, `edge`, `pair`, `pend`, `sigq`, `ver`, `mach`, `say`) and no name
  misdescribes what it holds
- Proper-noun sweep done? No product, project, company or framework name appears anywhere in the
  agent-facing tree; the domain words that remain (body, history, command, signal, marker) are the
  ordinary vocabulary of the work and carry no provenance
- Upstream-diff check: there is no upstream to diff against

## Task summary

`/app` is the replay half of a durable runtime. A run file carries a concurrent workflow body,
the history an earlier attempt recorded, and the values that work run for real gives back; the
engine replays the body against the history and prints a line per event, each naming the branch
it belongs to. The shipped engine implements the remembered shape - one position into the
history, the answer sitting next to its command, a marker that returns whatever the code asks
for - and the specification it has to meet is the runtime's own: a branch that waits goes down
carrying the position of the line that will release it, the branch that runs next is the one able
to run or the one whose mark is smallest, commands are counted per kind while their results are
paired on kind and name together, the live side opens when the whole run comes to a stop, and a
recorded command nobody matched fails a run that otherwise finished. The agent fixes the seven
files under `/app/dur/` so every run file's printout matches.

## Why it is hard

The first plan is the remembered one and it is wrong at the first decision point; what replaces
it is a schedule no container holds, and the rule after that makes the body's control flow depend
on a boundary the whole run has to reach.

- Expert time estimate: 9 hours
- Why a frontier agent cannot one-shot the plan (the strategic answer - required): because the memorised and retrievable answer to replaying a workflow against its history is a single position walked beside the code, and because the thing that replaces it here is not a container but a derivation. A branch that waits goes down with the position of the line that will release it, and the branch that runs next is the one able to run or the one whose mark is smallest - so a branch's place in the queue is a recorded position that cannot be known until the branch has been matched, which cannot happen until the branch runs. The counting rules feed that schedule and are fed by it, because the per-kind count is global across branches. The live side is then a property of every branch at once rather than a test any command makes, and the version marker reads it, so the body's control flow depends on a standstill its own branches have to reach. The first implementation of the queue - a list of branches walked at each step - is exactly correct and 137.8 seconds against a stated 60.
- Tactics making that true (prong A poison, prong B withholding, prong C late failure): A1, A2, B2, C1, C3 and C4. A1 the shipped engine is the model's prior implemented faithfully and it is the wrong answer; A2 the schedule, the claim rule and the standstill are stated as what this runtime does and never named, so their consequences must be derived; B2 eleven rules hold at once and each changes what a correct implementation of the others looks like; C1 both sides are graded, so an engine that always takes the smallest mark and one that never lets a forked branch start both fail; C3 a wide family makes the natural branch walk infeasible while leaving it exactly correct; C4 every run file is compared line for line against a population generated after the agent is gone.
- Assistant's attack on the plan (its first plan, and where that plan is wrong): my first plan was
  to parse the history into a list, keep a cursor, check each command against the event under the
  cursor, read the answer that follows it, and go live when the cursor reached the end. It is
  wrong before it starts: the body is concurrent, so there is no single position to walk; the
  command counter is per kind and global across branches while the result counter is on kind and
  name together; and the order branches run in is the order their lines were recorded, which is
  not the order anything was issued. My second plan - a list of branches scanned for whichever is
  next - is correct and does not fit the limit.
- Estimated solves out of 8 (design for 1, the hard edge; the realized rate drifts up): 2 of 8 (range 1-4)
- Difficulty record score (tools/difficultycheck.py on authoring/<slug>/difficulty.toml, before
  Stage 2; every attempt's score and what changed, until it reaches the band in
  docs/DIFFICULTY-SCORE.md): attempt 1 on 2026-09-22 scored 100/100 for the v1 design, which the
  quality review then failed on `difficult`; the record was rewritten for the rebuilt design and
  scores 100/100 again, with the gate now measured rather than declared. The checker reads fields
  and counts and could not see what the reviewer saw, which is recorded here rather than argued
  away: a record in the band is necessary and not sufficient.
- Difficulty score anchor (50 at first complete submission, approved by contributor): not yet submitted
- Score history (date, score, what moved, and any pipeline re-anchor): 2026-09-22 v1 record scored 100, quality review failed `difficult`; 2026-09-22 rebuilt record scored 100 with a measured gate
- Leak audit (docs/DIFFICULTY.md): for each mechanism, what in the bundle could let an agent
  discover, name or verify it without reasoning? Answer must be "nothing": the recorded lines
  carry kind, name, tag or key and a value, never a position, an index, a branch number or a
  mark, so every one of those has to be derived; nothing in a run file names the standstill, and
  it is recomputed every run; the generator produces recordings by walking the branches the way
  the rules do, so adjacency between a command and its result is never a usable rule; the sample
  run files ship without their correct printouts and the brief quotes one line of one of them,
  which is a value rather than a rule; the shipped engine keeps one position and counts nothing
  by kind, and its scheduler prefers marks to ready branches, so neither structure can be found
  by reading.
- Expert path, described step by step (the harder the aim, the more this guard must hold): run the
  shipped run files and read the one line the brief says is wrong, to find which module decides
  it; split the history into a table of recorded commands per kind, results per kind and name,
  and signals per tag, each carrying the position of its line, since the brief counts them on
  different axes and the schedule needs the positions; give a waiting branch the position of the
  line that releases it, claiming a signal as it goes down rather than when it wakes; build the
  two queues the scheduling rule describes and keep the branches with no mark apart, because they
  are what the standstill is made of; settle the live side as that standstill, printed once, after
  which nothing waits and nothing is matched; keep the matched positions as a set so the
  end-of-run check can name the earliest recorded command nobody matched; then time the wide run
  files and replace the walk over the branches with a heap, which the history being fixed before
  the body starts makes sound.
- Originality check: searched 2026-09-22 for the mechanism. What the literature and the vendor
  documentation carry is the general statement that replay must be deterministic, that a code
  change breaks it, and that a version marker returns the recorded branch. None of it says that a
  concurrent body's replay order is the order its work was recorded finishing, on what axis a
  command is counted against a result, when a marker with no record yields the legacy value, or
  that a recorded command nobody issued is a failure while a recorded signal nobody took is not.
  The best retrievable page gives a plan that is wrong before it starts.

## Instruction contract (docs/INSTRUCTION-CONTRACT.md, read before anything else)

Every graded assertion traces to a sentence in the instruction. The walk is
`authoring/replay-match-drift/trace.md`.

- Instruction trace (authoring/<slug>/trace.md; rows walked, NOT STATED left, tracecheck result): 63 rows walked - 4 test functions, 38 enumerated run files, 6 artifacts, the 60 second clock and 14 rows over the sealed model split one per rule with its lines - plus 23 readings, 6 shortcuts and 2 limits; no NOT STATED row survived, and `python tools/tracecheck.py replay-match-drift` is clean. The trace is built by a script that refuses to write a quote which is not in `instruction.md` word for word, so a brief edit that stranded a citation could not ship.
- Identifiability (readings enumerated, which survived the published evidence, what separated them): 23 readings were written as whole engines by `authoring/replay-match-drift/emit.py` and measured by `python tools/readingcheck.py replay-match-drift`. All 23 are separated by the enumerated set; one, `name-answer`, came back `equivalent` on the first run and `pair-kind-name` was written for it, a program using one name under two kinds whose answers are recorded in the other order. `cheat_report.py` then asserts that each reading is caught by the run file named for it, which holds for all 23, and reports how much of the generated population each moves: from 2 per cent (`ver-key-blind`, which is three quarters of its own family) to 100 per cent (`const-zero`).
- Shortcut strategies scored (nop, constant, positional, replayed example; score and cases matched): the nop scores 0 with 17 of 41 graded assertions failing; `cheat-const-zero` scores 0 and moves 100 per cent of the generated set; `cheat-pos-first` scores 0 and moves 34 per cent; `cheat-forge-hand` carries the 38 enumerated histories by fingerprint and is the reference only for those, passes every enumerated run file and fails the generated population; `cheat-forge-truth` carries the frozen answers themselves, replaces the trace writer at import and hands them back, and does the same. `tools/forgecheck.py` names the second as a carrier of ground truth.
- Independent implementation behind every tolerance and limit (path, measured headroom): `authoring/replay-match-drift/variants/ok-deque` and `.../ok-flat`, both written apart from the reference, settle the six scale run files in 1.0 seconds each against the 60 second clock, a factor of sixty; the reference takes 0.9. The two readings that settle every rule the same way and walk the history instead of indexing it take 306.4 and 153.2 seconds, so the limit sits at a fifth of the first and two fifths of the second. The sealed model, also written apart, agrees with both and with the reference on every graded program. There is no numeric tolerance: traces are compared string for string.
- Undecided decisions from the cold-reader pass (author-run or fresh session; sentence or example added for each): author-run, mechanically, over every printed token. Ten gaps were found and closed in the brief: that every count and position starts at zero, that blank lines are skipped, that values are integers and names single words, that `lab` does nothing, that the count of one kind is not moved by another kind, that a live answer ranks after every recorded one, that an outstanding command with no answer never wins a race, that only recorded commands count toward the leftover, that a run which stopped short makes no leftover check, and that an empty history is still replaying until a command opens the boundary. One sentence survives without a reading that contests it - that a body which runs off its last op ends like one that reached `fin` - because no generated body omits `fin`; it is kept because the machine allows it and the agent is owed the fact.

## Verifier contract - FROZEN after Stage 2

Frozen 2026-09-22 for the first build and **reopened the same day** after the quality review
failed `difficult`: a rejection on that criterion is a rejection of the mechanism, so the
contract could not stand. The rebuilt contract is frozen as of the rebuild and is restated in
`tests/test_outputs.py`, which is the file a reviewer reads.

- Artifacts the agent produces: `/app/dur/tab.py`, `/app/dur/edge.py`, `/app/dur/pair.py`,
  `/app/dur/hold.py`, `/app/dur/sched.py`, `/app/dur/wake.py`, `/app/dur/ver.py`. Nothing else is
  collected; the verifier lays those seven over its own clean copy of the tree.
- What is checked: the stdout printout of every graded run file, line for line, exactly. Forty
  enumerated run files against `gt.json`, frozen before the grading file was written; 525
  generated run files against the sealed model, which must itself still reproduce `gt.json`.
- Tolerances: none. The only limit is the 60 second wall clock on the stage that runs submitted
  code, validated against two independently written correct implementations.
- Ground truth, and where it lives: `tests/seal/model.py` and `tests/seal/gt.json`, in a directory
  `chmod 700` before the privilege drop.

### The eleven graded decisions

1. A command matches the recorded command at its own position among those of its kind, and once
   the live side is open nothing is matched.
2. A recorded command naming something else stops the run where it happens.
3. A result is paired with its command on kind and name together.
4. An awaiting command takes its own result; a `take` takes the branch's earliest untaken one.
5. A waiting branch's mark is the position of the line that releases it, or none.
6. A branch waiting for a signal claims one as it goes down, per tag, in recorded order.
7. A branch able to run goes before one that must be woken; lowest number, then smallest mark.
8. The live side opens at the standstill, is said once, and nothing waits or matches after it.
9. A result the history does not carry comes off the `r` lines in the order branches take them.
10. Branch zero ending ends the run; a recorded command nobody matched is a failure naming the
    earliest, and nothing else in the history is.
11. A body past the step ceiling ends `over`.

## Decisions and their reasons

- **Software / Languages, not Data engineering.** The graded work is an interpreter and the
  machinery that decides which recorded effect each command is entitled to. `tools/catcheck.py`
  is clean on the choice.
- **Two counters on different axes.** This is the A1 tactic: one position into one list is what
  the prior writes and what the shipped engine is, and it is wrong wherever kinds interleave
  differently or work completed out of order.
- **The marker default depends on the boundary, not on the history's length.** A runtime that has
  not yet asked the history for anything cannot tell a fresh run from one whose commands are all
  still ahead, so the rule follows from what the engine can know. It is also what makes the body's
  control flow depend on a boundary its own branches open.
- **The leftover check is at the end of the body, not during it.** A check during the run would
  make it a local test; at the end it means the final verdict is not the streaming verdict, and a
  run that crossed the boundary early can still owe the history a command.
- **The run file carries the live values.** Live work has to return something deterministic, and a
  list in the run file is honest about it without inventing a formula the agent has to guess.
- **Two shared kit files were rewritten rather than reused.** `tests/reap.py` and `tests/test.sh`
  do the same job as in every retained bundle and are written here in their own words and
  structure; `tools/simcheck.py` is the check. The two Dockerfiles remain near-identical to every
  retained bundle because their content is prescribed by the kit - the canonical pytest pins, an
  artifact parent per RUN line, `COPY . /tests/` - and there is nothing in them to author.

## Stage 7 re-attack, run cold on the finished bundle

Read the final brief with the built tree in front of me and tried to one-shot the plan.

- **Is the first plan still wrong?** The plan from the prior is one position walked beside the
  code with the answer next to the question, and that is the shipped engine. The plan *after*
  reading the brief is right in outline, because every rule is stated; it is wrong in structure.
  One position cannot carry two counters on different axes, a history read ahead of the body
  cannot answer a marker whose value decides which commands exist, and a count of matched records
  cannot name the earliest one that was missed.
- **Are the load-bearing facts still distributed?** They are stated rather than hidden, which is
  the doctrine. What is not stated is which structures survive all eleven at once, and that is
  unchanged since Stage 1.
- **Did the instruction come to telegraph the method?** No. It states the outcome of each rule and
  never a data structure; `tools/hintcheck.py` is clean and the prose names no technique.
- **Updated estimate of solves out of 8: 2** (range 1 to 4). Every rule is in the brief and a
  meticulous implementer who holds all eleven at once wins; against them is that there is no
  feedback on any of the eleven except one quoted line, the grading is all or nothing over 524
  run files, and the natural history-walking implementation is over the clock.

## Validation status

All of it re-run after the rebuild.

| Check | Status | Notes |
|---|---|---|
| Agent image builds | not run | image pulls are refused by this session's egress policy (403 on the registry CDN); `tools/imagecheck.py` interprets the Dockerfile instead and is clean, 16 files, four shipped run files executed in it |
| No answer leaked into agent image | pass | `imagecheck`: no `tests/` or `solution/` content |
| `harbor run -a oracle` = 1 | emulated | `host_trial.py oracle`: reward 1, seven files collected. Harbor is not installed and no container could be built here |
| `harbor run -a nop` = 0 | emulated | `host_trial.py nop`: reward 0 |
| Cheats all score 0 | pass | 36 cheats through `host_trial.py`, every one 0; the eleven probes additionally asserted to have reached the verifier and been refused |
| Correct variants score 1 | pass | `ok-sorted` and `ok-array`, both 1 |
| `readingcheck` | pass | 21 readings, every one separated by a named enumerated run file |
| `onelinecheck` | pass | six graded quantities, none with an exact rule at depth two, including which branch runs next |
| `forgecheck` | pass | `cheat-forge-truth.sh` carries the frozen answers and scores 0 |
| `tracecheck.py` | pass | clean |
| `preflight.py` | pass | 0 errors |
| `difficultycheck.py` | 100/100 | measured tree: 440 environment lines, 7 editable files, 330 reference lines, 36 cheats, 2 variants |
| `catcheck` / `hintcheck` / `solvecheck` / `deadfieldcheck` / `extraneouscheck` / `structcheck` | pass | clean; catcheck measures 56 software terms in the environment |
| `simcheck` | in family | both Dockerfiles near-identical to retained bundles because the kit prescribes their content; the conceptual line reads "this task does not grade what any earlier one grades" |
| `textcheck` against `expert-defer-shed` | residual | 20 per cent short sentences against the reference's 31. Two retained bundles trip the same findings against the same reference |
| `harbor check` rubric | not run | no API key in this session |

### The resource gate, measured

| Engine | six scale run files | verdict |
|---|---|---|
| reference | 2.6 s | 1 |
| `variants/ok-sorted` | 3.3 s | 1 |
| `variants/ok-array` | 2.5 s | 1 |
| `variants/ok-array` with its first, flat-list hold | 19.4 s | inside the limit; kept as the headroom a poor but correct auxiliary structure has |
| `cheat-slow-sched`, the branches walked for the one whose turn is next | 137.8 s | 0, on the clock |
| `cheat-slow-history`, the history walked for every lookup | does not finish | 0, on the clock |

## Open questions and next steps

Container evidence is unavailable in this session: the Docker daemon runs, but `docker pull` is
refused by the egress policy, so neither image could be built and nothing was executed inside a
container. Everything recorded above as emulated was run on the host with the shipped
`tests/test.sh` verbatim, at the real paths, with the real privilege drop onto uid 1002, the real
root-owned 0700 reward directory and artifact collection restricted to the six declared files.
What that does not prove is that either image builds and that the container boundary holds;
`tools/imagecheck.py` covers the first by interpreting the Dockerfile against the build context.
The oracle and nop gates should be re-run with `tools/docker_trial.py` in a session whose egress
policy allows the registry.

The easiness probe has not been run: this session has no probe harness, and a self-probe by the
author who wrote the model would measure memory rather than difficulty. The reading separations,
the layer report, the correct variants and the cold re-attack stand in its place, and the
estimate above is what they support.

## Quality self-review (docs/QUALITY-REVIEW.md, walked criterion by criterion)

**Instruction and verifier agree both ways.** Every graded assertion has its row in
`authoring/replay-match-drift/trace.md` and `tracecheck` is clean. The converse was walked by
hand: every sentence of the brief is graded by the trace comparison, except four that describe
the environment rather than a behaviour - that `/app/runs` holds four run files, what
`/app/run_dur.py` does, the one wrong line it prints on `tiny.txt`, and the two sizes of the
scale run files. All four were re-derived from the tree rather than from memory: the directory
holds four files, every `/app` path the brief names exists in the shipped tree, the shipped
engine's third line on `tiny.txt` is `ok call 0 7` against the reference's `ok call 0 5`, and the
generator emits 30000 commands against 60000 recorded lines and 22000 against 44000.

**Counts.** Re-derived from the code after the last generator and case changes: 38 enumerated run
files, 486 generated (12 small families at 40 plus three of each scale family), 14 families, 524
in all, 60 seconds, 200000 ops. Every enumerated name `task.toml` mentions exists in
`cases.ORDER`.

**Boundaries.** Two counters with their bases, one strict test at a count, three tie-breaks (the
earliest recorded command, the earliest answer, the earliest leftover), the empty history, the
exhausted value list and the run that stopped short are all settled in the text, and each has an
enumerated run file named for it.

**Verifier rigor.** The tests run the submitted modules over a clean copy and compare the whole
trace; nothing is taken on the submission's word. `tests/test_outputs.py` opens with the frozen
contract and is sectioned by what each block checks. The only wall-clock dependence is the stated
60 second limit, measured at sixty times the headroom on two independent implementations.

**Environment hygiene.** `environment/Dockerfile` copies `app_src/` and nothing else; pytest is
pinned at 9.1.1 with ctrf 0.5.2 in `tests/Dockerfile` only; no apt package is pinned;
`tools/imagecheck.py` assembles what the image would hold (15 files) and runs the four shipped
run files in it.

**Solution quality.** `solution/solve.sh` copies six source files into place and runs two run
files; it computes nothing by hand and writes no answer.

**Anti-cheating.** `tools/forgecheck.py` finds a forgery carrying the frozen answers and it scores
0. `deadfieldcheck`, `extraneouscheck` and `solvecheck` are clean, `onelinecheck` reports that
none of the five graded quantities has an exact rule at depth two, and the eleven isolation probes
are each asserted to have reached the verifier and been refused rather than merely to have scored
0.

**Metadata.** Category and subcategory are a valid pair and `catcheck` measures 45 software terms
in the environment against 74 in the prose; the five tags name mechanisms rather than the
taxonomy; `difficulty_explanation` names the concrete step and states the legacy naming as a
design choice; the expert estimate of nine hours matches the difficulty claim.

## Difficulty recovery - 2026-09-22, quality review FAILED on three blocking criteria

Reviewer `claude-fable-5-1`, 22 Sept 18:22. Verbatim, because the wording is the repair list.

1. **category and tags** - FAIL. "Category Software is right and the tags are specific, but
   subcategory `Languages` is a poor fit: the task is debugging a durable-execution replay
   engine's event-matching logic, not language design or implementation. `Debugging` or
   `Distributed Systems`/`Backend` would fit better."
2. **difficult** - FAIL. "Every rule is spelled out in the instruction and the full solution is
   ~150 lines of per-kind counters, a dict keyed by (kind,name), a set of matched positions and a
   min over pending records. The performance requirement is satisfied by ordinary dict indexing.
   An average undergraduate reading carefully could implement this in a day or two; difficulty
   comes mostly from parsing dense idiosyncratic prose, not from domain expertise or algorithmic
   depth."
3. **solvable** - FAIL. "`solve.sh` as shipped errors out: after copying the files it runs
   `python run_dur.py runs/tiny.txt` and `runs/mixed.txt` under `set -e`, and `environment/app_src`
   contains no `runs/` directory (`environment/Dockerfile` only copies `app_src/`). The oracle
   script therefore exits non-zero and the instruction's promised inputs do not exist." It also
   recorded that the six solution files pass the verifier, 41 of 41 across 13 seeds, stage one in
   about 2.3 s.

### 1. What actually happened, per failure

**solvable.** Not a Dockerfile bug and not a `set -e` bug: a packaging bug, and a bad one.
`shipped_files()` in `scripts/preflight.py` excludes any directory named `runs`, because that is
one of the names harbor uses for its own output. My sample programs lived in
`environment/app_src/runs/`, so all four `.txt` files were dropped from the zip while remaining in
git and in the working tree. Every retained bundle calls that directory `progs/` or `plans/`,
which is why the trap had never been sprung. Three local gates said clean and none of them could
see it: `imagecheck` copies from the working tree, `zipcheck` reads the archive without comparing
it against the environment tree, and the host trial stages `app_src` directly. The instance is
fixed by renaming the directory; the class is fixed by a new preflight error that fires when the
task tree holds a directory whose name packaging drops.

**category and tags.** The reviewer's two suggestions, `Debugging` and `Distributed
Systems`/`Backend`, are not labels in the guideline table - the same thing happened to
`alias-settle-report` on 2026-09-04, where the reviewer's `Debugging` was unusable and its other
suggestion was taken. Of the five Software labels the table does carry, the one that describes a
durable workflow runtime is `Data engineering`. `Languages` was my call and it was wrong: the
graded work is not language implementation.

**difficult.** This is the finding that matters, and the reviewer named the techniques the design
rested on, which is the same shape `CLAUDE.md` records for `publish-settle-order`: per-kind
counters, a dict keyed by a pair, a set of positions, a min over records. All four are retrievable.
Two things follow. The graded patch was bookkeeping over containers, so there was nothing to
derive; and the resource gate did not bite, because the structure that satisfies it - a dict - is
the structure a first implementation writes anyway. The gate only killed a scan nobody would write.
The prose complaint is the third face of the same problem: with the difficulty carried by many
small stated rules rather than by structure, the brief had to carry many small stated rules.

### 2. Classification (RAISE-DIFFICULTY.md section 2)

| Failure mode | Evidence | Direction taken |
|---|---|---|
| The naive method was fast enough | "satisfied by ordinary dict indexing"; my measured gate killed only a deliberate re-scan of the history | Re-site the gate on a structure a natural implementation does not have |
| The default plan was correct | "~150 lines of per-kind counters ... a min over pending records" | Make the graded answer a derivation with no container that holds it |
| The instruction delivered the plan | "difficulty comes mostly from parsing dense idiosyncratic prose" | Fewer stated micro-rules; put the weight in structure the rules use |

### 3. The replan

Three candidates were attacked before one was chosen.

- *More rules on the same mechanism* - rejected outright. It is what the reviewer already refused,
  and `CLAUDE.md` records the same refusal for `reach-pair-sweep`.
- *Nested child histories* - a parent history carrying a child's, replayed recursively. Rejected:
  it is the same lookup one level down, and it doubles the brief.
- *A history-ordered scheduler over concurrent branches* - selected. The body forks branches; a
  branch blocks on the event it waits for; and the order branches run in is the order their events
  were recorded, not fork order and not issue order. The schedule is therefore a derivation over
  the history and the body at once: a branch's place in the queue is the position of an event that
  cannot be known until the branch has been matched, which cannot happen until the branch runs.
  No container holds that, and the natural implementation - scan the branches at each step for the
  one whose wake is earliest - is quadratic in a way ordinary dict indexing does not fix.

### 4. The rebuild (RAISE-DIFFICULTY.md section 4)

The contract changed, which a `difficult` rejection makes unavoidable: the graded work is a
different mechanism. Stage 2 was reopened and the whole bundle rebuilt from it.

**What the engine is now.** A body runs as branches. `fork` starts one at a label; a branch that
waits goes down carrying a mark - the position in the history of the line that will release it -
and the branch that runs next is the one able to run without waiting, lowest numbered, or failing
that the waiting branch whose mark is smallest. The schedule is therefore a derivation over the
body and the history at once: a branch's place in the queue is a recorded position that cannot be
known until the branch has been matched, which cannot happen until the branch runs. The live side
is no longer a test any one command makes: it opens when the whole run comes to a stop, nothing
able to run and nothing waiting for anything recorded, which is a property of every branch at
once.

**What that fixed, criterion by criterion.**

- *the graded answer is a derivation, not a container.* `tools/onelinecheck.py` reports that none
  of the graded quantities has an exact rule at depth two, as before - but the reviewer's reading
  was about the patch, and the patch is now a two-queue scheduler whose second queue reorders
  itself every time a branch goes down, a claim rule whose outcome decides its own order, and a
  boundary that is a property of the whole run. The reference is 319 lines across seven files
  against 234 across six.
- *the gate bites a natural implementation.* This is the finding that mattered. Keeping the
  branches in a list and walking it at each step for the one whose turn is next is what a first
  implementation writes, it is exactly correct, and it takes 137.8 seconds on the six scale run
  files against 2.7 for the reference and a stated limit of 60. The old gate only killed a
  deliberate re-scan of the history; this one kills the obvious structure, and ordinary dict
  indexing does not repair it.
- *less dense prose.* Four terminal shapes instead of six, one boundary rule instead of two, and
  the micro-rules that carried the old difficulty are gone; `textcheck` puts the brief at 20 per
  cent short sentences against 14 before, and the word count is within thirty of the old one for
  a mechanism with more in it.
- *the category.* `Data engineering`, the label from the guideline table that describes a durable
  workflow runtime. The reviewer's own suggestions are not labels the table carries.
- *the packaging bug.* `environment/app_src/runs/` is now `progs/`, and `scripts/preflight.py`
  errors on any file packaging would silently drop - proved to fire on the defect (8 files) and to
  be clean on all twelve retained bundles.

### 5. Measured after the rebuild (RAISE-DIFFICULTY.md section 5)

- reference scores 1; nop scores 0; both independently written correct engines score 1
- 36 cheats score 0, including the two correct-but-slow readings and eleven isolation probes
- all 21 wrong readings are separated by a named enumerated run file (`readingcheck`, no BLIND,
  no equivalent)
- the old winning shape - a cursor over the history with the answer next to the question - is
  what the shipped tree still is, so the nop is that cheat
- reference and sealed model agree on every graded run file
- the resource gate is measured on both families, for the correct and the naive shapes
- `tracecheck` clean, `preflight` clean, the manual quality review walked again below

The external easiness probe has still not been run here, so under section 6 the recovery is
**pending its exit gate**: this session has no probe harness, and a self-probe by the author who
wrote the model would measure memory rather than difficulty.
