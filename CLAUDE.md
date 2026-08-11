# Building a Frontier Bench task in this repo

This file is the operating manual for a fresh session with no memory of the earlier ones.
Two tasks in `tasks/` have been through the real pipeline. `rollout-cache-coherence` cleared
the difficulty band and its instruction passed the AI-text screen; getting there took three
instruction rewrites and a lot of avoidable rework. Everything below exists so the next task
does it in one pass.

Read `docs/RULES.md`, `docs/DIFFICULTY.md`, `docs/VERIFIER-ISOLATION.md` and
`docs/QUALITY-REVIEW.md` before doing anything. They are the transcribed guideline and they
are authoritative. This file is the *practice* on top of them: what actually worked here,
with numbers.

## First moves in a new session

1. Read the four `docs/` files, then this one.
2. Read `tasks/rollout-cache-coherence/STATE.md` end to end. It is the worked example: the
   difficulty argument, the frozen verifier contract, the expert path, the failure signature
   of every cheat.
3. Read `tasks/rollout-cache-coherence/instruction.md` and the reaction one. Those two are the
   only briefs known to have passed the AI-text screen, and they are the style reference.
4. Pick a seed and attack your own first plan before writing any code. That step is the whole
   game; everything after it is execution.
5. Start `dockerd` by hand and pull the base image from the mirror before you need it. It
   takes minutes and it fails in ways that waste an hour if you leave it to the end.

Aim the next task one notch harder than `rollout-cache-coherence`, which cleared the band.
The section at the bottom says how, and what not to do instead.

## Layout

```
tasks/<slug>/            the bundle that ships (packaged to tasks/<slug>.zip)
  instruction.md         the brief; the AI-text screen reads this
  task.toml              metadata, resources, artifact declaration
  environment/app_src/   the tree the agent lands in
  solution/ref/*.py      the reference implementation, well commented
  solution/solve.sh      generated from solution/ref by authoring/emit.py
  tests/                 sealed verifier: scenarios, oracle, ground truth, pristine copy
  cheat/                 deliberate fake solutions, every one scores 0
  authoring/             generators; never hand-edit what they emit
  STATE.md               working notes, excluded from the zip
tools/                   trial emulation and the instruction checker
scripts/                 preflight.py and package.py from the kit, unmodified
```

## The method in one paragraph

Take a real, hard bug class from a public tracker as the **seed only**. Do not vendor the
repo. Write a small self-contained simulator that has the same organs and the same failure
mode, in integer arithmetic so every check is exact. Excise the decision that carries the
bug and ship the tree with the degenerate version in place. Grade three things at once:
outputs, *the exact amount of work done*, and lifecycle events. The work accounting is what
makes it hard, because the plan a frontier agent forms first produces correct outputs and
the wrong amount of work, and nothing in the agent's environment lets it check that.

## The difficulty pattern that cleared the band

Copy the shape, not the subject.

**One question that is really two, with different answers.** In `rollout-cache-coherence` a
weight push invalidates a sample in flight (every parameter reaches the logits) but does not
necessarily invalidate a cached KV block (a block depends only on parameters upstream of the
last key/value projection). One fingerprint through the engine is wrong on one side or the
other. Both sides are graded. The agent must derive the distinction from a forward pass in a
file it cannot edit.

Four properties made it work, and a new task needs all four:

1. **The retrieved answer is specifically wrong.** The nearest public issue's accepted fix
   (adapter identity in the cache key) fails here. Searching harder makes the plan worse.
   Write that transplant as a cheat and confirm it scores 0.
2. **A resource gate the safe answer fails.** Counters for real work, incremented in files
   the agent may not edit, compared exactly. "Invalidate everything on every change" is
   correct and fails. This is the single highest-value element of the design.
3. **Fenced from both sides.** For every case that must fail, ship a case that must still
   work: a replayed push that changes nothing, an offload level that preserves the cache,
   two adapters that must keep sharing. Overcaution has to fail too.
4. **No oracle for the thing being graded.** The agent can check its tokens against a cold
   engine it builds itself. It cannot check its counters against anything. A wrong plan
   stays invisible until the verifier.

Plus small simultaneous contracts so a nearly-right implementation still fails: a
cross-layer parameter tie that makes an apparently harmless target harmful, a queue
discipline, a preemption path, an eviction path.

## Stage recipe

### 1. Idea

Pick a seed issue from a real tracker. `mcp__github__search_issues` works when the GitHub
MCP server is connected; `issue_read` is blocked for repos outside this session, so read the
issue body with `WebFetch` on its URL. Look for RFCs that enumerate failure categories,
because they hand you a menu of coupled sub-bugs. Then:

- Write the simulator yourself. Vendoring a public repo means the diff is public and the
  real fix is public with it.
- **Different failure mode from every task already in `tasks/`.** Reskinning is rejected.
  Cache coherence under weight updates is used. Do not do it again.
- Self-attack before writing code: state your first plan. If your first plan is correct,
  the design has already failed. Iterate the design until the honest answer is "I can see
  where to start but my first plan would probably be wrong somewhere that matters."
- Design for **1 solve of 8**. The realized rate drifts up.

### 2. Verifier contract, frozen before any environment code

Decide the artifact list, what is checked, and where ground truth comes from. Write it into
`STATE.md`. Do not touch it afterwards to make a run pass.

### 3. Environment

- Integer arithmetic, CPU only, `gpus = 0`. Determinism is what lets you assert exact
  equality on outputs *and* counters. Floats would force tolerances and tolerances leak.
- Keep it small enough to run in seconds. Eleven scenarios run in under two seconds here.
- **No comments, no docstrings, no `.md` files anywhere under `environment/`.** Preflight
  errors on prose comments. Degrade identifiers to ordinary internal register (`pfx`, `blk`,
  `pstore`), never to noise, never to a name that lies.
- Put the counters that bind the grade in files the agent may **not** edit. Here
  `runtime/eng.py` counts computed and reused positions and `model/be.py` counts forward
  passes. That is what makes the accounting implementation-independent.
- Ship a runner (`run_rollout.py`) that takes a scenario file so the agent can experiment.
  Fair, and it does not hand over the answer.
- Add `.dockerignore` with `__pycache__` and `*.pyc`. Bytecode from local test runs
  otherwise lands in the built image; check the image, not the source tree:
  `docker run --rm <img> sh -c 'find /app -type f'`.

### 4. Reference solution

`solution/ref/*.py` holds the corrected files, fully commented (the agent never sees them).
`authoring/emit.py` generates `solution/solve.sh` from them as heredocs. If the reference is
doing heavy computation the difficulty is on the wrong side; here it is ~120 lines and runs
in under a second.

### 5. Instruction - the part that failed three times

The screen is a classifier. It reacts to **uniform cadence and editorial smoothing**, not to
word choice alone. The first rewrite here matched the passing sample's *average* sentence
length and was rejected again, because regularising toward the mean is exactly the signal.

Measure, do not guess:

```
python3 tools/textcheck.py tasks/reaction-network-reconstruction/instruction.md <draft>
python3 tools/textcheck.py tasks/rollout-cache-coherence/instruction.md <draft>
```

Both of those passed the screen. A draft ships only when both runs report no findings. Run
the two references against each other once and you will see the reaction brief trip a single
stock-vocabulary hit against the rollout brief; the rollout brief is the stricter reference on
that axis, and a new draft carrying zero stock words clears both.

Targets from the two passing briefs:

| axis | reaction | rollout | aim for |
|---|---|---|---|
| burstiness (sd/mean of sentence length) | 0.938 | 0.926 | >= 0.90 |
| short sentences (<10 words) | 25% | 32% | >= 25% |
| long sentences (>30 words) | 18% | 20% | ~20% |
| sentence range | 5-140 words | 3-94 | wide |
| paragraph length sd | 38.5 | 37.5 | >= 35 |
| stock words / hedges / antithesis / triads | 1/0/0/0 | 0/0/0/0 | 0 |
| dash asides, first person singular | 0, 0 | 0, 0 | 0 |

How to hit those honestly, since **faking human artifacts is banned** (no deliberate typos,
no staged informality, no contrived quirks - `AGENTS.md` D1, and detectors are trained
against exactly that):

- Verdicts get short sentences. "Ours is neither." "Throw those tokens away." "None of them
  care." "Both halves are measured."
- Specifications get long chained ones. The file-boundary paragraph and the rewind rule run
  60-90 words each, clauses joined with commas and a semicolon.
- Team voice, "we" and "our", never "I". Address the reader as "you".
- Ban the antithesis reflex outright: no "X is not Y, it is Z", no "not just A but B", no
  punchy closer at the end of a paragraph. This is the strongest model tell and the checker
  counts it.
- Concrete numbers from the real environment. Quote actual token streams from a real run.
- One-line paragraph as a section pivot: "Some ground rules, because several of them are not
  what you would do elsewhere."

Content rules that are separate from style, and blocking on their own:

- Every behaviour the verifier checks must be stated. Every stated behaviour must be checked.
  Walk the assertion list against the brief line by line before packaging.
- State the must-still-work side explicitly, or an overcautious solution fails on a criterion
  it was never told about.
- State anything the grade depends on that is not derivable, such as queue discipline after a
  rewind. Getting this wrong makes a semantically correct solution fail, which the quality
  review reads as an artificial handicap.
- Never name the method, the algorithm, or which files to read first. Symptom, goal, rules.
- Do not name the wrong default plan either. "Both halves are measured" carries the
  requirement without telling the agent which plan to abandon.
- Plain ASCII. Absolute paths. Blank line, then the exact suffix with N equal to
  `[agent] timeout_sec`.

### 6. Cheats

Two families, both mandatory, all scoring 0.

**Single-mistake variants**: the *whole* reference solution with exactly one decision made
the way a solver who missed one piece would make it. Generate them in `authoring/emit.py`
from the reference sources by string-swapping an anchored block; never hand-write them.
A variant that omits the other corrected files silently tests the shipped bug instead of the
mistake you meant to test - that error cost a debugging cycle here.

Aim for a spread of failure signatures and record them with
`python3 tasks/<slug>/authoring/cheat_report.py`. The most valuable cheats are the ones that
produce **every output correctly** and fail only on work accounting. Four of the nine here do.

**Isolation probes** (required whenever the verifier executes agent code): background reward
rewrite, planted run output, garbage report, privilege probe, ground-truth read. Build these
on the **shipped, broken tree**, not on the reference. A probe built on the reference does the
real work and scores 1 legitimately, which proves nothing.

Plus a sweep cheat that hunts the agent image for answer material and finds nothing.

### 7. Gates

```
python3 tasks/<slug>/authoring/sync.py          refresh tests/pristine from environment/app_src
python3 tasks/<slug>/authoring/build_gt.py      regenerate ground truth, proving it
python3 tasks/<slug>/authoring/emit.py          regenerate solve.sh and the cheats
python3 tools/run_local_rollout.py --all        host emulation of every trial
python3 tools/docker_trial.py --all             the same trials on the real two images
python3 tools/textcheck.py <passed.md> <draft>  instruction cadence
python3 scripts/preflight.py tasks/<slug>
python3 scripts/package.py tasks/<slug>
```

`build_gt.py` must refuse to write a ground truth it cannot prove independently. Here every
expected token stream has to be reproducible from scratch, under one parameter snapshot, by
a sealed generator that shares no code with the engine.

## Verifier architecture that passed

The overlay pattern, for any task where the solution is code inside the repo:

- `artifacts` lists **only the editable paths**. Declare a wider candidate set than strictly
  needs changing, so the boundary does not hand over the diagnosis. One of the four files
  here needed no change at all.
- `tests/Dockerfile` bakes a pristine copy of the whole tree (`COPY . /tests/` then move it
  to `/pristine`). `test.sh` copies it to a work dir and overlays the agent's declared files.
  Edits outside the declared set are structurally impossible.
- Ground truth in `tests/gt.json`, `chmod 600`, root-owned.
- Grade on three axes, all-or-nothing: outputs, exact work counters, lifecycle events.
- Re-prove ground truth at verification time with a sealed independent implementation.

Isolation, since the verifier imports agent code (`docs/VERIFIER-ISOLATION.md`):

```
chmod 700 /logs/verifier; echo 0 > reward.txt      # lock and default-deny first
setsid --wait env ... setpriv --reuid=1002 ... timeout --signal=KILL 600 python /tests/runner.py
python /tests/reap.py 1002                          # kill double-forked survivors
pytest ... && echo 1 > reward.txt || echo 0 > reward.txt
```

The run writes to a sandbox-writable work file. pytest runs afterwards as root, reads that
file defensively as hostile input, and never executes agent code. Confirm it: the privilege
probe should report `uid=1002` and `PermissionError` on the reward channel, the ground truth,
the pristine tree and the tests.

## Traps that cost time here

- `setsid` without `--wait` can fork, so `wait` returns immediately and grading starts before
  the run finishes. Use `setsid --wait`.
- `pkill` is not in `python:3.12-slim`, and apt is unreachable in this sandbox. `tests/reap.py`
  walks `/proc` instead. `setpriv`, `setsid`, `timeout`, `useradd` are all already present.
- Comparing a restart *trace* in order over-constrains a correct solution. Compare
  engine-generated events in order and agent-generated events as a set, and state the queue
  discipline in the instruction so counters stay well defined.
- A cached-block index and a page pool must be reconciled through code the agent cannot edit,
  or the answer becomes "invent the reconciliation", which is a different and worse task.
- Docker Hub returns 429 in this sandbox. Pull `mirror.gcr.io/library/python:3.12-slim` and
  `docker tag` it as `python:3.12-slim`. `dockerd` may need starting by hand.
- Builds inside docker do not trust the sandbox's egress CA, so pip fails. `tools/docker_trial.py`
  injects `/root/.ccr/ca-bundle.crt` into a temporary copy of the build context. The shipped
  Dockerfiles stay unchanged; this is local only.
- `harbor` is not installed here. `tools/docker_trial.py` reproduces the two-container trial
  with docker directly. Say plainly in the handover that `harbor check` was not run.

## Making the next one harder

The last task landed inside the band with the design aimed at 1-of-8. To go a notch harder,
add **one more axis of discovery that the instruction cannot state without giving it away** -
do not just add more stated rules, which is grinding rather than difficulty.

Two that were designed for this task and not built:

- **A second holder of the same cached state**, such as an offload tier that also caches and
  must be retired in step with the primary index. An agent that fixes one side gets every
  output right and the wrong counters. The instruction can state the requirement ("nothing
  computed before that point may be served after it") without hinting that two holders exist.
- **State that must be reconstructed rather than recomputed** across a lifecycle event, such
  as calibration scales restored from a host copy instead of reset to a default. It changes
  outputs after the cycle, and the requirement is stateable while the mechanism is not.

Guardrails when hardening: the reference solution must still pass every run by a path you can
describe step by step, and the expert time estimate must stay honest. A design whose expert
path is uncertain is rejected exactly like a trivial one, and zero solves of eight is a
rejection, not a triumph.

## Definition of done

- `preflight.py` clean, no warnings.
- `docker_trial.py --all`: oracle 1, nop 0, every cheat 0, including all five isolation probes.
- `textcheck.py` clean against **both** passing instructions.
- Instruction-to-verifier coverage walked line by line, both directions.
- Built agent image inspected file by file for leaks.
- `STATE.md` current: verifier contract, the difficulty argument, the expert path, estimated
  solves, and every gate you did not run.
- Handover states honestly what was run and what was not. Packaging proves nothing.
