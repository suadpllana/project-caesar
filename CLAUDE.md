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
