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

Two findings the models caught in the reference itself: an occurrence cache that froze the
first index it found missed a longer stop completing later but starting earlier, and a
backward character scan disagreed with a forward one on a malformed lead byte. Both were
invisible to 1200 random requests until a stop pool containing the shape was added.

## batch-admit-reclaim: what the build measured (2026-09-06)

Seven findings, each with the number that produced it. Nothing here was a pipeline
rejection; all of it came from gates run locally before packaging.

**A brief that describes the machine is a recipe, and the self-probe caught it.** The
first draft explained the step order, block identity, the merge and the difference
between releasing a block and giving it up. Graded through the real verifier, the plan
recorded before any code existed - count the blocks the newcomer is missing against the
free space - scored 0 on 189 of 300 generated traces. The same plan with the count
replaced by playing the step out on a copy of the pool scored 1 **on the first write**.
That is the mode C signature, and the cause was the brief: the play-out was a
transcription of the brief's own description. The repair was to cut the machine out of the
instruction and leave it in the frozen tree the agent has to read, so the brief carries
only what the four editable files must achieve, both fences, the input space and the
output shape. Recorded honestly: the post-cut brief has not been probed by anyone who does
not already know the answer.

**An engine that faults under a wrong policy is a confirmation signal.** The first build
raised on a failed allocation. Under one misreading, 16 of 120 traces tore - which tells a
solver its policy is wrong without telling it anything about the answer, and closes one
direction of the fence for free. Adding a preempt-on-demand valve to the allocation path
took that to 0 of 150 under every reading. **A machine that stays total under every
reading is what makes "no oracle" true.**

**Deciding before and applying after is what makes a question forward-looking.** Entries
were originally applied before the decodes, which let a wrong policy livelock: admit, put
out to make room, admit again, with nothing ever decoding. Deciding entries at the top of
the step and applying them after the decodes guarantees progress and is the whole reason
the entry question cannot be answered against the pool in front of you.

**Check whether the machine's own cost bounds the naive path before designing a speed
regime.** The obvious C3 here was to make a per-candidate play-out infeasible and hoist
it. It does not exist: head-of-line blocking caps the policy calls per step at one plus
the admissions, so the naive path is already O(steps x pool), which is what the engine
itself costs. Twenty minutes of arithmetic retired the lever, which is the
"ceiling measured from the other end" law applied before building rather than after.

**An attestation probe that swaps in a byte-identical function is a no-op.**
`cheat_report.py` reported two probes as "not caught by its own layer": one replaced
`Log.put` with a function whose body was identical, so the fingerprint did not move, and
one rebound a pool method at import time, before the instrumentation armed. Probes have to
change behaviour or identity, and they have to fire during the run. **A cheat suite that
scores all-zero proves less than a report naming which test caught each one.**

**`tools/docker_trial.py --dir` resolves a relative path against the task directory.**
Five correct variants came back reward 0, and the cause was that the path pointed at
nothing, `from_dir` wrote no files, and the shipped tree was graded. The reference itself
reproduces it. Pass absolute paths, and treat a variant that fails with the *same* two
tests as `nop` as a harness problem before believing it is a verifier problem.

**`tools/forgecheck.py` matches whitespace-split runs of `json.dumps(gt, sort_keys=True)`.**
An answer-key cheat that re-keys the table by input signature, or dumps it with compact
separators, carries no matching run and reports FAIL on a probe that is real. Embed
gt.json's own dump and index into it.

Measured, for calibration: 13 misreadings move 7.5% to 97% of generated traces, all above
the one-tenth line after the generator was tuned twice; the shipped tree agrees with the
reference on 3 of 150; reference and sealed model agree on 29 enumerated and 400 generated
traces, and on 720 traces drawn from 12 random nonces; five behaviour-preserving
permutations of the reference give byte-identical timelines on 150 traces, which is the
uniqueness evidence a run audit would want; 24 of 24 two-image trials behaved (oracle 1,
nop 0, 22 cheats 0) and 5 of 5 variants scored 1.
