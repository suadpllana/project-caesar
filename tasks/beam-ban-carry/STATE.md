# Task state

Working memory for this task. The assistant updates it after every stage. Assume the next
session starts with no memory of this one - anything not written here is lost.

## Current stage

`Stage 7 - packaging` (all local gates run; see the validation table)

## Assistant's assigned role

You are a decoding-path engineer on an inference serving team: the person who owns the search
stage that turns a scorer into the handful of sequences the server actually returns, and who
has spent time on beam bookkeeping, repeat suppression, length normalisation and the pruning
bounds that decide how long a request runs.

## Source repository (repo-based tasks only)

- Repo URL: none - idea-based task
- Task shape chosen (authored-on-top / ablation per docs/ABLATION.md): not applicable, no repository
- Contributor's relationship to it: not applicable
- License, and why vendoring it is permitted: not applicable, nothing is vendored
- Pinned commit vendored into environment/app_src/ (.git stripped): not applicable
- Load-bearing couplings found during research (file paths): not applicable
- Identifier degradation done? Not applicable - the tree is written here, in a legacy register
  from the start (`bm/`, `sc`, `rep`, `keep`, `pick`, `walk`, `halt`), with no upstream to degrade
- Proper-noun sweep done? Nothing carries provenance: no library, product or project name appears
  in the agent-facing tree
- Upstream-diff check: not applicable, there is no upstream to diff against

## Task summary

`/app` is the search stage of a decoding server, cut down to the part that decides which
sequences a request returns. A program file gives a scoring table over token pairs, the search
settings, and one or more requests with their prompts. `/app/run_beam.py` runs each request and
prints what the search did: each hypothesis that closed, each one the kept set dropped, the step
and reason the search halted, and the kept set at the end with its tokens. The shipped stage is
wrong, and the six files under `/app/bm` that decide closing, repeat refusal, the kept set,
ranking, the step loop and the halt bound are the files the agent may change.

The rule the whole task turns on: a hypothesis in the kept set lends its spans to the search.
While it is a member, no live beam may take a continuation whose span it holds; when the set
drops it, those bans come back. Refusal is therefore a property of the kept set's current
membership rather than of the beam's own tokens, and the membership is decided by a penalised
score that is not the order the beams were pruned by.

## Why it is hard

- Expert time estimate: 9 hours
- Why a frontier agent cannot one-shot the plan (the strategic answer - required): the memorised decoding structure keeps repeat suppression inside one hypothesis and treats the finished list as an inert sink, so the first plan puts the refusal state in the wrong place; getting it right
  means the refusal state is shared, revocable and ordered by a score the search does not prune
  by, and none of that can be confirmed one rule at a time because the stage prints closures, drops
  and the kept set and nothing about a refusal.
- Tactics making that true (docs/DIFFICULTY.md - prong A poison / prong B withholding / prong C late failure): A1, A2, B2, C1, C2, C3 and C4. A1 the recalled beam-search idiom is wrong at its first decision point; A2 the brief says what
  happens to spans on entry and exit and never says the state is shared or carried; B2 ten rules
  hold at once and each changes what a correct implementation of the next looks like; C1 both
  sides of the lending rule are graded; C2 a library beam search computes a different quantity so
  it confirms nothing; C3 a long search and a churning kept set put the history-walking
  implementation outside the stated limit while leaving it exactly correct; C4 exact line-for-line
  grading over a population generated after the agent's container is gone.
- Assistant's attack on the plan (its first plan, and where that plan is wrong): my first plan is
  W hypothesis objects each carrying its own token list and repeat set, expansion over the table,
  a finished pool ranked by the penalised score, top-W selection, and a stop test at the end. It
  is wrong in four places that do not announce themselves. The pool lends its spans, so the
  refusal test cannot be answered from the beam. An eviction takes those bans back, so folding the
  pool's spans into the beams - the obvious repair - is wrong, and two members can hold the same
  span, so a single shared set is wrong too. Closures are settled before the step's candidates are
  ranked, so a closure binds the same step. And selection keeps one beam per final token, so
  `sorted(...)[:W]` is not selection. My first plan also rebuilds each beam's span record from its
  tokens every step, which is exactly correct and does not fit the stated limit.
- Estimated solves out of 8 (design for 1, the hard edge; the realized rate drifts up): 2 of 8, with a plausible range of 1 to 3
- Difficulty record score (tools/difficultycheck.py on authoring/<slug>/difficulty.toml, before
  Stage 2; every attempt's score and what changed, until it reaches the band in
  docs/DIFFICULTY-SCORE.md): attempt 1 on 2026-09-22 scored 100 of 100, in band, with one warning
  that the gate timings were still a promise. No earlier attempt: the lending-and-revoking rule
  was in the design from the first draft, because a design whose repeat state is per-hypothesis
  scores `patch` on the second discovery and lands in the controls' range.
- Difficulty score anchor (50 at first complete submission, approved by contributor): not yet submitted
- Score history (date, score, what moved, and any pipeline re-anchor): 2026-09-22, 100, first record
- Leak audit (docs/DIFFICULTY.md): for each mechanism, what in the bundle could let an agent
  discover, name or verify it without reasoning? Answer must be "nothing":
  - the lending rule: the trace prints closures, drops, the halt and the kept set; a refusal is
    visible only as a path the search never took, and no line names a span
  - the revoking rule: nothing in the tree stores a span, a refusal or a count; the shipped stage
    builds the refusal state where it uses it
  - the carried span record: the shipped buffer has no record to find - it walks the token list -
    so the structure has to be built rather than switched on
  - the reach bound: the halt line carries the step it fired on and nothing before it, so the
    number of steps is a result and not an input
  - the graded answers: one line of one shipped program is quoted in the brief, and it is a kept-set
    line rather than a decision the task turns on
- Expert path, described step by step (the harder the aim, the more this guard must hold):
  1. run the shipped programs and read the quoted line against what the brief says it should be;
  2. split the refusal state into the part a beam owns and the part the kept set lends it;
  3. move closing ahead of ranking so a closure binds the same step's candidates;
  4. give each kept hypothesis its own span record so an eviction takes exactly its bans back;
  5. rewrite selection as a walk down the ranking keeping one candidate per final token;
  6. derive the reach bound from the penalty and the largest table score;
  7. carry each span record on the beam instead of rebuilding it from the token list;
  8. rebuild the lent set by combining member records instead of counting spans one at a time;
  9. time the long search and the churning set against the stated limit.
- Originality check: searched for public write-ups of a beam search whose finished set constrains
  the live beams and gives the constraint back on eviction. Public material covers n-gram blocking
  inside one hypothesis, diverse beam search across groups at one step, and n-best list
  diversification after the fact. Nothing found where the kept set lends a revocable repeat ban to
  the running search, which is the rule this task turns on. No retained task in `README.md` grades
  a decode search: `token-seam-emit` grades detokenisation and stop matching on the byte side of
  the same server, and shares no decision with this one.

## Instruction contract (docs/INSTRUCTION-CONTRACT.md, read before anything else)

- Instruction trace (authoring/<slug>/trace.md; rows walked, NOT STATED left, tracecheck result): 70 graded rows walked - 4 test functions, 42 enumerated programs, 6 collected artifacts, the 60 second clock and 17 rules of the sealed model with their line ranges - plus 32 readings, 5 shortcuts and 1 tolerance. Every row carries a quote; none was left unstated or unfilled. `python tools/tracecheck.py beam-ban-carry` is clean. The trace is regenerated by `authoring/beam-ban-carry/make_trace.py`, which asserts every quote is still in `instruction.md` before it writes, so a reworded sentence fails at the point of writing rather than at the check.
- Identifiability (readings enumerated, which survived the published evidence, what separated them): 32 readings enumerated from the four clusters applied to every rule, from the decoding prior, from the shipped stage's own behaviour, and from the other parse of each sentence. Every one is separated by an enumerated program, and each program was searched for rather than chosen: `authoring/beam-ban-carry/hunt.py` scans the shaped families for a program the reading gets wrong and shrinks it while it still does. `python tools/readingcheck.py beam-ban-carry` reports 32 of 32 separated by the enumerated set. One reading came out equivalent on first writing - the kept set lending only the spans that lie inside the prompt - because every beam of a request already holds those in its own sequence; it was rewritten as lending only the spans inside the emitted tokens, which straddling spans do separate. No two readings that reproduce the published evidence disagree on the graded set.
- Shortcut strategies scored (nop, constant, positional, replayed example; score and cases matched): all score 0. The shipped tree reproduces 8 of 42 enumerated and 2 of 108 generated programs; one fixed trace for every request, 2 and 0; one beam always taking the lowest-numbered continuation, 24 and 14, the high enumerated figure being an artefact of programs shrunk to one beam; the worked example replayed, 0 and 0; an answer key for all 42 enumerated programs laid over a stage that did no work, 42 and 21.
- Independent implementation behind every tolerance and limit (path, measured headroom): the only limit is the 60 second wall clock on the graded run. Validated against four implementations written apart from the reference: `authoring/beam-ban-carry/variants/var-a` at 26.3 s and `variants/var-b` at 10.6 s, both correct and both passing, against the reference's 4.2 s; and the three naive-but-correct stages under `authoring/beam-ban-carry/slow` at 97.3 s, 111.6 s and 356.5 s, all three producing the reference's traces on everything they finish. Headroom is 14x for the reference and 2.3x for the slowest correct variant; the naive family misses by 1.6x to 5.9x.
- Undecided decisions from the cold-reader pass (author-run or fresh session; sentence or example added for each): author-run, mechanically, over every printed token and every model branch that can change one. It found one decision the text did not settle - whether a beam keeps its own score when it closes or absorbs the score on the stop row - and the sentence "Closing leaves it standing, and the score of that beam does not change" was added, with `close-absorbs` as a reading and an enumerated program behind it. Five further readings surfaced in the same pass and each already had its sentence: the prompt printed in front of a hypothesis's tokens, the token tie broken the other way, the kept set giving one up as soon as it holds H, the ceiling read a step early, and the lending restricted to what a member emitted. Each of those now has a case as well. The stronger form - a fresh session reading only the brief and the tree - was not run, and is not claimed: this session designed the contract and cannot un-know it.

## Verifier contract - FROZEN after Stage 2

Once agreed, this does not change without the contributor's explicit approval.

- Artifacts the agent produces: the six files `/app/bm/sc.py`, `/app/bm/rep.py`, `/app/bm/keep.py`,
  `/app/bm/pick.py`, `/app/bm/walk.py` and `/app/bm/halt.py`. Nothing else is collected. The
  verifier lays them over its own pristine copy of the tree, so `/app/run_beam.py`, `/app/bm/spec.py`,
  `/app/bm/say.py` and the shipped programs cannot change what a program prints, and a new file put
  beside the six is never collected.
- What is checked: the exact list of lines `run_beam.run(text)` returns for a program, compared
  line for line. Graded decisions, each owed a sentence in the instruction:
  1. a continuation exists only where the table has a row for the beam's last token and that token;
  2. a beam closes when it has emitted at least S tokens and a row for the stop token exists; the
     stop row's score counts toward the hypothesis and its length does not;
  3. closing does not remove the beam, and closing is settled for every beam, in slot order,
     before any candidate of that step is refused or ranked;
  4. a hypothesis is ordered by `raw - P * len`, ties to the smaller length, then to the earlier
     entry; the kept set holds at most H, and the worst goes when it overflows;
  5. a member of the kept set lends its spans: a candidate whose span is held by a member is
     refused;
  6. a member that leaves takes its bans with it, and a span held by another member stays banned;
  7. a candidate is also refused when its span occurs earlier in its own sequence, where the
     sequence is the prompt followed by the emitted tokens;
  8. candidates rank by score descending, ties to the smaller parent slot then the smaller token,
     and are taken down that order keeping one per final token, at most W;
  9. the search halts `dry` when nothing was taken, `cap` at the step ceiling, and `bound` when the
     kept set is full and `best - P*t + max(0, G - P) * (T - t) <= worst`;
  10. the printed form: `ask`, then `shut` and `gone` in the order they happened, then `halt`, then
      the kept set as `hyp` lines best first, and nothing else.
- Tolerances: none. Exact string equality on every line of every graded program. The only limit is
  the wall clock on the stage that runs the submission, stated in the instruction as 60 seconds for
  the whole graded set.
- Ground truth, and where it lives: `tests/seal/gt.json` holds the frozen answers to the enumerated
  programs; `tests/seal/model.py` is an independently written implementation of the same contract.
  Both live in a root-owned `chmod 700` directory the sandbox uid cannot read. The grader asserts
  the model still reproduces `gt.json` before it grades anything, and checks the generated
  population against the model.

Prong C in this contract: C1 fences the lending rule from both sides (a closure that must refuse a
live candidate, and an eviction that must let the same candidate through); C2 denies the oracle
because no public beam search computes this quantity and the shipped stage prints a well formed
trace whatever it decided; C3 gates the history-walking implementation with a long search and a
churning kept set; C4 grades every line of every program over a population generated from a seed
drawn after the agent's container is gone. The route-around is blocked by collecting six files and
laying them over a pristine tree, so the grammar, the driver and the printed form are fixed.

## Decisions and their reasons

- Category ML / Inference. The graded work is a decode search over a scoring table with repeat
  suppression, length penalty and a pruning bound; the machinery in the tree is tokens, prompts,
  beams, scores and a stop token, so the category is carried by the code and not by the story.
- Six editable files rather than one: the rules the task turns on live in different places
  (refusal state, kept set, selection, loop order, bound) and a one-file patch would make the
  task a local fix.
- The stop token's score counts and its length does not. Both halves are stated; they are the
  cheapest pair of boundary conventions to get wrong and each has its own enumerated case.
- Every program has S at least 1, so a hypothesis always has at least one token and the kept-set
  line always carries one.

## Stage 7 re-attack (2026-09-22)

Read the final brief cold and tried to one-shot a plan against the built tree. The first plan
still puts the refusal state on the beam: every rule about lending is stated, but the structure
those rules force - a record per beam, a record per member, and the lent set rebuilt from the
members that remain - is not, and the plan that puts a closed hypothesis's spans into the live
beams is both smaller and wrong. The load-bearing facts are still spread: the ordering of the
two passes lives in the step loop, the lending in the span module, the membership in the kept
set, and the reach in the halt module, and no one of them can be settled without the others.
The brief does not telegraph the method: it says what happens to spans when a hypothesis is
kept and when it is dropped, and never that the state is shared, carried or reference counted.
The honest estimate is unchanged at 2 of 8.

What did drift during the build: the environment came out at 258 Python lines against 330
planned and the reference at 245 against 300. Both are inside the retained band (229 to 544,
and 110 to 424) and inside the checker's drift tolerance, and `tools/difficultycheck.py` scores
the built tree 100 of 100. The residual risk is that the tree sits at the low end of the band.

## Quality self-review (docs/QUALITY-REVIEW.md, 2026-09-22)

Walked criterion by criterion, each answered with what satisfies it.

- Tests described in the brief, and brief checked by tests: `authoring/beam-ban-carry/trace.md`
  carries a row per test function, per enumerated program, per collected artifact, for the clock
  and for each of the 17 rules of the sealed model. The converse holds too, with one honest
  exception: the sentence bounding the settings (N at least 2, S at least 1, and the width, the
  ceiling and the size of the kept set never below 1) describes the inputs rather than a
  requirement on the agent, and no assertion grades it; the generator honours it.
- Output paths named: the six collected files are listed in the brief with absolute paths, and
  `tracecheck` fails when one is not.
- Schema specified: the four printed line forms are given literally, with their order and the
  rank base.
- Boundaries and conventions: at least S emitted rather than more than S; more than H held
  rather than at least H; strictly greater for the reach; the ceiling read at T; three
  tie-breaks each written out; ranks from 0.
- Graded quantities defined: sequence, span, length, final score and reach each have a sentence,
  and each says what it excludes.
- No contradiction, no stale count: every number in the brief and in `task.toml` was re-derived
  from the code after the last generator change - four programs shipped, five requests each in
  the two scale programs, 2800 and 900 steps, a kept set of thirty, three of each scale size,
  three hundred and sixty small, forty-two by hand, eleven families, forty-nine cheats, thirty-two
  readings, and six timings.
- Verifier requirements in the text: the collected six, the pristine overlay, that a new file
  beside them is never collected, the `one(sp, name, prompt)` entry the driver calls, and the 60
  second clock.
- Prose: read through for runs of same-structured sentences and reworked twice.
  `tools/textcheck.py` is clean against `focus-return-point`; against `share-register-screen` one
  finding survives, that the cadence is more even than that brief's.
- Verifier rigor: the stage is executed on programs generated after the agent's container is
  gone, so no state the agent could write stands in for execution. `tests/test_outputs.py` opens
  with the frozen contract and each section says which rule it grades. Nothing depends on the
  wall clock except the stated limit, on the network, or on an order that is not itself graded.
- Environment hygiene: `tests/` and `solution/` are not copied into the agent image
  (`tools/imagecheck.py` lists the 23 files it would hold). Test dependencies are baked into
  `tests/Dockerfile`, pinned with `==`; no apt package is pinned. Every path the brief names
  exists in the tree and is spelled the same.
- Solution quality: `solution/solve.sh` copies six source files into place and runs the shipped
  driver; nothing is echoed as an answer, and it uses nothing the agent could not.
- Anti-cheating: the answers live only in `tests/seal`, which is root-owned and 0700 before any
  submitted line runs; the probes record a permission error on it. No repository is cloned.
  Grading is exact string equality, so a degenerate output fails.
- Metadata: category ML with subcategory Inference, the graded work being a decode search over a
  scoring table; `tools/catcheck.py` measures the ML vocabulary at 14 hits in the environment
  against 83 in the prose, so the category is carried by the code. Six tags, none of them
  restating the category or the subcategory. `difficulty_explanation` names the step that breaks
  and says that the legacy register is a deliberate choice. Nine hours is consistent with the
  claim.

## Validation status

| Check | Status | Notes |
|---|---|---|
| Agent image builds | not run | the egress policy denies Docker Hub's blob CDN in this session, so no base image can be pulled; `tools/imagecheck.py` assembles the image's contents from the Dockerfile and runs the shipped programs against them instead, and is clean |
| No answer leaked into agent image | pass | `imagecheck` lists the 23 files the image would hold: the app tree only. `extraneouscheck` and `deadfieldcheck` clean; nothing from `tests/` or `solution/` is copied |
| `harbor run -a oracle` = 1 | pass (host emulation) | harbor is not installed here and Docker cannot pull; `authoring/beam-ban-carry/host_trial.py` runs `tests/test.sh` verbatim as root with the privilege drop, the locked reward channel and the declared artifacts only. Reward 1, all tests passed; the final run was 51 of 51 trials plus 2 of 2 variants |
| `harbor run -a nop` = 0 | pass (host emulation) | reward 0 |
| Cheats all score 0 | pass (host emulation) | 49 of 49 on the final run, including 10 isolation probes; `authoring/beam-ban-carry/cheat_report.py` asserts the layer: every wrong reading is caught by the enumerated program named for it, 0 findings |
| Correct variants score 1 | pass (host emulation) | 2 of 2, `variants/var-a` and `variants/var-b` |
| Packaging | pass | `scripts/package.py` built `tasks/beam-ban-carry.zip`, 96 entries; `tools/zipcheck.py` clean |
| `tracecheck.py` (every graded assertion traced) | pass | clean |
| `readingcheck.py` | pass | 32 of 32 readings separated by the enumerated set |
| `onelinecheck.py` | pass | 2 of 4 graded decisions have a short rule, 2 do not |
| `preflight.py` | pass | no errors; the warnings are the known method-call false positive on unused public functions, 27 of them against 16 to 26 on the retained bundles |
| `catcheck` / `hintcheck` / `structcheck` / `solvecheck` / `deadfieldcheck` / `extraneouscheck` / `forgecheck` / `imagecheck` | pass | all clean |
| `simcheck` | reviewed | the Dockerfiles and the verifier harness share a shape with the retained bundles, which is the house scaffolding; its conceptual verdict is that this task grades nothing an earlier one grades |
| `textcheck` | reviewed | clean against `focus-return-point`; one residual finding against `share-register-screen`, that the cadence is more even than that brief's |
| `harbor check` rubric | not run | no API key in this environment |

## Open questions and next steps

Build the environment, then the independent model, then the reference. Measure the two scale
families before the brief quotes a limit.
