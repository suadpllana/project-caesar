# Frontier Bench workspace

Follow `AGENTS.md` as the operating manual. The retained task inventory is in `README.md`.
Before designing or hardening another task, read `docs/DIFFICULTY.md`,
`docs/QUALITY-REVIEW.md`, and `docs/PASSING-TASK-RESEARCH.md`.

Historical task transcripts and retired project notes were deliberately removed. Do not restore
them as examples; only the projects listed in `README.md` belong in this checkout.

## Lessons, measured (2026-09-06, `token-seam-emit`)

Four defects found by local gates before submission, each with the number that found it:

- **An ablation that measures unreachable variants measures nothing.** The first
  core-versus-periphery run ablated `sm.py`, which ships correct, and reported the character
  seam as the dominant failure at 47.8% of requests against the core's 15.2%. No agent
  produces that variant. Rebuilt as reachable whole-solver readings
  (`authoring/<slug>/readings.py`); the core reading now fails 50.5% and every reading is
  separated *and* named by an enumerated case. Frequency is not the point either: with 300
  nonce requests and all-or-nothing grading, any reading moving 1% of requests scores 0.
- **A cheat sweep that never installs the cheat reports 18 clean zeroes.** `trial.py`
  treated a whole app tree as a flat module directory, found only `run_stream.py`, and
  graded every cheat as the shipped tree. Caught only because `cheat_report.py` asserts
  *which* test catches each attestation probe. Assert the layer, never just the reward.
- **A probe that attacks at import time attacks nothing.** `cheat-kill-monitor` freed the
  monitoring tool id on import, before the runner arms it, and scored 1. Attestation probes
  must interfere during the run.
- **Fingerprints must not `repr()` nested code objects.** A `repr` of a code object carries
  its filename and address, so any function containing a generator expression hashed
  differently every run and failed the reference. Recurse into nested code instead.

- **Authoring scratch inside the task folder ships.** `package.py` zipped `.trial/` and
  `.cheats/` from an authoring run still in flight: 455 entries instead of 70, and
  `zipcheck` caught it only because the stray files were newer than the zip. Every
  authoring script now writes to `tempfile.mkdtemp` outside the bundle. Related: `zipcheck`
  rejects CRLF in `.py` and `.json`, not only in `.sh`, and Git normalising on commit hides
  it because the working copy is what gets zipped.

Two findings the models caught in the reference itself: an occurrence cache that froze the
first index it found missed a longer stop completing later but starting earlier, and a
backward character scan disagreed with a forward one on a malformed lead byte. Both were
invisible to 1200 random requests until a stop pool containing the shape was added.

## Lessons, measured (2026-09-06, `reach-pair-sweep`)

- **A mechanical variant that renames nothing proves nothing, and says so quietly.**
  `make_variants.py` built the mirror with a regex whose `\b` had been written into the file as
  a literal backspace byte (`\x08`) by an earlier patch. It matched nothing, so no identifier was
  renamed, the "still carries reference names" guard found nothing to complain about, and the
  mirror shipped as the reference with its docstring stripped - scoring 1 for the wrong reason.
  Two rules follow: a rename must assert it fired (`re.subn`, count > 0, fail on zero), and
  never patch Python escapes through a shell heredoc. Three separate edits in this session wrote
  `\x08` or a raw newline into source that way before the fourth used line-index replacement.
- **Ask what a wrong reading moves before believing your estimate.** The proposal put the
  pair-table-swept-once reading at ~35% of cases. Measured on 600 unshaped programs it moved
  3.7% - a tenfold error, and in the safe direction only by luck. The shaped `chain` family
  lifts it to 42.5%. A generated population that is not deliberately shaped around the mechanism
  does not exercise it, and the estimate you would have shipped is the one nobody checks.
- **The worked example is an oracle unless you measure that it is not.** The brief needs one
  record printed verbatim or a format slip fails every case for a reason that is not the task.
  Of 16,361 candidate programs showing all four line kinds, 184 decide none of the six wrong
  readings; `progs/small.txt` is the smallest. Search for the example, do not choose it.
- **`readingcheck` looked for `readings.py` inside the task folder, where `extraneouscheck` and
  `onelinecheck` both say it must not live.** Two tools in this kit disagreed. `readingcheck`
  now prefers `authoring/<slug>/readings.py` and falls back to the task-local path.
- **CRLF again, and again in the file no gate reads as text.** `build_gt.py` wrote `gt.json`
  with `write_text` and no `newline=`, so Windows made it CRLF and only `zipcheck` on the built
  archive caught it. Every generator that writes a shipped file now pins `newline="\n"` and
  asserts no `\r` survives.
- **The self-probe cannot be run by the author who wrote the model first.** The order here was
  brief, then sealed model, then environment - so by build time both discoveries were already in
  hand and a cold solve would have measured memory. It is recorded as not run, with the reading
  separations and the no-oracle property standing in its place. A self-probe reported as passed
  by a contaminated author is worse than no self-probe.

- **A grep that reads the wrong field is a wrong answer delivered with confidence.**
  `reach-pair-sweep` was rejected on `timeout-floor`: `[agent] timeout_sec = 900` against a
  3600 s floor, for a task whose own brief claims eight expert hours. The number came from
  `grep -E '^timeout_sec' task.toml | head -1`, which matches the `[verifier]` section because
  it sits above `[agent]` in the file. Every retained bundle uses 14400; the check reported 900
  for all eight. That false reading was then put to the contributor as "matches all eight
  retained tasks", so their approval was approval of a fact that was not true - a confirmation
  obtained on bad information transfers no responsibility. Two rules: read a keyed field with an
  awk section guard or a TOML parser, never a bare grep for a key that repeats under different
  tables; and sanity-check the value against the task's own claims before quoting precedent,
  because 15 minutes for an 8-hour task is wrong on its face whatever the neighbours do. The
  floor was recorded nowhere locally - only the 18000 s ceiling was - so it is now in
  `docs/RULES.md`, `AGENTS.md`, and as a `preflight.py` error that fires on the old value.

- **Two reviews can pull in opposite directions, and the resolution is usually C3.**
  `reach-pair-sweep` was cut back on a contributor review that called the incremental-marking
  rules guessable conventions and warned against a sprawl of corner cases. The quality review
  then failed `difficult` on exactly what that produced: "the rules are each stated explicitly
  and the remaining work is ~40 lines". Restating the cut rules would have failed the first
  review again. The repair that satisfies both is a measured scaling boundary, because it adds
  difficulty without adding a single rule to the spec: the naive form stays semantically
  correct and stops fitting the stated budget. Measured here at 0.7 s against 129.8 s on
  identical answers, 185x, with the limit and the input scale both in the brief.
- **A regime you promised to measure and then dropped on a recommendation is a regime you never
  measured.** The proposal committed to "timing the reference against the naive implementation
  before contract freeze". That timing was never run - the axis was dropped on a judgement call
  instead, and the rejection came back on the axis that was missing. Worse, the first reference
  was itself the naive form, so the measurement would have failed and the defect would have been
  visible at freeze. Run the number you said you would run, before the design depends on it.

## Lessons, measured (2026-09-07, `reach-pair-sweep`)

- **A redesign leaves stale prose in every file that described the old design, and the rubric
  reads all of them.** Swapping the reference from rescanning the pair table to indexing it by
  key updated one paragraph of `solution_explanation` and left the other, plus the docstrings of
  `tests/model.py` and `tests/test_outputs.py`, still saying "the reference rescans". The quality
  review failed `solution explanation quality` on the contradiction. When the reference changes
  shape, grep the whole bundle for every claim about what it does before anything else - the
  code was right and only the words were wrong, which is the cheapest possible rejection to earn.
- **Redesign silently invalidated an independence claim, not just a description.** The
  reference-versus-model independence had rested on rescan-versus-worklist. The scaling boundary
  forces both to index by key, so that axis closed for both and the claim had to be narrowed
  honestly to what survives: depth-first from a stack against breadth-first from a deque, two
  calls with a blocked set against one colour dict painted twice. An independence claim is a
  measurement, and a redesign can spend it without touching the sentence that asserts it.
- **Counts drift with the generator.** Adding the `wide` family moved the nonce population from
  320 to 335 and the family count from four to five, both quoted in `verification_explanation`.
  Numbers in shipped prose need re-deriving from the code after any generator change, not
  re-reading.
- **Verify the claim, not your memory of it - and check the checker.** The audit that confirmed
  each docstring against the source first reported two false claims that were both true: it
  counted call sites with a substring that also matched each function's own `def` line. A
  verification script that fails is not evidence until it has itself been checked.

## Lessons, measured (2026-09-07, `reach-pair-sweep` rebuild)

- **Check a design against the bundles that passed before acting on an argument about it.** The
  contributor's review argued that a shipped broken implementation is a worked example and an
  oracle. It is a good argument, and I acted on it by deleting the shipped collector. All seven
  retained passing tasks ship a working-but-wrong engine; not one ships a stub. That left this
  task at 107 environment lines with one editable file against a passing band of 229-544 lines
  and 1-7 editable files, and the quality review failed `difficult` twice on exactly that shape.
  Measuring the retained set takes one command and would have caught it before the first
  rejection, let alone the second.
- **Two `difficult` failures means the environment, not the brief.** The manual says so and it
  was right. The repair was not more prose or another axis bolted onto a small mechanism: it was
  a runtime with a nursery, an old space, a write barrier, pins and a handle stack, where the
  stated rules interact with structure the agent has to read. Nine graded decisions across five
  modules, four shipping wrong.
- **A reading you cannot express is a reading you cannot test.** The remembered set first stored
  (source, field), which made "trust the record instead of re-reading it" impossible to write -
  the reading measured 0% and no hand case caught it. Storing the written value too made the
  classic stale-entry bug expressible: it now moves 12% of a shaped population and `rset-stale`
  names it. When a reading refuses to separate, suspect the environment cannot represent the
  mistake, not that the mistake is rare.
- **`preflight` reads fields, not prose.** "Estimated solves out of 8: 2-5" is unparseable to it
  and reported as unanswered; a bare number with the range in brackets satisfies both the tool
  and the reader.
- **stdout buffering looks exactly like a hang.** A timing harness printing between subprocess
  runs showed an empty output file for ten minutes and sent me hunting a performance bug that did
  not exist - the fast cases had finished and were sitting in the buffer behind the slow one. Use
  `python -u` or `flush=True` in any script whose output is the measurement.

- **A rebuilt tree needs its Dockerfile rebuilt with it, and nothing local was reading it.**
  Reference verification rejected `reach-pair-sweep` with a compose build failure on both the
  oracle and the nop rows, five seconds each, no test run. The environment had been rebuilt from
  `rt/` and `cyc/` into `mem/`, `col/` and `ops.py`, and `environment/Dockerfile` still copied
  the old directory names; `COPY` on a missing source fails the build. Every local gate was
  green because none of them read the COPY lines, and the host emulation copies `app_src`
  straight out of the working tree with `copytree`, so the Dockerfile is never exercised on a
  machine without Docker. Both halves are now closed: `preflight` errors when a COPY source is
  absent from the build context, and `tools/imagecheck.py` interprets WORKDIR and COPY against
  `.dockerignore` to assemble what the image would hold, drops the reference in and runs the
  shipped programs - which turns a missing file into an ImportError locally instead of a compose
  error on the platform. Both were checked to fire on the real defect and to be clean on all
  nine bundles. The Dockerfile now copies `app_src/` whole rather than enumerating subdirectories
  that drift. Diagnosis rule confirmed: identical failures on the oracle AND nop rows, in
  seconds, are packaging, never the task.

## Lessons, measured (2026-09-07, `grid-spread-refresh`)

Six defects found by local gates during the build, each with the number or check that found it.

- **Two implementations can share one rule error, and a two-way differential finds it by luck
  or not at all.** The reference and the sealed model both failed to recompute a cell whose
  formula had been replaced, because both judged staleness only by the old record's reads and
  that record still agreed with the sheet. The differential run only diverged three edits later,
  when an unrelated value moved. A third implementation written to the rule as stated - settle
  the whole sheet by repeated passes, then derive the recomputed set in one comparison against
  the previous records - finds that class directly, because it has no incremental machinery to
  be wrong in the same way. It is now `authoring/<slug>/slow.py` and it is worth its hour.
- **A wrong reading that does not answer wrongly still has to be bounded before you measure it.**
  Dropping the rule that a block may not occupy a cell its own formula read does not produce a
  wrong report, it produces a loop: the block writes over its own input, the input changes, the
  block is asked for again. The readings harness hung for twenty minutes. A cap on recomputations
  was not enough on its own either, because a related shape spins inside a single evaluation;
  the harness now carries both a step cap and a `signal.alarm` per script.
- **A family shaped around a mechanism can still fail to exercise it, because an earlier check
  fires first.** The self-occupancy family measured 0.0% separation: the planted literals meant
  every block was refused for holding own content before the self-occupancy rule could decide
  anything. Reshaping it so the values sit at the bottom of the column and everything the block
  would reach is empty took it to 16.7%. When a reading measures zero, suspect the order of the
  checks, not the rarity of the input.
- **A probe that patches at import time patches nothing** - the same lesson as `token-seam-emit`,
  in a new shape. The frozen-runtime probe did `from sheet import core` at the top of a module
  that `core` itself imports, saw a half-built module, and raised before installing anything. It
  scored 0 for the wrong reason and the digest check it exists to prove never fired. `cheat_report`
  asserting the layer is what caught it; the reward alone said PASS.
- **`preflight`'s unused-function warnings are mostly noise and occasionally not.** Thirty-one
  of them here, twenty-nine being method calls the checker cannot resolve through an attribute.
  Two were real: a store field nothing read anywhere (the sheet's column count, which the script
  format now omits) and a method in the shipped tree with no caller, which announced the very
  distinction the task turns on. Grepping `\.name\(` across the environment separates the two
  classes in one command; do that rather than dismissing the block.
- **Check the brief against the retained briefs for borrowed construction, not only for cadence.**
  `textcheck` reported the draft as irregular enough on every axis while a six-word-phrase
  comparison against all nine retained briefs found whole clauses carried over - the
  must-still-work opener, the no-expected-output pair, the closing grading sentence. Calibrating
  style against accepted work slides into copying it without anyone deciding to. The comparison
  now lives in `tools/simcheck.py` and runs on every brief. It reports rather than fails, and
  the reason is the measurement: every earlier brief here shares runs with some other one, and
  `guard-mark-unwind` against `token-seam-emit` shares 98 of them, so a threshold would reject
  work already accepted. Read what it prints. `grid-spread-refresh` ships at zero shared runs
  outside the mandated closing sentence, which is where a new brief should be.
