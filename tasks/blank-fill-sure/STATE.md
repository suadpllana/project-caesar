# Task state

Working memory for `blank-fill-sure`. This file never ships: `package.py` drops it. Assume the
next session starts with no memory of this one.

## Current stage

`Stage 7 - Final gates` (Stages 1-6 closed 2026-09-22; built, traced, cheats and variants run
through the two-stage host trial; container gates not run - no image can be pulled here)

## Assistant's assigned role

You are a database engineer on the query side of a data-integration layer. Records arrive from
several sources and are merged; a value a source never supplied is kept as a labelled
placeholder, the same label wherever the merge learned that two unknowns are one, and every
column declares the values it may hold. You have written report engines over that store, you
know SQL null semantics, certain answers and the naive-evaluation theorem for unions of
conjunctive queries, and you know that the theorem assumes an infinite domain that real
schemas do not have.

## Source repository (repo-based tasks only)

- Repo URL: none - idea-based task, no third-party code vendored
- Task shape chosen (authored-on-top / ablation per docs/ABLATION.md): not applicable, no repository
- Contributor's relationship to it (maintainer / contributor / production user, how long): not applicable
- License, and why vendoring it is permitted: not applicable, nothing vendored
- Pinned commit vendored into environment/app_src/ (.git stripped): not applicable
- Load-bearing couplings found during research (file paths): not applicable
- Identifier degradation done? Conversion table lives at solution/ (never in environment/): the
  tree is written here in a legacy register directly (`rs/`, `cmp`, `join`, `keep`, `say`,
  `idx`); no name misdescribes what it holds and there is no source to degrade from
- Proper-noun sweep done? No product, project, company or engine name appears in the tree
- Upstream-diff check: there is no upstream to diff against

## Task summary

`/app` is the query side of a merged record store. A program declares tables whose columns each
allow a finite set of values (an integer range or a list of symbols), rows whose unknown values
are labelled placeholders `?name` (one label, one unknown value, wherever it appears), and
queries written as unions of join rules with optional `X != c` conditions. The report lists, for
each query, the rows it returns whatever values the placeholders turn out to have. The shipped
engine applies SQL null logic: a placeholder matches nothing, so it drops rows that hold under
every filling. The agent fixes the three evaluator files under `/app/rs/` so every program's
report is exactly right, inside a stated time limit on programs with thousands of placeholders.

## Why it is hard

The definition is one sentence and any strong agent can implement it by trying every filling;
that is exact and cannot finish on the graded scale. The retrievable fast method - let each
placeholder be a value only it holds, report the rows free of placeholders - is exact only when
a placeholder has spare allowed values and reaches no inequality. Finite column domains that
the data already uses make rows certain by case analysis, which that method never produces, and
an inequality lets a filling pick the compared constant, which that method never tries.

- Expert time estimate: 9 hours
- Why a frontier agent cannot one-shot the plan (the strategic answer - required): the plan it retrieves is the naive-evaluation theorem for unions of conjunctive queries, correct only over an infinite domain,
  and the plan it can write from the definition, trying every filling, is exact and infeasible at
  the stated scale. The correct method is a hybrid
  that no page describes: a placeholder is treated as a value only it holds exactly when it has
  more unused allowed values than there are placeholders and reaches no inequality; one that
  reaches `X != c` needs exactly two cases, c and a fresh value, and the case c can open a join;
  the rest are enumerated, and a candidate row is reported when its derivation conditions,
  split into groups that share no placeholder, hold under every assignment of some group.
- Tactics making that true (prong A poison, prong B withholding, prong C late failure): A1, A2, A3, B2, C1, C2, C3 and C4, across all three prongs.
  A1 the retrievable theorem and SQL null logic are both the prior
  and both wrong; A2 the brief never names certain answers, naive evaluation or case analysis;
  A3 no single technique fits, the method is chosen placeholder by placeholder; B2 label
  identity, the meet of column domains, unions across rules, inequalities, repeated variables
  and wildcards hold at once and each changes which placeholders may be fresh; C1 both
  directions fail, under-reporting forced rows and over-reporting rows an inequality guards;
  C2 an SQL database reproduces the wrong engine and the agent's own brute force cannot reach
  the scale families; C3 two families, each fatal to a different exact method; C4 exact,
  all-or-nothing comparison over programs generated after the agent has finished.
- Assistant's attack on the plan (its first plan, and where that plan is wrong): my own first plan, before this design, was naive evaluation:
  placeholders as distinct unknown constants,
  report the placeholder-free rows, because the theorem says that is exact for join-and-union
  queries. It is wrong twice at once. A status that allows only `open` and `shut`, read by one
  rule asking for open and one asking for shut, is certain and naive evaluation drops it; a
  distance compared `D != 0` is reported by naive evaluation and is not certain, because the
  distance can be 0. My second plan, enumerating every placeholder whose allowed set is small,
  is wrong on a region column whose forty allowed values all appear in a region table: its size
  says nothing, its unused values say everything. Only after those did the per-placeholder
  classification and the grouped check appear, and the grouped check was itself a discovery of
  the timing run: without splitting, the check was exponential on a program I had generated.
- Estimated solves out of 8 (design for 1, the hard edge; the realized rate drifts up): 2 (range 1-4)
- Difficulty record score (tools/difficultycheck.py on authoring/<slug>/difficulty.toml, before
  Stage 2; every attempt's score and what changed, until it reaches the band in
  docs/DIFFICULTY-SCORE.md): attempt 1 on 2026-09-22 scored 100/100, in band, no hard stop;
  only warning was the unmeasured gate, measured the same day (below). Nothing changed between
  attempts because there was one.
- Difficulty score anchor (50 at first complete submission, approved by contributor): not yet submitted
- Score history (date, score, what moved, and any pipeline re-anchor): 2026-09-22 difficulty
  record 100; originality record 97 then 100 after a stop-word fix in the checker (below)
- Leak audit (docs/DIFFICULTY.md): for each mechanism, what in the bundle could let an agent
  discover, name or verify it without reasoning? Answer must be "nothing": no sample ships with
  its report; the brief quotes one line of one program and that line turns on label identity,
  a rule the brief states; the frozen domain module parses and tests membership and nothing
  else, so no meet, size or unused-value count ships; no field anywhere stores a label's
  allowed set, its occurrences or a classification; the evaluator files are `cmp`, `join` and
  `keep`, and no name in the tree says fresh, cover, case, certain or completion.
- Expert path, described step by step (the harder the aim, the more this guard must hold):
  run the shipped programs and see the null-logic engine drop rows that two rows sharing a label
  produce under every filling; write the definition as a brute force over fillings for small
  programs and diff naive evaluation against it on random programs with small allowed sets,
  finding rows forced by case analysis and rows wrongly reported past an inequality; take each
  label's allowed set as the meet of its columns and derive when it may stand for a value only
  it holds (unused allowed values, counted against every label, and no reachable inequality);
  rebuild the join so a binding carries equality and inequality conditions on the labels that
  matter; give a label that reaches `X != c` the cases c and fresh and let c take part in joins;
  for each candidate row split its derivation conditions into groups sharing no label and report
  it when some group holds under every assignment; time the wide and flag samples against the
  limit and confirm everything against the brute force, including labels sharing one spare
  value.
- Originality check: searched 2026-09-22 (queries in the originality record). The literature
  covers certain answers over marked nulls, the naive-evaluation theorem for unions of
  conjunctive queries under an infinite domain, SQL three-valued logic against certain answers
  (Libkin and Guagliardo), and hardness and counting results for finite domains; none gives a
  method for finite per-column domains, and no task, exercise or library found does this.
- Distinctness record score (tools/originalitycheck.py on authoring/<slug>/originality.toml, at
  Stage 1 before the difficulty record, again once instruction.md exists; every attempt's score,
  and the crowded archetype named - docs/ORIGINALITY.md): attempt 1 scored 97 with 3 points lost
  on "substrate shares they, whose with note-carry-forward" - two function words, not a
  substrate. `substrate_terms` in the checker now drops English function words; `--selftest`
  (all twelve seeded defects still fire) and `--calibrate` (all three negative controls below 90)
  pass after the change, and the record scores 100. Crowded archetype named: query planner and
  join ordering (on the Databases list); the departure is that no plan or order is graded.
- Nearest already-submitted task (from authoring/submissions.toml or the platform's own flag),
  what overlaps, and which of the five surfaces separate them: alias-settle-report. Both grade
  an output that must hold across every admissible completion of unknown information and both
  have an exact search that collapses in a special case. All five surfaces differ: it settles
  item identity from timed sameness and difference tags and grades a filing tick; this evaluates
  join queries over a static store with finite allowed sets and grades answer sets.
  delta-view-retraction, the other Databases entry, shares only the label.

## Stage 1 measurements (prototype, scratch, 2026-09-22)

A prototype of the definition (brute force over every filling) and of the fast method was
written before any contract, to test the design's claims rather than trust them.

- Unshaped random programs: the fast method agreed with the brute force on 1744 of 1744 and
  again on 869 of 869 after a fix; but the wrong readings barely moved them (null logic 7.8%,
  naive evaluation 5.6%, spare-one 0.3%, inequality-as-fresh 0.3%, query-constants 0%,
  first-column domain 1.8%, per-rule union 0.1%). An unshaped population does not test this.
- Shaped families, 250 programs each: the fast method agreed with the brute force on all 1500.
  Each wrong reading moves its own family hard: first-column domain 100% of `meet`,
  query-constants 57% of `qconst`, inequality-as-fresh 50% of `trade`, per-rule union 53% of
  `union`, spare-one 19% of `pigeon`, null logic and naive evaluation 23% to 100% everywhere.
- The gate, measured: on a wide program of 19019 rows and 7897 labels the fast method took
  0.65 s; the exact method without the fresh-value classification was killed at 300 s; the exact
  method without splitting conditions into groups took 0.65 s there. On a flag program of 1701
  rows and 3360 labels the fast method took 0.04 s, the unsplit check was killed at 300 s, and
  the method without the fresh classification took 0.04 s. Each family kills a different exact
  method. The first wide timing was 18 s, from counting a label's unused values by scanning
  every constant; a sorted-constant bisect fixed it.
- One design error caught by reasoning before timing: a flag family whose accounts carry one
  placeholder each does not need the split, because a plain backtracking search prunes each
  wrong value at once. Groups need several falsifying assignments each - two placeholders per
  account - and a group every assignment satisfies placed after them.

## Build measurements (Stages 3-6, 2026-09-22)

- Tree: 346 lines of Python in `environment/app_src` across 10 modules, 3 editable files that all
  ship as SQL null logic, 4 shipped programs (tiny 11 lines, shop 142, wide 19046, flags 6005).
  Reference 474 lines across `solution/cmp.py`, `join.py`, `keep.py`, 484 with `solve.sh`.
- Agreement: the reference against the brute force on 1659 small programs, the model against the
  brute force on 1657 and on 565 shrunk family programs; 40 of 40 small flags programs. Both
  correct variants, the reference and the model agree on all 339 graded programs of a seed.
- Timing of the whole graded set (339 programs, one process, this host): reference 2.3 s, ok-b
  3.5 s, ok-a 34.7 s. In the host trial with grading: oracle 8.1 s, ok-b 8.9 s, ok-a 40.9 s.
- Memory on the six big programs, under a 2048 MB address-space cap: reference 51 MB, model 50 MB,
  ok-b 43 MB, ok-a 74 MB.
- The exact readings the limits exist for: slow-no-split was killed by the 300 s clock in the host
  trial (worker exit 124), and alone on one flags program ran 1800 s without finishing (killed there, peak 20 MB). slow-no-fresh
  exhausts 2048 MB in 38 s on the first wide program (MemoryError; 90 s for the whole set under
  the cap, every wide program failing); without a cap it was past 5.7 GB after two minutes and
  still growing, and was killed to protect the host. used-only, a semantic reading, grows the same
  way on wide programs and is also caught by its hand case.
- Two design errors found by measurement during the build. The first flags family let the
  reference's frequency-ordered search find the covering group first, so the unsplit search
  finished in time; it was rebuilt from like-shaped groups (four conditions each, the status in
  all four), where only the constants decide which group covers. And the first flags timing of
  the unsplit reading had no per-program guard, so the authoring report hung; `cheat_report.py`
  now runs each program under an alarm.
- Checker defects found by checking the checker, all in authoring tools: `trial_all.py` matched
  "missing" in grader source echoed by a traceback (the real failure was "program altered"), and
  credited a reading's named case when a dead worker had failed every test; the forged-answer
  cheat carried the answers re-encoded, so `forgecheck` could not see it; and `cheat_report.py`'s
  docstring promised a forgery check its code never ran. Each is fixed and re-run.

## Instruction contract (docs/INSTRUCTION-CONTRACT.md, read before anything else)

Every graded assertion traces to a sentence in the instruction. The walk is
`authoring/blank-fill-sure/trace.md`.

- Instruction trace (authoring/<slug>/trace.md; rows walked, NOT STATED left, tracecheck result): authoring/blank-fill-sure/trace.md walks 4 test functions, 33 hand cases, 3 artifacts, the worker's tree building and entry point, the printer, the 300 s clock, the 2048 MB cap, the standard-library-only image and every rule of the sealed model (21 rows); no NOT STATED left; `python tools/tracecheck.py blank-fill-sure` clean on 2026-09-22.
- Identifiability (readings enumerated, which survived the published evidence, what separated them): 15 semantic readings plus the shipped engine's null logic, each ruled out by a quoted sentence and failed by the hand case named for it (readingcheck: all 15 separated); none survives the published evidence. Two exact-but-slow readings are separated only by the clock and the memory cap. The worked example rules out the shipped engine, possible and smallest-fill, all misreadings of the stated definition, and none of the method's decisions (measured: fresh-all, ne-fresh and no-ban differ from the reference on tiny.txt only in the far query, whose output the brief does not give).
- Shortcut strategies scored (nop, constant, positional, replayed example; score and cases matched): all score 0 (authoring/blank-fill-sure/shortcuts.py, 33 hand and 306 generated programs): nop 16/33 and 173/306; constant empty report 8/33 and 75/306; positional first-rule-only 25/33 and 198/306; replayed example 0 and 0; textbook evaluation 20/33 and 173/306; possible 23/33 and 109/306; forged hand answers 33/33 and fail the generated set.
- Independent implementation behind every tolerance and limit (path, measured headroom): no numeric tolerance. The 300 s clock: variants ok-a (34.7 s on the whole graded set, 8.6x headroom) and ok-b (3.5 s), both written apart from the reference, and the sealed model; the 2048 MB cap: peaks of 74 MB (ok-a), 43 MB (ok-b), 50 MB (model), 51 MB (reference) on the six big programs, 27x headroom.
- Undecided decisions from the cold-reader pass (author-run or fresh session; sentence or example added for each): author-run, in the mechanical form of docs/INSTRUCTION-CONTRACT.md, by the author who wrote the model, so it is contaminated and recorded as such; no fresh-session reader was run. Every printed token (the ans line and its count, row values, row order, the empty-head row) was listed with the model branches behind it and the four clusters put to each. One gap was found by the pass and closed with a sentence: which values of a returned row are ints and which strs, which decides sort order. The rest were already settled by a sentence written for them in the first draft - ranges include both ends; a placeholder's value need not appear elsewhere; two placeholders may share one; a zero-head query prints its name alone; queries print in first-rule order even with no rows; the run is one Python 3.12 process, standard library only, one CPU, 2048 MB, 300 s - or by the grammar: a condition's constant is any integer or symbol, allowed by the column or not.

## Verifier contract - FROZEN after Stage 2

Frozen 2026-09-22. A change to anything below changes what "correct" means and needs the
contributor's explicit approval.

- Artifacts the agent produces: `/app/rs/cmp.py`, `/app/rs/join.py`, `/app/rs/keep.py`.
  Nothing else is collected. The verifier lays those three over its own pristine copy of the
  tree; a new file beside them is never collected.
- Frozen interface: `/app/run_ask.py` loads a program with the frozen loader, calls
  `report(store)` in `rs/keep.py`, and prints what it returns with the frozen printer.
  `report` returns a mapping from query name to an iterable of rows, a row being a tuple of
  ints and strs of the query's arity. A query missing from the mapping prints as empty.
- What is checked: the printed report of every graded program, line for line, exactly. Thirty
  or so hand programs against `tests/seal/gt.json`, frozen before the grading file is written;
  about three hundred generated programs against the sealed model, which must itself still
  reproduce `gt.json`. The whole graded set must finish inside the stated wall clock on the
  worker stage; that clock is the only limit.
- Tolerances: none. Lines are compared as strings.
- Ground truth, and where it lives: `tests/seal/model.py` and `tests/seal/gt.json`, in a
  directory `chmod 700` before the privilege drop, so code running inside the verifier cannot
  read it.

### Program grammar (stated in the brief; the frozen loader parses it)

- `table <name> <allowed> ...` - one allowed set per column: `lo..hi` (integers, inclusive,
  0 <= lo <= hi <= 999999999) or `s1|s2|...` (symbols). Tables come first.
- `row <name> <value> ...` - a value is an integer, a symbol, or `?label`. Every constant is
  allowed by its column; the columns a label sits in allow at least one value in common.
- `rule <query> <Var> ... :- <item>, <item>, ...` - an item is an atom `t(a, ...)` whose
  arguments are variables, integers, symbols or `_`, or a condition `<Var> != <constant>`.
  Head variables and condition variables occur in an atom of the rule. Every rule of one query
  has the same number of head variables. Integers are digits without a sign or leading zero;
  symbols and names start with a lowercase letter; variables with an uppercase letter.

### The graded decisions

1. Label identity: one label is one value everywhere in the program.
2. A label's allowed values are the values every column it sits in allows.
3. A filling gives every label one allowed value; two labels may get the same value.
4. An atom matches a row when its constants equal the row's values, a variable takes one value
   everywhere in the rule, and `_` matches anything; an integer never equals a symbol.
5. `X != c` holds when the value bound to X is not c.
6. A query's result under a filling is the union of what its rules derive.
7. The report of a query holds a row of constants exactly when the query returns it under every
   filling; each such row once. Rows containing a label never appear.
8. Order: queries in the order of their first rule; rows sorted value by value, integers before
   symbols, integers by value, symbols by character codes; `ans <query> <n>` then one line per
   row, `<query> <v1> ...`.
9. Scale: the whole graded set, including programs of about twenty thousand rows and several
   thousand labels, inside the stated wall clock, on the Python standard library.

Both sides of every fence are graded: under-reporting (null logic, fresh-value evaluation,
per-rule union, wrong allowed sets) and over-reporting (fresh-value evaluation past an
inequality, spare-one freshness, too few cases enumerated) each fail enumerated cases, and
ordinary programs without labels, or with labels no query reads, must be answered exactly.

### Implementation choices the verifier must accept, and does not grade

How labels are classified, which sufficient test decides that a label may stand for a value only
it holds, join order, index shape, how conditions are represented, how a candidate's conditions
are split and searched, and any internal naming. Not free, but not asserted either: trying every
filling, or checking a row's conditions without splitting them, cannot finish the scale families
inside the wall clock.

### Independent evidence

The sealed model is written apart from the reference, with a different evaluation order
(bottom-up joins of whole relations against the reference's top-down backtracking) and a
different validity search. An authoring brute force over every filling is the definition itself
and checks both on every small program. Two further correct variants live under
`authoring/blank-fill-sure/variants/` and must score 1.

## Decisions and their reasons

- **300 s, not the planned 120.** The limit sits between the slowest correct implementation
  measured (ok-a, 34.7 s, with no pruning at all) and the exact readings the scale families
  exist for (the unsplit search runs past 300 s on one flags program alone). The 8.6x headroom
  over ok-a is for slower graders, not for the reference, which needs 2.3 s.
- **Memory is stated and was measured, not assumed.** `task.toml` gives 2048 MB and the brief says
  so. Every correct implementation peaks under 75 MB; the no-fresh exact reading dies of it.
- **The worked example is one line, and it was measured, not chosen by feel.** It rules out the
  shipped engine and two misreadings of the stated definition, and no decision of the method.
- **Readings that are exact are recorded against the clock, not as readings.** `readings.py`
  keeps them in READINGS for readingcheck but out of EDITS, so the trace's Readings table holds
  only readings a hand case can separate, as the retained trace does.

- **Software / Databases.** The graded work is query evaluation over an incomplete relational
  store: label identity, column domains, joins, unions, inequalities, answer sets. The one
  visible Databases ledger entry maintains aggregates under a change stream.
- **Chosen over the prepared seeds.** The retained probe trajectories show strong agents
  transcribing every stated rule of a rulebook correctly in one write and checking themselves
  with a brute force (`probes/*/notes.md`). The seeds in `prompts/` are rulebooks. What moved a
  task into the band was a semantic scale boundary with an invariant that holds in part of the
  input (`alias-settle-report`); this design is built on that from the start.
- **Inequalities against constants only.** `X != Y` between two variables would let a filling
  merge two fresh placeholders, which multiplies the case analysis without adding a rule an
  expert meets more often. `X != c` is the everyday report condition and alone breaks the
  fresh-value argument.
- **No keys or dependencies.** A key would force placeholders equal (a chase) and pull the task
  toward record linkage, which is `alias-settle-report`'s neighbourhood.

## Validation status

Host emulation means `authoring/blank-fill-sure/host_trial.py`: the agent stage and the verifier
stage run one after the other on this host, with `tests/test.sh` itself doing the privilege drop,
the locked reward, the sealed model and the reaping. It is not container evidence: one kernel,
the host's Python 3.11 where the image has 3.12, no image build, and memory capped with an
address-space limit (`--mem 2048`) where the container's cgroup would kill instead.

| Check | Status | Notes |
|---|---|---|
| Agent image builds | not run | Docker Hub blobs are denied by this session's egress policy (403 on production.cloudfront.docker.com) and harbor is not installed. `tools/imagecheck.py` interprets the Dockerfile: 15 files, no caches, the reference runs all four shipped programs |
| No answer leaked into agent image | checked by reading | the Dockerfile copies `app_src/` only; no report, allowed-set helper or mechanism name ships; `extraneouscheck` clean |
| `harbor run -a oracle` = 1 | host emulation only | reward 1, 36 tests passed, 8.1 s with grading, under the 2048 MB cap, on the final `test.sh` |
| `harbor run -a nop` = 0 | host emulation only | reward 0; decided by `test_hand_case[self-same]` |
| Cheats all score 0 | host emulation only | 29 of 29 score 0 under the cap, each decided by the layer it was built for (`trial_all.py --mem 2048`: readings by their named hand case with a clean worker, the forgery by the generated programs, slow-no-split by the clock, slow-no-fresh by the memory cap, probes by denial, reaping, signature and rejection) |
| Correct variants score 1 | host emulation only | ok-a 1 (40.9 s), ok-b 1 (8.9 s) |
| `tracecheck.py` (every graded assertion traced) | clean | 2026-09-22 |
| `preflight.py` | clean of errors | 10 warnings, all the unused-public-function check missing `module.func(...)` calls: every flagged function is called that way (checked one by one) |
| Kit checks | clean | catcheck, hintcheck, structcheck, textcheck, deadfieldcheck, extraneouscheck, solvecheck, forgecheck, onelinecheck (no exact rule at depth 2 over 637 candidate rows), readingcheck (15 of 15 separated), imagecheck; simcheck: no NEAR, the environment Dockerfile HIGH at 0.71, conceptually distinct; originality 100; difficulty 100 |
| `harbor check` rubric | not run | harbor not installed; the manual quality review (Decisions, and the fixes it drove: the `report` name in the brief, the register note, the failure-direction grouping in the metadata) stands in for it |
| `package.py` + `zipcheck` | clean | 76 entries, no STATE.md, no caches; `tasks/blank-fill-sure.zip` |

## Open questions and next steps

- **Container gates were never run.** No image can be pulled in this session, so `harbor run -a
  oracle`, `-a nop` and every cheat in a real container are still owed, as is a real build of both
  Dockerfiles (their `RUN test -f` lines assert the layout the harness needs). Run them with `-o`
  outside the task folder before trusting the host-emulation rows above.
- **The easiness probe has not run.** The estimate of 2 of 8 solves is a design estimate. If a probe
  solves it, read `RAISE-DIFFICULTY.md` and feed the trajectories to `tools/leakcheck.py`.
- **The cold reader was author-run.** A fresh session given only `instruction.md` and the agent tree,
  asked which decisions the text leaves open, is the stronger test and is still owed.
- **`relevant_experience` is written as a profile of the expertise the task needs**, not as a claim
  about the contributor; the contributor may want to replace it with their own.
- On the ledger: `authoring/submissions.toml` carries this task as `pending`; update the verdict
  when the platform answers.
