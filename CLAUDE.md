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

## Lessons, measured (2026-09-08, `publish-settle-order`)

- **Measure the tree against the retained band before calling the environment done.** The first
  build of this task was 162 lines of Python across eleven files - under every retained bundle
  (229 to 544) and the exact shape the quality review has failed `difficult` on twice. Nothing
  else saw it: preflight, `extraneouscheck`, `imagecheck`, the oracle, the nop and 33 cheats were
  all green on a task that was quietly too small. `wc -l` over `tasks/*/environment/app_src/**.py`
  is one command and it is the check. The repair was structure the rules use - a declaration
  store, a publication order, a hold ledger keyed by name, an event writer, all frozen - plus one
  more graded rule that splits bringing a unit up from keeping it up.
- **A sealed model inside the verifier is readable by the code it grades unless it is locked.**
  The worker puts `/tests` on `sys.path` so it can import the case list and the generator, and
  that also makes `import model` work from a submitted file - the model computes the answer to
  every graded program. `tests/seal/` with `chmod 700` before the privilege drop closes it, and
  the probe that reaches for it now reports `PermissionError` instead of only a zero. Two kit
  tools had to be taught the new location, which is the same "two tools disagree" shape as the
  `readingcheck` fix.
- **Two runs of a fixed-path harness are one run with the rows interleaved.** `host_trial.py`
  writes `/app`, `/tests`, `/work` and `/logs`; a second copy started beside it produced a cheat
  row carrying the shipped host's trace and cost twenty minutes chasing a bug that was not there.
  It takes a lock now. The same applies to any authoring script that writes absolute paths.
- **A relative path handed to a harness that chdirs is a silent no-op.** `--cheat tasks/.../x.sh`
  ran `bash` with cwd `/app`, where that path does not exist, and the exit status was ignored, so
  the cheat looked like a clean run that scored 0 for its own reasons. Resolve paths, and check
  the status of anything you shell out to.
- **`tests/pristine/` is a copy, and copies go stale.** Rebuilding the environment without
  re-syncing it made the oracle fail with an ImportError inside the worker, which reads like a
  broken task rather than a stale mirror. The sync script has a `--check` mode; run it after any
  change to `environment/`.
- **A forgery probe has to key on the program, not on the process.** The first answer-key cheat
  kept its op buffer in a module global, so it reproduced the first program and drifted on every
  one after it. It scored 0 either way, which is the trap: the layer report claimed the nonce
  population caught it when in truth it had stopped working after the first case. Assert what the
  probe was supposed to reproduce, not only what it scored.

## Lessons, measured (2026-09-09, `publish-settle-order` easiness recovery)

The easiness probe solved the task 2 of 3. All three agents formed the complete plan before
running a program, because every rule was individually implementable and the structure each rule
wants is the standard one; trial 2 wrote a brute-force model from the brief and fuzzed 1,900
programs against it. The repair is one rule whose consequences invalidate six structures at once -
a unit brought up by a call is published *ahead* of its caller, as a dependency would be - and
the lessons below are from building it.

- **A trajectory file that opens with the brief makes `leakcheck` grade the brief against
  itself.** The three probe transcripts arrived with the instruction pasted at the top. Stripped,
  the check found one shared rule sentence in one trial and nothing in the other two, which is the
  evidence that the plan came from the rules being stated rather than from quoted prose. The
  transcripts carry no verdicts either: which trial failed cannot be read from them, and STATE.md
  says so rather than guessing.
- **`open('w')` truncates before it validates.** Writing `newline="\\n"` through a quoted heredoc
  put a literal backslash-n into Python, `io.open` raised on the argument, and `cases.py` was
  already zero bytes. The next command then failed with "module has no attribute ORDER", which
  reads like an import-path problem and is not. Escapes go through a script file, once, and a
  file that a failed write may have touched is checked with `wc` before anything imports it.
- **A cheat emitted before the reading was repaired tests the unrepaired reading.** `emit.py`
  ran, then `make_readings.py` was fixed for a reading whose candidate check ran before it swapped
  the in-progress set, then `readings.py` said "caught by auto-busy" from the fresh directory while
  `cheat_report.py` said "NOT CAUGHT, nothing failed" from the stale script. Two tools disagreeing
  is the signal; the rule is that `emit.py` runs after every `make_readings.py`, never before.
- **A reading that moves 0.7% of the population is a reading the population is not shaped for.**
  The serial-as-order-key reading needs a competitor that came up *before* the load and stands
  *after* the caller, which only a publisher opened privately and promoted afterwards can be. The
  first shaping put the competitor up after the load, where a serial and a position agree, and the
  number stayed at 0.7%. Shaped correctly it moved 9.7%. Write the wrong reading down, derive the
  program shape that separates it, then generate that shape; do not generate and hope.
- **A committed harness value can disagree with every number in the prose.** `test.sh` ran
  `PER=60` while the brief, the metadata and the timings all said 45 (366 programs, three of each
  large size). It had passed reference verification on the platform, so nothing local or remote
  flagged it. Every count in shipped prose is now re-derived from `gen.programs` after any change
  to the generator or the harness, and the harness value is the one the prose is derived from.
- **`build_gt.py` proves additivity, and only if it reads the old file first.** Thirty-six frozen
  answers held byte-for-byte through a new op, a linked order with insertion, a new retention
  edge and a changed scope model; the one contract change that did move an answer nowhere -
  a promoted unit going on reading its own scope - is recorded as a contract change all the same,
  because no frozen program exercised the corner and that is why it had gone unnoticed.

## Lessons, measured (2026-09-09, `publish-settle-order` difficulty rebuild)

The quality review failed `difficult` on the first submission: "the editable code is roughly 100
lines of Python across five files, and each fix is a few lines. The two inventions the author
highlights (a per-instance mark to defeat record reuse, and a per-name list kept in publication
order) are standard techniques (ABA/generation tagging, a dict of lists)."

- **A rubric that names the technique your difficulty rests on has already told you the repair.**
  Both names were accurate, and that is the finding: a task whose hard parts are two retrievable
  techniques is a task whose plan is retrieved. The repair is not more rules. It is making the
  fast path a derivation rather than a lookup - here, a resolution that depends on the caller as
  well as the order, so the answer is the earlier of two heads because each is a subsequence of
  one order, and a teardown whose specified event order forbids the obvious worklist.
  `tools/onelinecheck.py` measures exactly this and measured the repair: before, `run_target` had
  the exact rule `= first_publisher_pos`; after, none of the three graded quantities has a rule
  at depth two.
- **"Roughly a hundred lines across five files" is a measurement, and it was the one I never
  made.** I had measured the *environment* against the retained band and rebuilt it for being
  small; I never measured the graded patch, which is the number the rubric reads. 179 lines of
  reference before, 312 after, five editable files before, six after. Measure both.
- **An additive contract change is provable, and the proof is worth building first.** Scopes were
  added without changing any existing rule, so every one of the 27 already-frozen answers had to
  come out byte-identical afterwards. `build_gt.py` checks that on every run. Without it, a
  rebuild of this size means re-deriving thirty-odd traces by hand and hoping.
- **Two of the three intended scaling boundaries did not bite when measured.** A per-name list
  filtered by visibility came out at 1.5 s and a rescanning teardown at 11.5 s, both inside the
  limit, because the noise publishers were visible to the callers and the forest was too small.
  The shapes had to change, not the claims. The metadata I had already drafted would have stated
  two boundaries that did not exist - write the number after measuring it, never before.

## Lessons, measured (2026-09-09, the difficulty checker)

- **The passing shape was already written down; nobody had scored against it.** The ten intake
  questions in `docs/PASSING-TASK-RESEARCH.md`, the prongs, the leak audit and the size band were
  all on file, and three tasks still went to the quality review without a second discovery, with
  rules that could be confirmed one at a time, or with a 37-line reference. `tools/difficultycheck.py`
  scores a design record (`authoring/<slug>/difficulty.toml`) on exactly those parts, before any
  code. Transcribed from their own state files, the six passed bundles score 95 to 100 and the four
  documented rejected designs score 40 to 59, a 36-point gap that no axis alone explains: the
  rejections lose on `patch` where a pass has `replan`, on no interacting pair, on per-decision
  feedback and on a small reference, together.
- **A calibration with only positives measures agreement with the author.** The first six records
  all scored 95 or better, which says the rubric fits the passing set and nothing else. The
  rejected versions of four of the same tasks are on file in `STATE.md` and `CLAUDE.md`, so they
  are records too, under `authoring/controls/`, and `--calibrate` fails if any of them reaches the
  floor. A rubric change is validated in both directions or not at all.
- **The record measures articulation, not truth.** It reads fields, lengths and counts. That is
  why it lives beside `STATE.md` rather than replacing it, why the prompt says the record is never
  tuned to the score, and why the built tree is re-measured at Stage 7: a design that scored in
  the band on paper and shrank during the build falls out of it there, with the axis named.

## Lessons, measured (2026-09-10, `claim-raise-cut`)

- **The differential against an independently written model found two defects in the reference
  that no hand case reached, and both were set-iteration-order bugs.** Popping and rebuilding the
  cached wait relation in one interleaved pass over a *set* of dirty items let a later item delete
  edges an earlier one had just added; clearing the cycle-search roots before the cut rather than
  after it left a second ring with no root to be found from. Each showed up as exactly one
  mismatch in a few hundred programs, each was invisible to two dozen hand cases, and both are now
  enumerated (`cut-again`, `ring-pair`). Where the structure is a set, "it worked" is a statement
  about this process's hash seed and nothing more.
- **A wrong reading that separates only on iteration order cannot be reported as caught.**
  `cut-one-ring` - compare inside the first ring found rather than across all of them - differs
  from the reference only when the traversal reaches the wrong ring first. Measured: caught by
  `cut-again` in one process and by no enumerated case in the next, same code both times. It is
  recorded with that caveat and backed by the 8.5% of the generated population it moves, rather
  than claimed as pinned by a case.
- **A variant that patches cleanly can still change nothing.** The first `cut-one-ring` patch
  returned early from the SCC helper, whose caller looped over every root anyway, so the file was
  byte-different and the behaviour identical and the reading reported 0.0% moved. The rule from
  `reach-pair-sweep` was that a rename must assert it fired; the rule this adds is that a
  behavioural patch must assert the behaviour moved, because a patch that fires and changes
  nothing reads exactly like a reading nothing separates.
- **Three of four scaling boundaries bit, and the fourth taught the most.** Restricting the
  removal question to the item's own participants was meant to be the fast path; it measures 181 s
  against a 60 s limit, because one raise stuck across a crowd of holders excludes the whole crowd.
  The fast path needs the grouping - holders carrying the same mark with no request of their own
  answer alike - and a variant that groups but then does per-member work proportional to the queue
  measures 83 s. Two asymptotics hide in one loop and only the clock separated them.
- **An `apt` layer that installs nothing the verifier uses costs the container gates.** `procps`
  and `util-linux` were carried over from the house pattern; `setpriv`, `setsid` and `timeout` are
  already in `python:3.11-slim`, and the reap reads `/proc` instead of calling `pkill`. Dropping
  the layer removed the only part of the build that needed a Debian mirror, which is what let the
  oracle, the nop, the variants and the probes run in a sandbox with no apt egress. Check the base
  image before copying an install line.
- **A cheat script written against `/app` is a silent no-op in a harness that stages the tree
  elsewhere.** The host trial ran the scripts with cwd set to a temporary copy while the scripts
  wrote absolute `/app` paths, `set -euo pipefail` made them exit non-zero, the harness ignored the
  status, and four cheats came back "caught by the limit" - because what was actually graded was
  the shipped tree. Stage the path the scripts expect, and fail the run on a non-zero status from
  anything you shell out to.
- **`open('w')` truncates before it validates, again.** `newline="\\n"` written through a shell
  heredoc put a literal backslash-n into the Python source, `io.open` raised on the argument, and
  the target file was already zero bytes. Same shape as the 2026-09-09 entry, one session later,
  because the rule was read and not applied: escapes go through a script file, once.
