# Task state

Working memory for this task. The assistant updates it after every stage. Assume the next
session starts with no memory of this one - anything not written here is lost.

## Current stage

`Stage 7 - Pre-flight and packaging`

## Assistant's assigned role

You are a platform engineer on the settings service that the rest of the estate reads its
configuration out of: an append-only journal of operator changes, resolved into an effective
board of settings that callers read by section and name. You have built the resolver, you have
carried the pager when a withdrawn change put a setting back to a value nobody had asked for,
and you know that a section that inherits from another is not the same thing as a section that
holds the same value, and that withdrawing a change is not undoing it.

## Source repository (repo-based tasks only)

- Repo URL: none - idea-based task, no third-party code vendored
- Task shape chosen (authored-on-top / ablation per docs/ABLATION.md): not applicable, no repository
- Contributor's relationship to it (maintainer / contributor / production user, how long): not applicable
- License, and why vendoring it is permitted: not applicable, nothing vendored
- Pinned commit vendored into environment/app_src/ (.git stripped): not applicable
- Load-bearing couplings found during research (file paths): not applicable
- Identifier degradation done? Conversion table lives at solution/ (never in environment/): the tree is
  written here rather than degraded from a source; identifiers are chosen directly in the legacy
  register (`cf/`, `book`, `sect`, `step`, `gate`, `wake`, `walk`, `tell`, `cur`, `ent`, `chg`) and
  no name misdescribes what it holds
- Proper-noun sweep done? No product, project, company or framework name appears anywhere in the
  agent-facing tree; the words that remain (section, slot, link, journal, change) are the ordinary
  vocabulary of configuration work and carry no provenance
- Upstream-diff check: there is no upstream to diff against

## Task summary

`/app` is the resolver of a settings service. A program file is a journal: operator changes that
write a name in the section the journal is currently working in, empty a name, mask a name, step
a held number, move the journal to another section, or link a section to the one above it. Some
changes carry a condition. `/app/run_conf.py` reads a program and prints what the resolver
answered. The settled board is whatever a walk of the surviving changes over a clean board
produces, so withdrawing a change in the middle of the journal is not the same as undoing it,
and a read climbs the link chain rather than looking in one place. The shipped resolver keeps an
undo record and restores it, which is right until a later change wrote the same name. The agent
fixes the seven files under `/app/cf/` so every program's trace matches, inside a stated limit
that a walk-everything-for-every-question resolver does not fit.

## Why it is hard

The first plan is the undo stack, and it is wrong the first time two changes touch one name.
The rule that replaces it makes every answer a walk of what survives; the rule after that makes
a change rest on the names its climb looked at and did not find, which no record of what it read
contains.

- Expert time estimate: 9 hours
- Why a frontier agent cannot one-shot the plan (the strategic answer - required): because withdrawing a change has one memorised meaning - undo it - and it is carried by every version-control, override-stack and edit-history idiom the model holds, while here the result is defined as a re-walk of the survivors over a clean board, so an undo restores a value no walk would ever produce. Past that, the resolver must answer thousands of questions over a journal of tens of thousands of changes inside a stated limit, which rules out the walk that made it correct; and the structure that replaces it has to key a change's lookups on the slots the climb passed over and the links it followed, not on the value it ended up with, because a change that found nothing starts finding something when a mask far away is withdrawn.
- Tactics making that true (prong A poison, prong B withholding, prong C late failure): A1, A2, B2, C1, C3 and C4. A1 the shipped resolver is the model's prior implemented faithfully and it is the wrong answer; A2 the climb, the two removals, the carried section and the one wake per pass are stated as what the resolver does and never named, so their consequences must be derived; B2 twelve rules hold at once and each changes what a correct implementation of the others is; C1 both sides are graded, so the from-clean walk that is exactly right is too slow and the index built from values read is fast and wrong; C3 two large families make the from-clean walk infeasible while leaving it exactly correct; C4 every program is compared line for line against a population generated after the agent's container is gone.
- Assistant's attack on the plan (its first plan, and where that plan is wrong): my first plan was to hold the settled slots in a dictionary, apply each change as it arrived with the old value recorded beside it, undo those writes when the change was lifted, evaluate each condition once at the moment the change was applied, and answer a read by looking the slot up and following the link if it was not there. It is wrong three times over. The settled board is a walk of the survivors, so a lifted change whose write a later change overwrote must leave nothing behind, and a lifted change carrying a section or link change moves the target of everything after it rather than only its own. Every settle begins again with every conditional change asleep, so the awake set cannot be carried forward and adjusted. And once the limit forces the walk to be replaced, a record of what each change read is not the dependency set: a change rests on every slot its climb passed over and every link it followed, so an implementation that reopens changes when a value they read moves leaves asleep exactly the ones that found nothing.
- Estimated solves out of 8 (design for 1, the hard edge; the realized rate drifts up): 3 of 8 (range 1-5), revised up from 2 at the Stage 7 cold re-attack because every rule is stated and a careful implementer who reads the settle rule before touching the shipped code forms the correct semantics at once; what is left is the structure, the conjunction of twelve rules and the two scale families
- Difficulty record score (tools/difficultycheck.py on authoring/<slug>/difficulty.toml, before
  Stage 2; every attempt's score and what changed, until it reaches the band in
  docs/DIFFICULTY-SCORE.md): attempt 1 on 2026-09-22 scored 100/100, in band, no hard stop. There
  was one attempt; nothing was changed between attempts. Its one warning was that the resource
  gate was declared and not measured; Stage 4 measured it and the record now says so. Re-run at
  Stage 7 against the built tree it scores 100/100 again, measuring 332 environment Python lines,
  7 editable files, 299 reference lines, 45 cheats and 2 variants, with no drift reported on any
  declared size.
- Difficulty score anchor (50 at first complete submission, approved by contributor): not yet submitted
- Score history (date, score, what moved, and any pipeline re-anchor): 2026-09-22 record scored 100 on paper and 100 again with the tree measured
- Leak audit (docs/DIFFICULTY.md): for each mechanism, what in the bundle could let an agent
  discover, name or verify it without reasoning? Answer must be "nothing": no slot records which
  change last wrote it, so the change behind a value is recoverable only by walking the journal;
  the shipped resolver carries no index from a name to the changes that touch it, so the structure
  the limit demands has to be built rather than adapted; a section holds at most the one section it
  links to and every read walks the hops itself, with no memo anywhere in the tree; sleeping is a
  fact about one settle and lives in the run, never as a field on a change, so nothing says which
  changes a previous settle woke; and the sample programs ship without their answers, with one line
  of one of them quoted in the brief. The procedural half of the audit is
  `tools/onelinecheck.py`, which searched for an exact rule of two terms or fewer over the fields
  the tree exposes at each graded decision and found none for any of the five, over 820 to 3513
  samples each.
- Expert path, described step by step (the harder the aim, the more this guard must hold): run the
  shipped resolver on the small sample and find which module prints the line the brief says is
  wrong; read the settle rule and replace the undo log with a walk of the live changes over a clean
  board; separate the two removals, one emptying a slot so the climb goes on and one masking it so
  the climb stops; make the section a value the walk carries, so a refused condition leaves it where
  it was; settle the sleeping changes one per pass, lowest number first, reading each condition in
  the section that pass gave it and over the board that pass left; time the two large families and
  find the walk does not fit; record for each change the slots its climb consulted, the links it
  followed and the section it started in; index those by slot and by link so a withdrawal reopens
  only the changes whose lookup can have moved, in journal order; and check the fences, because a
  change that found nothing where a mask stood has to be reconsidered once the mask goes.
- Originality check: searched 2026-09-22 for the mechanism. What the public material carries is
  layered configuration and overlay resolution, where the layers present are merged and nothing
  defines what withdrawing a layer in the middle does to the layers after it; and the incremental
  and self-adjusting computation literature, which memoises a step against the values it read and
  invalidates when one of them changes - the dependency set that is precisely wrong here. No public
  source defines a settle as a re-walk from a clean board with conditional changes woken one per
  pass in number order, a condition read in one pass's section over that pass's board, a masked
  slot that stops an inheritance climb where an emptied one does not, or a withdrawal that moves
  the target of every change after it. The best retrievable page gives a plan that is wrong at the
  first decision and hands over a dependency set that fails late. `tools/simcheck.py` reports that
  this task does not grade what any earlier one in this repository grades.

## Instruction contract (docs/INSTRUCTION-CONTRACT.md, read before anything else)

Every graded assertion traces to a sentence in the instruction. The walk is
`authoring/entry-lift-restate/trace.md`.

- Instruction trace (authoring/<slug>/trace.md; rows walked, NOT STATED left, tracecheck result): 114 rows walked - 75 graded assertions (4 test functions, 38 enumerated programs, the 7 collected files, the two rows for the pristine overlay and for a file put beside them, the 60 second clock and 21 rows splitting the sealed model one rule at a time with its lines), 33 readings, 4 shortcuts and 2 tolerances. No NOT STATED row survived: three findings on the first run were all short quotations rather than missing sentences, and `python tools/tracecheck.py entry-lift-restate` is clean.
- Identifiability (readings enumerated, which survived the published evidence, what separated them): 30 wrong readings were written as changes to the reference in `authoring/entry-lift-restate/readings.py`. `python tools/readingcheck.py entry-lift-restate 400` scores 28 of them - the two that do not terminate are left to the worker's clock - and every one is separated by an enumerated program, none BLIND and none equivalent. Three of the enumerated programs did not in fact separate the reading they were written for when this was first measured: `all-shape` had no pair of slots whose order differs between section-then-name and name-then-section, `gate-reads-here` put the same number in both sections, and `off-unlinks` had its section entry and its link entry in one change so lifting it hid the link. All three were rewritten and `gate-reads-sec` added.
- Shortcut strategies scored (nop, constant, positional, replayed example; score and cases matched): the nop scores 0 in the container with 19 of 41 graded assertions failing; `cheat-const-common` scores 0, settling 4 of 38 enumerated programs and 2 per cent of a sampled generated population; `cheat-pos-last-write` scores 0, settling 7 of 38 and none of the sample; `cheat-forge-hand` carries the frozen answers for all 38 enumerated programs, passes every one of them and fails 98 per cent of the sample, which is what the nonce seed is for.
- Independent implementation behind every tolerance and limit (path, measured headroom): `authoring/entry-lift-restate/variants/ok-flat` and `.../ok-coarse`, both written apart from the reference, settle the six scale programs in 1.93 and 2.33 seconds; the reference settles the whole graded set in 3.11 seconds inside the verifier container under one CPU and 2048 MB, against the 60 second clock, a factor of nineteen. The sealed model, written apart from all three, agrees with the reference on all 404 graded programs. There is no numeric tolerance: the trace is compared string for string.
- Undecided decisions from the cold-reader pass (author-run or fresh session; sentence or example added for each): run as the author-run form of the pass, decision by decision over the printed tokens. Five things the text left open were closed by writing the sentence. Whether a value or a step may be negative while a section or a name may not, which is now the last sentence of the second paragraph. Whether `open`, `shut`, `off`, `back`, `get` and `all` take entry numbers, which is now said outright. That a change is numbered when its bracket opens, counting a bracket and a bare entry alike. That a question is answered over the entries above it in the file rather than over the whole file, which `later-entries-ignored` grades. And that every pass, not only the first of a settle, starts in section 0, which `sec-resets-each-pass` grades. The stronger form - a fresh session shown only the brief and the tree - was not run.

## Verifier contract - FROZEN after Stage 2

Once agreed, this does not change without the contributor's explicit approval.

- Artifacts the agent produces: the seven files `/app/cf/book.py`, `/app/cf/sect.py`,
  `/app/cf/step.py`, `/app/cf/gate.py`, `/app/cf/wake.py`, `/app/cf/walk.py` and
  `/app/cf/tell.py`. Nothing else is collected; a new file placed beside them is never read.
- What is checked: the verifier lays the seven collected files over its own pristine copy of the
  tree and runs `/app/run_conf.py` on every graded program under an unprivileged uid. The printed
  trace is compared line for line, exactly, against the sealed model. Every program must match;
  the whole graded set must finish inside the stated wall clock.
- Tolerances: none. The trace is compared string for string. The only limit is the wall clock
  over the whole graded set, validated against two independently written correct resolvers.
- Ground truth, and where it lives: `tests/seal/model.py` is a resolver written apart from the
  reference; `tests/seal/gt.json` holds the frozen answers for the 38 enumerated hand programs
  and the grader asserts the model still reproduces it byte for byte before grading anything. The
  seal directory is root-owned and `chmod 700` before the privilege drop, so code running inside
  the verifier cannot read either. Generated programs are produced inside the verifier from a
  seed drawn after the agent's container is gone: 36 from each of ten small families and three
  from each of the two scale families, 366 in all.

### The twelve graded decisions

1. A read of a name in a section takes the slot's value if it holds one, finds nothing if the
   slot is masked, and otherwise moves to the section that section links to and looks again;
   returning to a section already visited on the climb ends it with nothing found.
2. A step change reads its name through the climb and writes the result into the section the
   journal is working in, not into the section the value came from.
3. A step change does nothing at all when its read finds nothing.
4. Emptying a slot leaves the climb free to go on; masking it stops the climb there.
5. Every change acts in the section the walk is carrying when it is reached, and that section
   starts at 0 at the beginning of every pass.
6. A change whose condition is not met does nothing at all, including not moving the section and
   not linking anything.
7. Every settle starts from a clean board with every conditional change of the second kind asleep.
8. Between passes the lowest-numbered sleeping change whose condition is met wakes, one per pass.
9. A sleeping change's condition is read in the section the finished pass gave its position, over
   the board that pass left.
10. A woken change is applied on later passes without its condition being tested again.
11. A lifted change's entries are skipped in every pass, take no part in the section the walk
    carries, and can never wake.
12. The printed format: what a read prints, what the board summary prints, the order of the
    detail lines, and the pass count.

## Decisions and their reasons

- Withdrawal is per change rather than per entry. A change is the unit an operator makes, and
  keeping withdrawal at that grain removes a whole axis of grammar without removing any
  interaction: the cascade comes from the conditions and the carried section, never from partial
  withdrawal.
- Sections and names are integers rather than strings. Nothing in the task turns on text, and
  integers keep the program grammar small enough that the parser can be frozen.
- The settle is defined as a re-walk from a clean board rather than as an incremental update.
  That is what makes the from-clean resolver exactly correct, which is the requirement a resource
  gate has: the limit removes a correct implementation rather than a wrong one.
- The pass count is printed. It is the only observable that separates waking one change per pass
  from waking every eligible change at once in the programs where the two settle on the same
  board, and the brief states it.
- Two kinds of removal rather than one. An emptied slot and a masked slot are indistinguishable
  in a board that only records values, which is exactly the distinction a resolver built on an
  undo log cannot carry.
- An isolation probe must not be able to score 1 for its own reasons. The first ten probes were
  the reference plus an attempt at the attack, and seven of them scored 1 in the container
  because the attempt failed and the resolver was still correct. Each is now the attack laid
  over a base that is certainly wrong - the frozen answers for the enumerated programs and
  nothing for the rest - so a probe can only reach 1 when its layer actually broke. The answer
  key probe resolves from `/tests/seal/gt.json` and the sealed model, and its own reconstruction
  of a program from a parsed one was checked to reproduce all 38 enumerated programs, so a
  readable seal really would win.
- `preflight.py` reports eleven unused public functions in the agent tree. Every one is called
  through its module (`walk.play`, `sect.read`, `step.act`), which the check's pattern
  deliberately excludes; the same class of warning is on every retained bundle, sixteen of them
  on `expert-defer-shed`.

## Stage 7 re-attack, run cold on the finished bundle

Read the final brief as the probe agent will, with the tree in front of me.

The first plan is still wrong, but it is worth being exact about which first plan. An agent that
starts from the shipped code keeps the undo log, and the brief's own example shows that failing
on the second line of the smallest sample. An agent that reads the settle rule before touching
anything writes a from-clean walk instead, and that plan is semantically right: every rule is
stated, so the semantics can be formed in one shot by a careful reader. What cannot be formed in
one shot is a structure that satisfies all twelve rules and fits the limit, and that is where the
task lives. The from-clean walk takes 70 and 76 seconds on the two scale sizes against a 60
second clock for the whole set; the structure that replaces it has to answer "what has this
change's lookup rested on" with the slots the climb passed over and the links it followed, and
an index built from values read is fast, plausible and wrong on exactly one family.

Are the load-bearing facts still distributed? Partly, and honestly: this is a compact tree, 332
lines across eleven files, so B1 is not claimed. What is distributed is the consequence rather
than the fact - which structure survives the climb, the carried section, the two removals, the
sleeping rules and the clock together - and that is B2 with a measured C3, the shape
`focus-return-point` passed on.

Did the brief come to telegraph the method? It states the settle as a re-walk, which it must,
and says nothing about how to avoid re-walking. It names no index, no memo, no dependency and no
trail. The words "incremental" and "cache" do not appear.

Estimated solves, revised: 3 of 8, range 1 to 5. Up from the design target of 2, because the
semantics is reachable by a careful reader and the expert path is short enough to describe in
nine steps. The two things most likely to sink an otherwise correct submission are the mask that
a lookup stopped at, which only the `mask` family and `mask-lifted` reach, and the clock.

## Validation status

| Check | Status | Notes |
|---|---|---|
| Agent image builds | pass | `tools/docker_trial.py entry-lift-restate --build`; harbor is not installed here, the two-image runner stands in for it |
| No answer leaked into agent image | pass | `tools/imagecheck.py` assembles what the image would hold, 25 files, and runs all four shipped programs; nothing under `tests/` or `solution/` is copied; the tree names no answer file |
| `harbor run -a oracle` = 1 | pass | `tools/docker_trial.py entry-lift-restate oracle`: 41 tests passed, reward 1 |
| `harbor run -a nop` = 0 | pass | `tools/docker_trial.py entry-lift-restate nop`: 20 failed, 21 passed, reward 0 |
| Cheats all score 0 | pass | 45 of 45 in the container: 30 wrong readings, 2 correct and too slow, 2 shortcut strategies, 1 forgery, 10 isolation probes |
| Correct variants score 1 | pass | `--dir authoring/entry-lift-restate/variants/ok-flat` and `.../ok-coarse`, both reward 1 |
| Isolation probes score 0 | pass | all ten, after the rebuild that made each one depend on its own attack |
| `forgecheck.py` | pass | reports ten carriers of the frozen answers - the forgery and the nine probes built on it - and every one scores 0. Its slice picker had to be taught to draw its marks from the answers rather than from the case names beside them; checked to keep reporting the carriers of all eight other bundles |
| `tracecheck.py` (every graded assertion traced) | pass | clean |
| `preflight.py` | pass | no errors; eleven warnings, all module-qualified calls |
| `harbor check` rubric | not run | no API key in this environment; the manual walk of docs/QUALITY-REVIEW.md is below |

Other local checks: `solvecheck`, `deadfieldcheck`, `extraneouscheck`, `hintcheck`, `structcheck`
and `catcheck` are clean; `catcheck` measures 81 hits of the Software vocabulary in the
environment against 43 in the prose. `onelinecheck` finds no exact rule at depth two or less for
any of the five graded decisions. `simcheck` reports that the task grades nothing an earlier one
grades; its remaining near-duplicate hits are the two Dockerfiles, whose shape the kit's own
rules fix (`FROM python:3.12-slim`, a `RUN mkdir -p` per declared artifact parent, the canonical
pytest pins), and `test_outputs.py` at 0.64, which is the shared pytest scaffolding around a
different contract and different case names.

## Open questions and next steps

- The easiness probe has not been run. Nothing here is evidence about it.
- `textcheck` still reports two soft findings against `expert-defer-shed` as the reference:
  paragraph lengths more uniform (standard deviation 40 against 69) and one dash aside, which is
  the literal `-` inside the worked example's output line. Contractions, stock phrases, hedges
  and oxford triads are all at zero.
- The cold self-probe was not run as a cold solve and is recorded as not run, below.

## The self-probe, and why it is recorded as not run

The order of work here was brief, then specification, then sealed model, then reference, so by
the time an environment existed both discoveries were already in hand. A cold solve by this
session would have measured memory. `CLAUDE.md` records that a self-probe reported as passed by
a contaminated author is worse than none, so it is recorded as not run. What stands in its place
is measurable: every one of the 28 terminating wrong readings is separated by an enumerated
program named for it, no graded decision has a rule of two terms or fewer over the fields the
tree exposes, and nothing in the agent's tree answers a question without the work.

## Quality self-review (docs/QUALITY-REVIEW.md, walked criterion by criterion)

**Instruction and verifier agree, both ways.** Every behaviour the tests check has a sentence:
the walk is `authoring/entry-lift-restate/trace.md`, 114 rows, and `tracecheck` is clean. Every
sentence has a test: the twelve graded decisions each have at least one enumerated program, and
the fences have both sides (`gate-passes` against `gate-blocks-sec`, `clr-goes-on` against
`cut-stops`, `off-uncovers` against `off-overwritten`, `plain-run` as the everyday case). The
seven collected files are named with absolute paths in the fourth paragraph. The printed format
is given down to the three counts and the order of the three runs of detail lines. Boundaries
are settled: sections and names from 0, passes from one, values and steps may be negative while
sections and names may not, `-` for a reading that finds nothing, the order of the detail lines,
what a doubled `off` does. Every graded quantity is defined, held and masked and linked by name.
No count in the brief or the metadata contradicts what ships: the two sample figures were
re-derived from the files after the last generator change (15437 entries and 11565 questions in
`wide.txt`, 22719 and 15656 in `deep.txt`), and so were the 38 hand programs and the 360 smaller
ones. The clock is in the text.

**Instruction prose.** Read aloud, twice. No run of same-structured sentences survives: the
grammar paragraph is a list because it is a list, and the rule paragraphs alternate long and
short. Each requirement is stated once - the climb once, the two removals once, the wake rule
once. `textcheck` against `expert-defer-shed` reports no stock vocabulary, no hedges, no
antithesis, no triads and no contractions.

**Verifier rigour.** The tests demand the trace of a run that happened: the worker stages a
pristine tree, runs the driver, and the grader compares line for line against a model it first
checks against the frozen answers. Nothing is taken from an exit code. `tests/test_outputs.py`
opens with the frozen contract, twelve numbered decisions, and says which section checks what.
Determinism: the generated population comes from a seed written into a file, the enumerated
answers are frozen on disk, and nothing reads the clock except the wall limit that is stated in
the brief.

**Environment hygiene.** Neither `tests/` nor `solution/` is copied into the agent image;
`environment/Dockerfile` copies `app_src/` and nothing else. Pytest and the CTRF plugin are
installed in `tests/Dockerfile` at the canonical pins and `tests/test.sh` touches no network.
Every Python package is pinned with `==`; no apt package is pinned because none is installed.
Every path and name in the brief exists in the tree and is spelled the same: checked by reading
the brief against `find environment -type f`.

**Solution quality.** `solution/solve.sh` installs seven source files and then runs the driver on
a shipped program; it computes nothing by hand and writes no answer. The reference uses only what
the agent has.

**Anti-cheating.** The answer is not in the environment: no slot records its writer, no index
from a name to the changes that touch it exists, the sample programs ship without their answers,
and `deadfieldcheck` and `extraneouscheck` are clean. The comparison is exact, so a degenerate
output fails: `cheat-const-common` and `cheat-pos-last-write` both score 0. No repository is
cloned.

**Metadata.** `category = "Software"` with `subcategory = "Algorithms"`, which is a label from
that row; the graded work is an incremental derivation over an ordered journal, and `catcheck`
confirms the vocabulary is in the environment rather than only in the story. The six tags name
techniques rather than the taxonomy. `difficulty_explanation` names the concrete steps - the undo
log, the re-walk, the dependency set that has to include the misses - and says outright that the
identifiers are in a legacy register by choice. `solution_explanation` describes the actual
method file by file. `verification_explanation` says what each fence catches by the name of the
program that catches it. `relevant_experience` is the settings-resolver work this task is drawn
from and claims no employer, credential or duration. Nine hours is consistent with the nine-step
expert path and the two structures it has to build.
