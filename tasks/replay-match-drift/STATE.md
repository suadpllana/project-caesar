# Task state

Working memory for this task. The assistant updates it after every stage. Assume the next
session starts with no memory of this one - anything not written here is lost.

## Current stage

`Stage 7 - Pre-flight and packaging`

## Assistant's assigned role

You are a runtime engineer on a durable execution platform: the replay half, which takes a
workflow body and the history an earlier attempt recorded and decides, command by command,
which recorded event each one is entitled to. You have written and debugged command matching,
version markers and signal delivery, and you know that what a runtime does when the code and
the history stop lining up is a policy rather than a law.

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

`/app` is the replay half of a durable runtime. A run file carries a workflow body, the history
an earlier attempt recorded, and the values that work run for real gives back; the engine replays
the body against the history and prints a line per event. The shipped engine implements the
remembered shape - one position into the history, the answer sitting next to its command, a
marker that returns whatever the code asks for - and the specification it has to meet is the
runtime's own: commands are counted per kind, answers are paired on kind and name together,
one boundary opens for the whole run, a marker with no recorded choice answers for the code that
wrote the history, and a recorded command the body never issued fails a run that otherwise
finished. The agent fixes the six files under `/app/dur/` so every run file's trace matches.

## Why it is hard

The first plan is the remembered one and it is wrong at the first decision point; the rule that
replaces it needs two counters where the plan has one, and the rule after that makes the body's
control flow depend on the boundary the commands themselves open.

- Expert time estimate: 9 hours
- Why a frontier agent cannot one-shot the plan (the strategic answer - required): because the memorised and retrievable answer to replaying a workflow against its history is a single position walked beside the code, with the answer next to the question and the live side beginning where the history ends. Here a command is counted among the commands of its own kind while its answer is
  paired on kind and name together, and answers are recorded in completion order rather than
  issue order, so one position cannot express either counter. Then the version marker makes the
  body's branch depend on whether the boundary has already opened, while the boundary is opened
  by the commands that branch issues, so the history cannot be walked ahead of the body or turned
  into a command plan. A plan that reads the history has to be turned around into one that asks
  it, and the wrongness shows up only in a position and a value on one line of a printout.
- Tactics making that true (prong A poison, prong B withholding, prong C late failure): A1, A2, B2, C1, C3 and C4. A1 the shipped engine is the model's prior implemented faithfully and it is the wrong answer; A2 the counting, pairing, boundary and leftover rules are stated as what this
  runtime does and never named, so their consequences must be derived; B2 eleven rules hold at
  once and each changes what a correct implementation of the others looks like; C1 both sides are
  graded, so an engine that never crosses the boundary and one that crosses too early both fail;
  C3 two wide families make the history-walking implementations infeasible while leaving them
  exactly correct; C4 every run file is compared line for line against a population generated
  after the agent is gone.
- Assistant's attack on the plan (its first plan, and where that plan is wrong): my first plan was
  to parse the history into a list, keep a cursor, check each command against the event under the
  cursor, read the answer that follows it, and go live when the cursor reached the end. It is
  wrong three times over: the command counter is per kind, so a timer between two calls does not
  move the second call's position; the answer counter is on kind and name together and answers
  are recorded out of issue order, so the answering event is not the next one; and the marker
  default depends on a boundary that the commands the marker's branch issues are what open, so
  nothing can be settled by reading the history first.
- Estimated solves out of 8 (design for 1, the hard edge; the realized rate drifts up): 2 of 8 (range 1-4)
- Difficulty record score (tools/difficultycheck.py on authoring/<slug>/difficulty.toml, before
  Stage 2; every attempt's score and what changed, until it reaches the band in
  docs/DIFFICULTY-SCORE.md): attempt 1 on 2026-09-22 scored 100/100, in band, no hard stop; there
  was only one attempt, so nothing was changed between attempts. The single warning was that the
  resource gate was declared and not yet measured, which Stage 4 settled before any prose
  depended on it.
- Difficulty score anchor (50 at first complete submission, approved by contributor): not yet submitted
- Score history (date, score, what moved, and any pipeline re-anchor): 2026-09-22 record scored 100
- Leak audit (docs/DIFFICULTY.md): for each mechanism, what in the bundle could let an agent
  discover, name or verify it without reasoning? Answer must be "nothing": the recorded events
  carry kind and name only, so the position a command matches on is implied by order within kind
  and has to be derived; nothing in a run file names the boundary, and it is recomputed every run;
  the generator interleaves kinds and completes commands out of issue order deliberately, so
  adjacency between a command and its answer is never a usable rule; the sample run files ship
  without their correct traces and the brief quotes one line of one of them, which is a value
  rather than a rule; the shipped engine keeps one position and counts nothing by kind, so the
  tables have to be built rather than found.
- Expert path, described step by step (the harder the aim, the more this guard must hold): run the
  shipped run files and read the one line the brief says is wrong, to find which module decides
  it; split the history into a table of recorded commands per kind and a table of answers per
  kind and name, since the brief counts the two on different axes; drive the pass from the body
  rather than from the history, so a command asks its kind's table for the slot its own counter
  names; hold the outstanding commands in issue order with the answer position bound at issue
  beside them, because taking the earliest issued and taking the earliest answered are different
  rules; settle the boundary as one global crossing that prints once, and make the marker read
  that state rather than the history's length; keep the matched positions as a set so the
  end-of-body check can name the earliest recorded command the body never issued, and skip that
  check when the body stopped short; deliver signals from a per-tag queue that survives the
  boundary and leave them out of that check; then time the wide run files and confirm the tables
  built once replace the per-command walks.
- Originality check: searched 2026-09-22 for the mechanism. What the literature and the vendor
  documentation carry is the general statement that replay must be deterministic, that a code
  change breaks it, and that a version marker returns the recorded branch. None of it says on
  what axis a command is counted, how an answer is paired with a command that completed out of
  order, when a marker with no record yields the legacy value rather than the asked one, or that
  a recorded command the body never issued is a failure while a recorded signal it never took is
  not. The best retrievable page gives a plan that is wrong at the first of those.

## Instruction contract (docs/INSTRUCTION-CONTRACT.md, read before anything else)

Every graded assertion traces to a sentence in the instruction. The walk is
`authoring/replay-match-drift/trace.md`.

- Instruction trace (authoring/<slug>/trace.md; rows walked, NOT STATED left, tracecheck result): 63 rows walked - 4 test functions, 38 enumerated run files, 6 artifacts, the 60 second clock and 14 rows over the sealed model split one per rule with its lines - plus 23 readings, 6 shortcuts and 2 limits; no NOT STATED row survived, and `python tools/tracecheck.py replay-match-drift` is clean. The trace is built by a script that refuses to write a quote which is not in `instruction.md` word for word, so a brief edit that stranded a citation could not ship.
- Identifiability (readings enumerated, which survived the published evidence, what separated them): 23 readings were written as whole engines by `authoring/replay-match-drift/emit.py` and measured by `python tools/readingcheck.py replay-match-drift`. All 23 are separated by the enumerated set; one, `name-answer`, came back `equivalent` on the first run and `pair-kind-name` was written for it, a program using one name under two kinds whose answers are recorded in the other order. `cheat_report.py` then asserts that each reading is caught by the run file named for it, which holds for all 23, and reports how much of the generated population each moves: from 2 per cent (`ver-key-blind`, which is three quarters of its own family) to 100 per cent (`const-zero`).
- Shortcut strategies scored (nop, constant, positional, replayed example; score and cases matched): the nop scores 0 with 17 of 41 graded assertions failing; `cheat-const-zero` scores 0 and moves 100 per cent of the generated set; `cheat-pos-first` scores 0 and moves 34 per cent; `cheat-forge-hand` carries the 38 enumerated histories by fingerprint and is the reference only for those, passes every enumerated run file and fails the generated population; `cheat-forge-truth` carries the frozen answers themselves, replaces the trace writer at import and hands them back, and does the same. `tools/forgecheck.py` names the second as a carrier of ground truth.
- Independent implementation behind every tolerance and limit (path, measured headroom): `authoring/replay-match-drift/variants/ok-deque` and `.../ok-flat`, both written apart from the reference, settle the six scale run files in 1.0 seconds each against the 60 second clock, a factor of sixty; the reference takes 0.9. The two readings that settle every rule the same way and walk the history instead of indexing it take 306.4 and 153.2 seconds, so the limit sits at a fifth of the first and two fifths of the second. The sealed model, also written apart, agrees with both and with the reference on every graded program. There is no numeric tolerance: traces are compared string for string.
- Undecided decisions from the cold-reader pass (author-run or fresh session; sentence or example added for each): author-run, mechanically, over every printed token. Ten gaps were found and closed in the brief: that every count and position starts at zero, that blank lines are skipped, that values are integers and names single words, that `lab` does nothing, that the count of one kind is not moved by another kind, that a live answer ranks after every recorded one, that an outstanding command with no answer never wins a race, that only recorded commands count toward the leftover, that a run which stopped short makes no leftover check, and that an empty history is still replaying until a command opens the boundary. One sentence survives without a reading that contests it - that a body which runs off its last op ends like one that reached `fin` - because no generated body omits `fin`; it is kept because the machine allows it and the agent is owed the fact.

## Verifier contract - FROZEN after Stage 2

Frozen 2026-09-22 and unchanged since. Eleven graded decisions, the trace format and the artifact
list are recorded in the section of the same name in the design record
`authoring/replay-match-drift/difficulty.toml` and restated in `tests/test_outputs.py`, which is
the file a reviewer reads.

- Artifacts the agent produces: `/app/dur/tab.py`, `/app/dur/edge.py`, `/app/dur/pair.py`,
  `/app/dur/pend.py`, `/app/dur/sigq.py`, `/app/dur/ver.py`. Nothing else is collected; the
  verifier lays those six over its own clean copy of the tree.
- What is checked: the stdout trace of every graded run file, line for line, exactly.
  Thirty-eight enumerated run files against `gt.json`, frozen before the grading file was
  written; 486 generated run files against the sealed model, which must itself still reproduce
  `gt.json`.
- Tolerances: none. The only limit is the 60 second wall clock on the stage that runs submitted
  code, validated against two independently written correct implementations.
- Ground truth, and where it lives: `tests/seal/model.py` and `tests/seal/gt.json`, in a directory
  `chmod 700` before the privilege drop.

### The eleven graded decisions

1. A command matches the recorded command at its own position among those of its kind.
2. A recorded command naming something else stops the run where it happens.
3. One boundary for the whole run, printed once, after which no command consults the history.
4. An answer is paired with its command on kind and name together.
5. Live answers come from the run file's list in issue order, ranked after every recorded answer.
6. `join` takes the outstanding command issued earliest, `race` the one answered earliest.
7. A result that has no answer stops the run and names the command, or `hold none`.
8. Signals are taken per tag, in recorded order, on either side of the boundary.
9. A marker with no recorded choice is zero while replaying and the body's own value once live.
10. A finished body owing the history a command it never issued fails, naming the earliest; only
    recorded commands count, and a run that stopped short makes no check.
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

| Check | Status | Notes |
|---|---|---|
| Agent image builds | not run | image pulls are refused by this session's egress policy (403 on the registry CDN); `tools/imagecheck.py` interprets the Dockerfile instead and is clean |
| No answer leaked into agent image | pass | `imagecheck`: 15 files, no `tests/` or `solution/` content |
| `harbor run -a oracle` = 1 | emulated | `authoring/replay-match-drift/host_trial.py oracle`: reward 1. Harbor is not installed and no container could be built here |
| `harbor run -a nop` = 0 | emulated | `host_trial.py nop`: reward 0, 16 of 39 assertions failing |
| Cheats all score 0 | pass | 38 cheats through `host_trial.py`, every one 0; the 11 probes re-run after a harness fix |
| `tracecheck.py` (every graded assertion traced) | pass | clean |
| `preflight.py` | pass | see the report below |
| `harbor check` rubric | not run | no API key in this session; the manual quality review in docs/QUALITY-REVIEW.md was walked instead |
| `simcheck` | in family | `tests/test.sh` 0.733 against `expert-defer-shed`, whose own report is 0.722 the other way; both Dockerfiles are near-identical to four retained bundles because their content is prescribed by the kit. The conceptual line reads "this task does not grade what any earlier one grades" |
| `textcheck` against `expert-defer-shed` | residual | 19 per cent short sentences against the reference's 31, and paragraph lengths more even. Every short sentence that carries a contract fact has been added; going further would mean restating rules, which the rubric rejects. Two retained bundles trip the same findings against the same reference |
| `onelinecheck` | pass | none of the five graded quantities has an exact rule at depth two over what the tree exposes |
| `forgecheck` | pass | `cheat-forge-truth.sh` carries the frozen answers and scores 0 |

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
