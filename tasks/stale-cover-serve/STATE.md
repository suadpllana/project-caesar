# Task state

Working memory for this task. The assistant updates it after every stage. Assume the next
session starts with no memory of this one - anything not written here is lost.

## Current stage

`Stage 7 - Pre-flight and packaging`

## Assistant's assigned role

You are an engineer on the read path of a versioned key-value service: the layer that decides
whether a range read can be answered from what the cache already holds, at which version that
answer is, and what has to be fetched when it cannot. You have written the invalidation side of
one of these and the assembly side of another, and you know that the expensive bugs are never in
the lookup but in what a cache is allowed to claim.

## Source repository (repo-based tasks only)

- Repo URL: none - idea-based task, no third-party code vendored
- Task shape chosen (authored-on-top / ablation per docs/ABLATION.md): not applicable, no repository
- Contributor's relationship to it: not applicable
- License, and why vendoring it is permitted: not applicable, nothing vendored
- Pinned commit vendored into environment/app_src/ (.git stripped): not applicable
- Load-bearing couplings found during research (file paths): not applicable
- Identifier degradation done? Conversion table lives at solution/ (never in environment/): the
  tree is written here rather than degraded from a source. Identifiers are chosen in the legacy
  register directly (`rng/`, `seg`, `pick`, `hole`, `mend`, `knit`, `age`, `ask`, `mark`, `tune`)
  and no name misdescribes what it holds.
- Proper-noun sweep done? No product, project, company or framework name appears anywhere in the
  agent-facing tree. The domain words that remain (version, commit, store, range, cache) are the
  ordinary vocabulary of the work and carry no provenance.
- Upstream-diff check: there is no upstream to diff against.

## Task summary

`/app` is the read path of a key-value service: a cache of key ranges in front of a store whose
rows are versioned. A program is a text file of writes, commits and reads; `/app/run_rng.py`
replays it and prints `v` for each commit, `f` for each fetch and one `a` line per read carrying
the version the read was answered at and the rows. A read names a staleness allowance, and the
service's own contract is that an answer is served as of one version with every part of it
correct at that same version, at the newest such version the allowance permits. The shipped
service is the rehearsed pattern instead - an entry per range, deleted when a write lands inside
it, an age test on the entry, always answered at the present version. The seven files under
`/app/rng` are the graded artifact; the verifier lays them over its own pristine copy of the
driver, the store, the parser and the trace writer.

## Why it is hard

The first plan is the cache-aside pattern and it is wrong at the first decision of every read
that matters; the rule that replaces it makes an overtaken entry the thing that answers a read
rather than something to delete; and the rule after that makes the cache stop being a map of key
ranges at all.

- Expert time estimate: 9 hours
- Why a frontier agent cannot one-shot the plan (the strategic answer - required): because the memorised and retrievable answer to a range cache is look up, fetch the remainder, delete on
  write, and treat a staleness allowance as an age limit on an entry. Here an answer is served as
  of one version and every part of it must be correct at that same version, which kills the
  per-entry test and forbids deleting anything; and a fetch is correct from the version the store
  last wrote the keys it covers, so the cache learns about versions already past and its cached
  ranges start overlapping each other in key space while differing in version. A plan built on an
  interval map with a validity field has to be taken apart rather than corrected, and the
  wrongness shows up only in a version number on an answer line and in which ranges were fetched.
- Tactics making that true (prong A poison, prong B withholding, prong C late failure): A1, A2, B2, C1, C2, C3 and C4. A1 the shipped service is the model's prior implemented faithfully and it
  is the wrong answer; A2 the coverage question, the intersection of validity and the maximisation
  are stated as what the service does and never named, so the structure that survives them must be
  derived; B2 ten rules hold at once and each changes what a correct implementation of the others
  looks like; C1 both sides are graded, so refetching what is already current and serving pieces
  that were never simultaneously true both fail; C2 the store is reachable only through the fetch
  path the cache itself drives and the shipped engine prints a coherent trace for every program;
  C3 a deep family makes two exactly-correct searches infeasible inside the stated limit; C4 every
  program matches line for line against a population generated after the agent is gone.
- Assistant's attack on the plan (its first plan, and where that plan is wrong): my first plan was
  a dict of range entries each holding rows and a live flag, a read gathering the live ones and
  checking they cover the range, a fetch of whatever is missing, and a delete of every entry a
  commit wrote inside. It is wrong three times over. An entry a write overtook is exactly what
  answers a read aimed at the versions it was right for, so nothing may be deleted and the flag
  has to become a run of versions. A set of entries each recent enough on its own is not an answer
  unless one version is allowed by all of them, so the read becomes a maximisation rather than a
  lookup. And a fetch is correct from the store's last write rather than from the moment it
  happened, so validity does not arrive in time order and the refetched, combined and capped
  ranges sit on top of the ones already held - which the disjoint interval map my first repair
  builds cannot represent at all.
- Estimated solves out of 8 (design for 1, the hard edge; the realized rate drifts up): 2 of 8
  (range 1-4)
- Difficulty record score (tools/difficultycheck.py on authoring/<slug>/difficulty.toml, before
  Stage 2; every attempt's score and what changed, until it reaches the band in
  docs/DIFFICULTY-SCORE.md): attempt 1 on 2026-09-22 scored 99/100, in band, no hard stop. Nothing
  changed between attempts because there was only one. The single point is on `decisions.graded`,
  which is 8 against the 9 the top band wants and is the honest count of the enumerated decisions;
  it was left alone rather than tuned. The one warning was that the resource gate was declared and
  not yet measured, settled at Stage 4 and recorded below.
- Difficulty score anchor (50 at first complete submission, approved by contributor): not yet submitted
- Score history (date, score, what moved, and any pipeline re-anchor): 2026-09-22 record scored 99
- Leak audit (docs/DIFFICULTY.md): for each mechanism, what in the bundle could let an agent
  discover, name or verify it without reasoning? Answer must be "nothing". The shipped cache entry
  holds a key range, its rows and one number, so the version structure has to be introduced rather
  than filled in. The store's only public call returns the rows of a range and the one last-write
  number for that range, which is the fetch's own result and the primitive the rule is defined
  over; there is no way to ask it when a key changed. No shipped helper computes coverage - the
  shipped engine tests it inline against live entries only, in one of the files the agent
  replaces. The trace prints the fetches and the answer and nothing about the cache, and the
  version it prints is a graded output rather than a report. The sample programs ship without
  their answers; the one example quoted in the brief is the format example, whose four lines the
  shipped engine already produces, so it decides nothing about the mechanism. Confirmed by
  running the shipped engine on it.
- Expert path, described step by step (the harder the aim, the more this guard must hold):
  1. run the shipped programs, see that the staleness allowance is treated as an entry age, and
     find which module decides the served version;
  2. replace the live flag with a run of versions per cached stretch, because a commit ends the
     stretch's correctness rather than destroying what it knew;
  3. install a fetched stretch from the store's last-write number so it answers reads aimed at
     versions older than the fetch itself;
  4. watch the fetched stretches begin to overlap the closed ones and the combined and capped ones
     overlap the open ones, and replace the disjoint key map with a set of key-by-version
     rectangles;
  5. write the serving decision as the largest version inside the allowance at which the whole
     range is covered, and keep it apart from the uncovered-at-now computation that drives the
     fetch;
  6. settle the boundaries: a commit ends validity at the version before it, retention runs after
     each commit against the horizon, the slack is measured across the covered ground and the cap
     counts what combining left;
  7. time the deep programs, then replace the per-version search with a sweep over the ends of the
     rectangles carrying a covered-key count, and the per-commit table walk with an index over the
     key space.
- Originality check: searched 2026-09-22. What the literature carries is byte-range assembly for
  immutable objects (the HTTP caches, which never ask at which version the pieces were
  simultaneously true), snapshot-versioned result caches that compare one entry against the
  reader's snapshot and discard anything older, semantic caching's probe and remainder split, and
  bounded-staleness replication. Every component is documented somewhere; no source has an answer
  served at the newest version common to a whole cover, a fetch backdated to the store's last
  write, or fetch combining that costs reach into the past. The best retrievable page hands over
  the per-entry test this runtime specifically forbids.

## Instruction contract (docs/INSTRUCTION-CONTRACT.md, read before anything else)

Every graded assertion traces to a sentence in the instruction. The walk is
`authoring/stale-cover-serve/trace.md`.

- Instruction trace (authoring/<slug>/trace.md; rows walked, NOT STATED left, tracecheck result): 84 rows walked - 5 test functions, 37 enumerated cases, 7 artifacts, the 60 second clock and 18 rules of the sealed model split one per rule with its lines - plus 30 readings and 4 shortcuts. No NOT STATED row survived and `python tools/tracecheck.py stale-cover-serve` is clean. The trace is written by `authoring/stale-cover-serve/make_trace.py` from a hand-written mapping, which asserts every quote against the brief, so a reworded sentence fails there rather than leaving a stale citation.
- Identifiability (readings enumerated, which survived the published evidence, what separated them): 30 readings were written as whole engines by `authoring/stale-cover-serve/emit.py` and
  measured by `python tools/readingcheck.py stale-cover-serve 270`. 29 are separated by an
  enumerated case named for the rule. One, `install-per-hole`, was BLIND on the first run and the
  shrunk nine-line counterexample the tool printed is shipped as `install-run-whole`. One more,
  `holes-per-key`, is `equivalent`: the combining rule puts adjacent per-key runs back together
  whatever the slack, so the maximality of the holes is genuinely unobservable. It was promoted to
  a correct variant that must score 1 rather than left as a cheat.
- Shortcut strategies scored (nop, constant, positional, replayed example; score and cases matched): all four score 0 and `authoring/stale-cover-serve/cheat_report.py` says why. The nop fails two of the five test functions; `const-empty` and `const-now` each fail all 37 enumerated programs and all 90 sampled generated ones; `pos-always-fetch` fails 26 enumerated and all 90, caught first by `fresh-cover`; `forge-hand` carries the frozen answers, reproduces all 37 enumerated programs and fails 10 of the 90 generated. Every one of the 29 wrong readings is caught by the enumerated case the trace names for it, and the report is what asserts that rather than only the reward.
- Independent implementation behind every tolerance and limit (path, measured headroom): there is no numeric tolerance; the trace is compared string for string. The only limit is the 60 second
  wall clock on the stage that runs submitted code. Three independently written correct engines
  under `authoring/stale-cover-serve/variants/` settle the whole graded set of 401 programs in
  4.95, 5.10 and 8.40 seconds, against the reference's 5.09 - between 7 and 12 times the headroom.
- Undecided decisions from the cold-reader pass (author-run or fresh session; sentence or example added for each): author-run, mechanically, over every printed token; five gaps were found and closed in the brief, and they are listed in the cold-reader section below.

## Verifier contract - FROZEN after Stage 2

Frozen 2026-09-22. Ten graded decisions, the trace format and the artifact list are recorded in
the design record `authoring/stale-cover-serve/difficulty.toml` and restated at the top of
`tests/test_outputs.py`, which is the file a reviewer reads.

- Artifacts the agent produces: `/app/rng/seg.py`, `pick.py`, `hole.py`, `mend.py`, `knit.py`,
  `age.py`, `ask.py`. Nothing else is collected; the verifier lays those seven over its own
  pristine copy of the tree.
- What is checked: the stdout trace of every graded program, line for line, exactly. Thirty-seven
  enumerated programs against `gt.json`, frozen before the grading file was written; 364 generated
  programs against the sealed model, which must itself still reproduce `gt.json` on every run.
- Tolerances: none. The only limit is the 60 second wall clock on the stage that runs submitted
  code, validated against three independently written correct implementations.
- Ground truth, and where it lives: `tests/seal/model.py` and `tests/seal/gt.json`, in a directory
  `chmod 700` before the privilege drop.

### The ten graded decisions

1. The version a read is answered at: the largest in `[max(0, N - s), N]` at which the whole
   range is covered by content the cache accounts for at that version.
2. Whether the read is served from the cache alone or goes to the store.
3. The maximal runs of the range uncovered at the present version, in increasing key order.
4. Combining: a run beginning no more than the slack past the end of the previous one is taken
   with it, spanning the ground between.
5. The cap: more runs left than the cap allows means the whole requested range instead.
6. Installation: one stretch per run fetched, correct from the store's newest write across the
   whole of that run, 0 when it has never written one of its keys, and never folded into
   anything already held.
7. Invalidation: a commit that writes inside a stretch ends it at the version before the commit;
   one that does not leaves it open.
8. Retention after each commit: a stretch whose last correct version is below `N - H` goes; an
   open one never does.
9. The answer rows: the live rows of the range at the served version, each key once, in
   increasing key order.
10. Touch semantics: a write of the value already there and a delete of an absent key both count;
    two staged operations on one key leave the later one and count once; a commit staging nothing
    still makes a version.

## Decisions and their reasons

- **Software / Databases, not ML / Evaluation.** The graded work is a versioned-store read path:
  coverage, validity intervals, invalidation and fetch shaping. The category follows the skill
  exercised, not a narrative setting.
- **The allowance is a bound on the answer, not on the entry.** This is the whole A1 tactic: a
  per-entry age test is what the pattern comes with and it produces answers that were never
  simultaneously true.
- **A fetch is backdated to the store's last write.** Realistic for an MVCC store, and it is what
  makes validity arrive out of time order and the cached ranges overlap.
- **Invalidation carries keys, not values.** That is why a commit ends a stretch rather than
  updating it in place: the invalidation channel of a real range cache carries what changed, not
  what it changed to. It is also what keeps the task from collapsing into a write-through cache.
- **Fetch combining and the cap were added after the first environment measured 232 Python lines**,
  at the bottom of the retained band of 224 to 544 and the shape the quality review has failed
  `difficult` on twice. They are rules rather than scenery: combining makes a fetch correct from
  later than the holes inside it would have been, so saving a round trip costs reach into the past,
  and a capped read lays a stretch across everything already held. Both push the cache further from
  a disjoint map. The tree measures 254 lines and 7 editable files now, with a 309-line reference,
  and the difficulty record was brought in line with what was built: ten graded decisions rather
  than eight, seven collected files rather than six, two more interacting pairs, and the gate
  narrowed to the boundary that measured. It scores 100 with those corrections.
- **Retention is by horizon, not by count.** A count is an LRU, which the shipped engine already
  is; a horizon is what a bounded version window actually gives you and it interacts with the
  serving version rather than with memory.
- **`store.at` returns the rows and the last-write number together and there is no other call.**
  A separate "when did this range last change" entry point would hand over the backdating input
  for any range at any time, which is a derived quantity the cache is not supposed to have.

## The resource gate, measured

The naive families are exactly correct and are what a first implementation looks like. Measured on
this machine against the 60 second limit for the whole graded set:

| engine | deep-000 | deep-001 | wide-000 | wide-001 | scale total |
|---|---|---|---|---|---|
| reference | 3.37 s | 1.01 s | 0.10 s | 0.07 s | 4.55 s |
| every version in the allowance | 267.19 s | 52.88 s | 0.77 s | 0.37 s | 321.21 s |
| only the ends, coverage rebuilt at each | 70.42 s | 11.15 s | 0.11 s | 0.06 s | 81.74 s |

The whole graded set of 401 programs takes the reference 5.09 seconds and the sealed model 8.19
seconds. One deep program alone puts either naive engine over the limit. Both produce the
reference's traces exactly on everything they finish, so semantic correctness alone does not
pass. Re-measured on the final generator after the two fetch-shaping rules were added.

An earlier claim that a per-commit walk of the whole stretch table would also be gated was
**dropped after measuring it**: at the scale the programs reach it costs a few seconds, not sixty,
and `ok-no-index` - a correct variant with no key index at all - settles the whole set in 5.10
seconds. Only the serving search is gated.

## Stage 7 re-attack, run cold on the finished bundle

Read the final brief with the built tree in front of me and tried to one-shot the plan.

- **Is the first plan still wrong?** The plan from the prior - an entry per range, a live flag, a
  delete on write, an age test on the entry - is the shipped service, and it is wrong at the first
  decision of every read that matters. The plan *after* reading the brief is right in outline,
  because every rule is stated; it is wrong in structure. A live flag cannot hold a stretch that
  still answers older reads, a disjoint interval map cannot hold stretches that overlap in keys
  and differ in version, and a lookup cannot answer a question whose answer is a maximisation.
- **Are the load-bearing facts still distributed?** They are stated rather than hidden, which is
  the doctrine: nothing is withheld. What is not stated is which structures survive all ten rules
  at once, and that is unchanged since Stage 1.
- **Did the instruction come to telegraph the method?** No. It states the outcome of each rule and
  never a data structure; the worked example is the format example, four lines the shipped engine
  already produces.
- **Updated estimate of solves out of 8: 3** (range 1 to 5), revised up from 2 at this re-attack.
  The honest reason for the move is that every rule is in the brief, the tree is small enough to
  read in full, and a meticulous implementer who holds all ten rules at once wins. What stands
  against them: there is no feedback on any of the ten beyond the fetch lines and one version
  number, the grading is all or nothing over 401 programs, the structural discovery only shows up
  once a refetch has overlapped something, and the natural serving search is 21 to 79 times over
  the clock on the two deep programs.
- **What the checkers say from the other side.** `tools/onelinecheck.py` finds no exact rule at
  depth two for any of the three graded quantities - the version an answer is served at, whether a
  read fetches, and how many runs it splits into - over features read off the shipped table.
  `tools/difficultycheck.py` re-measured the built tree at 254 environment lines, 7 editable
  files, 309 reference lines, 38 cheats and 3 variants, and reports no drift from the design.

## Cold-reader pass

Author-run, mechanically, over every printed token: the `v` line, each `f` line and each field of
the `a` line, with the four clusters put to every decision that touches them. Five gaps were found
and closed in the brief while it was being written: that the version a read is answered at is
never below 0, that F is never below 1, that a commit staging nothing still makes a version, that
a run beginning exactly slack-plus-one keys after the previous one is not taken with it, and that
every key appears at most once on an answer line. One sentence survives the pass without a reading
that contests it - that a fetched run is kept as the run it was fetched in - because it is what
`install-run-whole` exists for and no shorter statement settles it.

## Validation status

| Check | Status | Notes |
|---|---|---|
| Agent image builds | **not run** | Docker Hub's blob host is refused by this session's egress policy (403 on `production.cloudfront.docker.com`), so neither image can be built here and `tools/docker_trial.py` cannot run. Not routed around. |
| No answer leaked into agent image | pass | `tools/imagecheck.py` assembles what the image would hold from the Dockerfile and `.dockerignore`: 16 files, no `tests/` or `solution/` content, and the four shipped programs run in it |
| `harbor run -a oracle` = 1 | pass, host emulation | `authoring/stale-cover-serve/host_trial.py oracle`: reward 1, 5 tests in 8.0 s. It lays the tree at `/app`, the kit at `/tests` and runs the bundle's own `tests/test.sh` unmodified - the drop to uid 1002, the 0700 reward directory, the session and clock on the worker, the reaper and the root grader. Everything except the image build. |
| `harbor run -a nop` = 0 | pass, host emulation | same harness: reward 0, two of five test functions failing |
| Cheats all score 0 | pass, host emulation | 40/40 trials behaved as required over oracle, nop and 38 cheats |
| Correct variants score 1 | pass, host emulation | three, run through the same harness with `--dir` |
| `readingcheck.py` | pass | 29 of 30 separated by a named case; the 30th is a correct variant |
| `onelinecheck.py` | pass | none of the three graded quantities has an exact rule at depth 2 |
| `forgecheck.py` | pass | one forgery probe carries the frozen answers; `cheat_report.py` grades it |
| `tracecheck.py` (every graded assertion traced) | pass | clean |
| `structcheck.py`, `hintcheck.py`, `catcheck.py`, `deadfieldcheck.py`, `extraneouscheck.py`, `solvecheck.py` | pass | clean |
| `preflight.py` | pass | 0 errors; the only warnings are the unused-public-function false positive every retained bundle trips |
| `harbor check` rubric | not run | no API key in this session |

## Quality self-review (docs/QUALITY-REVIEW.md, walked criterion by criterion)

**Instruction and verifier agree both ways.** Every graded assertion has its row in
`authoring/stale-cover-serve/trace.md` and `tracecheck` is clean. The converse was walked by
hand: every sentence of the brief is graded by the trace comparison except three that describe
the environment rather than a behaviour - that `/app/progs` holds four sample programs, the
scale of the two large ones, and the line naming the frozen files. All three were re-derived
from the tree rather than from memory.

**Counts, re-derived from the code after the last generator change.** 37 enumerated programs and
364 generated, 401 in all; nine small families at 40 each plus two wide and two deep; 38 cheats;
3 correct variants; 60 seconds. Checked mechanically against the generator: the largest key any
graded program mentions is 2047, the longest history is 12001 versions, the largest wide program
is 38256 lines and the largest deep one 28843, no program has a cap below 1, no read has lo above
hi and no key, value or allowance is negative. Every `/app` path the brief names exists in the
shipped tree, spelled the same way.

**Boundaries.** The band a read may be answered in (both ends, and the floor at 0), the commit
that ends a run at the version before itself, the horizon kept at exactly N - H, the combining
slack measured across the covered ground, the cap at more-than rather than at, a write that
changes nothing, a delete of a key that is not there, two staged writes of one key, a commit that
stages nothing, and the empty answer are all settled in the text, and each has an enumerated case
named for it.

**Verifier rigor.** The tests run the submitted modules over a pristine copy and compare the whole
trace; nothing is taken on the submission's word, and half two rebuilds the program list itself
and recomputes the digest of the text each record claims to have been run on.
`tests/test_outputs.py` opens with the frozen contract and is sectioned by what each block checks.
The only wall-clock dependence is the stated 60 second limit, measured against three independent
correct engines. Nothing depends on the network or on an ordering that is not itself under test.

**Environment hygiene.** `environment/Dockerfile` copies `app_src/` and nothing else; pytest is
pinned at 9.1.1 with ctrf 0.5.2 in `tests/Dockerfile` only; no apt package is used at all;
`tools/imagecheck.py` assembles what the image would hold (16 files) and runs the four shipped
programs in it.

**Solution quality.** `solution/solve.sh` copies seven source files into place and runs two sample
programs. It computes nothing by hand and writes no answer.

**Anti-cheating.** `tools/forgecheck.py` finds one forgery probe carrying the frozen answers and
no ground truth in the agent tree; `deadfieldcheck` and `extraneouscheck` are clean; the sealed
directory is 0700 before the privilege drop and `cheat-probe-answer-key` reports the exception
rather than the file.

**Metadata.** Software / Databases is a row of the guideline table and names the skill the graded
work exercises rather than a setting; `tools/catcheck.py` measures 59 database terms in
`environment/` against 148 in the prose; the five tags name techniques rather than the taxonomy;
`difficulty_explanation` names the concrete decision a frontier agent gets wrong and states the
legacy-register naming as a design choice; `expert_time_estimate_hours` is 9, consistent with the
claim.

**Known risks a reviewer should see.** The two images could not be built in this session, so every
container result above is the host emulation described in the validation table rather than a
`docker` run; the Dockerfiles themselves are checked by `tools/imagecheck.py` and by preflight.
`tools/simcheck.py` reports both Dockerfiles as near-identical to the retained bundles, which is
what happens when their content is prescribed by the kit - the canonical pytest pins, an artifact
parent per RUN line, `COPY . /tests/` - and there is nothing in them to author; `test.sh`,
`worker.py` and `reap.py` were written here and are not reported. `tools/textcheck.py` still puts
the brief's burstiness at 0.728 against 0.915 for `note-carry-forward` and its share of short
sentences at 14 per cent against 34; the cadence was reworked twice and the residue is what a
brief that states ten rules exactly looks like. Its two remaining dash asides are `N - s` and
`N - H`. Two sentences added during that rework restated rules already stated and were taken
back out at the final read; the patch that removed them asserts that it fired, because the first
attempt matched nothing and said so to no one. `harbor check` was not run: no API key is available in this session.

## Open questions and next steps

The easiness probe has not been run: this session has no probe harness, and a self-probe by the
author who wrote the model would measure memory rather than difficulty. The reading separations,
the measured gate, the cheat results and the cold re-attack stand in its place, and the estimate
above is what they support.
