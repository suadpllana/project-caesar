# Building a Frontier Bench task in this repo

Operating manual for a session with no memory of the earlier ones. Two tasks here have been
through the real pipeline and both cleared the difficulty and easiness probes; the third is
built and gated locally but has not been through the pipeline yet:

| task | category | cheats | assertions | agent budget | expert estimate |
|---|---|---|---|---|---|
| `reaction-network-reconstruction` | Science / Chemistry | 12 | 86 | 10800 s | 8 h |
| `rollout-cache-coherence` | ML / Training | 17 | 66 | 14400 s | 8 h |
| `checkpoint-resume-drift` | ML / Training | 18 | 86 | 14400 s | 8 h |
| `turn-seam-alignment` | ML / Training | 25 | 87 | 14400 s | 7 h |

`turn-seam-alignment` is the fourth, and it is the one that came back from the probes:
easiness 0 of 3 and **difficulty 0 of 8**, which is a rejection. Its post mortem is in its
own `STATE.md` and the short version is in "Grade the work, never the implementation
choice" below - it graded a character count against one number when the honest answer was
a range, so a solver who read the merge table more finely than the reference did scored 0.
It has been recalibrated and not re-probed. Its verifier has since been hardened twice
against adversarial probes that scored 1 without doing the work; the second of those is
written up under "Collect the evidence outside the process you are measuring" below.

Between them the first two were rejected three times by the AI-text screen and once by the
run audit. Every one of those rejections is written down below with the fix, because the
next task should hit none of them.

`checkpoint-resume-drift` is the first one built with the run-audit lesson applied from the
start rather than retrofitted: the graded set was sorted into real work and implementation
choice before the contract froze, `authoring/variants/` existed before the cheats did, and
one counter (`draws`) was dropped during design because only a legitimate alternative
implementation separated it. Its tooling is the reusable version of the earlier task's:
`tools/docker_trial2.py <slug>` takes a slug and reads the artifact list out of `task.toml`,
so it works for any task in `tasks/`, and it has a `--variants` mode that runs every
alternative correct implementation through the real verifier.

`docs/RULES.md`, `docs/DIFFICULTY.md`, `docs/VERIFIER-ISOLATION.md` and
`docs/QUALITY-REVIEW.md` are the transcribed guideline and are authoritative. This file is
the practice on top of them: what actually worked, with numbers.

## First moves in a new session

1. Read the four `docs/` files, then this one.
2. Read `tasks/rollout-cache-coherence/STATE.md` end to end. It is the worked example: the
   difficulty argument, the frozen verifier contract, the expert path, the failure signature
   of every cheat, and the run-audit post mortem.
3. Read both `instruction.md` files. They are the only two briefs known to have passed the
   AI-text screen and they are the style reference for the new one. The third,
   `tasks/checkpoint-resume-drift/instruction.md`, clears `tools/textcheck.py` against both
   of them but has not faced the screen.
4. Start `dockerd` and pull the base image from the mirror now (see Sandbox notes). It takes
   minutes and it fails in ways that waste an hour if left to the end.
5. Pick a seed, then attack your own first plan before writing any code. That step is the
   whole game; everything after it is execution.

Aim one notch harder than `rollout-cache-coherence`. The last section says how, and what
not to do instead.

## What the pipeline rejects, in the order it bites

| gate | what it kills | what saved us |
|---|---|---|
| `preflight.py` | mechanical rules | run it after every edit, not at the end |
| AI-text screen | the instruction | `tools/textcheck.py` against both passing briefs |
| similarity screen | reskins of earlier work | a genuinely different failure mode |
| quality review | unfair specs, thin tests, bad tags | `docs/QUALITY-REVIEW.md` walked criterion by criterion |
| anti-cheat probe | weak verifiers | the `cheat/` suite, all scoring 0 |
| difficulty probe (8 agents) | solved 0 or 7+ times | design for 1 of 8 |
| easiness probe (3 agents) | solved 2 or 3 of 3 | same design target |
| **run audit** | grading implementation choices | `variants/` + `field_report.py` |

The run audit is the one nobody expects. It reads the probe trajectories and judges whether
the task was fair, not whether the tests passed. See its own section below.

## Layout

```
tasks/<slug>/            the bundle that ships (packaged to tasks/<slug>.zip)
  instruction.md         the brief; the AI-text screen reads this
  task.toml              metadata, resources, artifact declaration
  environment/
    Dockerfile           FROM python:3.12-slim; COPY app_src/ /app/; WORKDIR /app
    .dockerignore        __pycache__ and *.pyc, or bytecode lands in the image
    app_src/             the tree the agent lands in (16 files in the ML task)
  solution/
    ref/*.py             the corrected files, fully commented, agent never sees them
    solve.sh             generated from ref/ by authoring/emit.py
  tests/
    Dockerfile           bakes tests, oracle, scenarios, ground truth, pristine tree
    test.sh              hardened entry point
    runner.py            the only place agent code executes
    test_outputs.py      the grader; pytest, root, never runs agent code
    oracle.py            sealed independent implementation that re-proves ground truth
    scen.py              the scenario set
    gt.json              ground truth, chmod 600
    reap.py              kills survivors of the sandboxed run
    pristine/            byte-identical copy of environment/app_src
  cheat/                 deliberate fake solutions, every one scores 0
  authoring/             generators and audits; never hand-edit what they emit
  STATE.md               working notes, excluded from the zip
tools/                   trial emulation, instruction checker
scripts/                 preflight.py and package.py from the kit, unmodified
```

## The method in one paragraph

Take a real, hard bug class from a public tracker as the **seed only**. Do not vendor the
repo. Write a small self-contained simulator with the same organs and the same failure mode,
in integer arithmetic so every check is exact. Excise the decision that carries the bug and
ship the tree with the degenerate version in place. Grade outputs, the exact amount of real
work done, and lifecycle events. The work accounting is what makes it hard: the plan a
frontier agent forms first produces correct outputs and the wrong amount of work, and
nothing in the agent's environment lets it check that.

## The difficulty pattern that cleared both probes

Copy the shape, not the subject.

**One question that is really two, with different answers.** In `rollout-cache-coherence` a
weight push invalidates a sample in flight (every parameter reaches the logits) but does not
necessarily invalidate a cached KV block (a block depends only on parameters upstream of the
last key/value projection). One fingerprint through the engine is wrong on one side or the
other. Both sides are graded. The distinction has to be derived from a forward pass in a file
the agent cannot edit.

Four properties made it work, and a new task needs all four:

1. **The retrieved answer is specifically wrong.** The nearest public issue's accepted fix
   (adapter identity in the cache key) fails here. Searching harder makes the plan worse.
   Write that transplant as a cheat and confirm it scores 0.
2. **A resource gate the safe answer fails.** Counters for real work, incremented in files
   the agent may not edit, compared exactly. "Invalidate everything on every change" is
   correct and fails. Highest-value element of the whole design.
3. **Fenced from both sides.** For every case that must fail, ship one that must still work:
   a replayed push that changes nothing, an offload level that preserves the cache, two
   adapters that must keep sharing. Overcaution has to fail too.
4. **No oracle for the graded quantity.** The agent can check its tokens against a cold
   engine it builds itself. It cannot check its counters against anything.

Plus small simultaneous contracts so a nearly-right implementation still fails: a cross-layer
parameter tie that makes an apparently harmless target harmful, a queue discipline, a
preemption path, an eviction path.

## Grade the work, never the implementation choice

`rollout-cache-coherence` cleared both probes and then failed the run audit for reward
hacking. Nothing was hacked. The verifier graded a number two correct implementations
disagree on, so an agent that had solved the problem could only close the gap by tuning an
internal detail against a hidden constant, and the audit called it what it looked like.

The exact failure, worth memorising:

- A graded counter recorded when the prefix index happened to drop a stale entry. A
  submission that retired entries at the push instead of at the sweep got every token, every
  rewind, every trace and every real-work counter right and lost 2 of 57 assertions.
- Worse, the memory-pressure scenario's work counters encoded the reference's eviction
  tie-break. The same policy backed by an `OrderedDict` instead of a tick counter gives
  computed 265 against 225 and preempt 12 against 9, on identical semantics and identical
  tokens.

Before freezing the contract, sort every graded quantity into one of two piles.

**Real work, safe to grade.** Positions computed, positions reused, tokens emitted, lifecycle
events the engine itself raises. Two correct implementations agree on these by construction.
If they can disagree, it is not real work.

**Implementation choice, never grade.** When bookkeeping is retired, which of several equally
old entries a sweep picks, the order of internally generated events, anything whose value
shifts when a dict becomes an OrderedDict.

Two mechanical guards, both cheap, both in `tasks/rollout-cache-coherence/authoring/`:

- `field_report.py` prints, per cheat, which graded field diverges. A field that separates no
  cheat is pure liability: it cannot catch a wrong answer and it can fail a right one.
- `variants/` holds **alternative correct implementations**, and `variant_check.py` runs them
  through the real verifier. Every `ok-*` variant must score 1. Build at least two: same
  semantics with different data structures, and same semantics with different timing of
  internal cleanup. This is the cheat suite's mirror image and it is the gate the run audit
  actually applies.

Where a scenario needs eviction or preemption for coverage, keep it but grade it on the
quantities ordering cannot move (tokens, rewinds), and derive the counter-graded subset from
the ground truth rather than hand listing it, so a scenario that starts evicting drops out of
counter grading by itself. `ORDER_FREE` in `tests/test_outputs.py` is that derivation.

**Grade a range when the answer is a range.** `turn-seam-alignment` failed the difficulty
probe 0 of 8 with a counter that was real work by every test above - characters handed to a
tokenizer the agent cannot edit, and two correct implementations do agree on it. What they
do not agree on is how clever the implementation is allowed to be. "Resume at the last
position the merge table protects" has four correct readings there, nested, 2298 to 2809
characters over the same twelve scenarios, all producing identical tokens. Equality against
the reference's 2631 failed three of the four. The fix is a window: a floor that comes from
the sealed oracle and that nothing legitimate can go under, a ceiling measured from the
weakest reading you intend to accept, and `build_gt.py` refusing to write a ceiling that has
drifted up far enough to admit the answer you do reject. Before grading any optimisation
counter, ask whether a better solution than yours would fail it. If it would, grade the
range and put every reading in `variants/`.

## Stage recipe

### 1. Idea

Pick a seed issue from a real tracker. `mcp__github__search_issues` works when the GitHub MCP
server is connected; `issue_read` is blocked for repos outside the session, so read the issue
body with `WebFetch` on its URL. RFCs that enumerate failure categories are the best seeds
because they hand you a menu of coupled sub-bugs: `vllm-project/vllm#48310` gave six.

- Write the simulator yourself. Vendoring a public repo means the diff is public and the real
  fix is public with it.
- **Different failure mode from every task already in `tasks/`.** Reskinning is rejected.
  Used already: mechanism reconstruction from noisy analytics (chemistry), cache coherence
  under weight updates (ML), state classification across a checkpoint and resume (ML). Do
  not do any of those again.
- Self-attack before any code: state your first plan. If your first plan is correct, the
  design has already failed. Iterate until the honest answer is "I can see where to start but
  my first plan would probably be wrong somewhere that matters."
- Design for **1 solve of 8**. The realized rate drifts up.
- Category and subcategory come from the table in `docs/RULES.md`. Tags name the specific
  techniques, never the taxonomy; repeating the subcategory is a blocking failure.

### 2. Verifier contract, frozen before any environment code

Decide the artifact list, what is checked, which quantities are real work versus
implementation choice, and where ground truth comes from. Write it into `STATE.md`. Do not
touch it afterwards to make a run pass.

### 3. Environment

- Integer arithmetic, CPU only, `gpus = 0`. Determinism is what lets you assert exact
  equality on outputs *and* counters. Floats force tolerances and tolerances leak.
- Small enough to run in seconds. Eleven scenarios run in under two seconds here.
- **No comments, docstrings or `.md` files anywhere under `environment/`.** Preflight errors
  on prose comments. Degrade identifiers to ordinary internal register (`pfx`, `blk`,
  `pstore`, `wq`), never to noise, never to a name that lies.
- Put the counters that bind the grade in files the agent may **not** edit. Here
  `runtime/eng.py` counts computed and reused positions and `model/be.py` counts forward
  passes, which makes the accounting implementation-independent and makes forgery detectable
  by cross-checking the two.
- Ship a runner (`run_rollout.py`) that takes a scenario file so the agent can experiment.
  Fair, and it does not hand over the answer.
- `.dockerignore` with `__pycache__` and `*.pyc`. Check the built image, not the source tree:
  `docker run --rm <img> sh -c 'find /app -type f'`.

### 4. Reference solution

`solution/ref/*.py` holds the corrected files, fully commented. `authoring/emit.py` generates
`solution/solve.sh` from them as heredocs; the script writes source files, it never writes an
answer. If the reference is doing heavy computation the difficulty is on the wrong side: here
it is 322 lines across four files and runs in under a second.

### 5. Instruction, the part that failed three times

The screen is a classifier. It reacts to **uniform cadence and editorial smoothing**, not to
word choice alone. The first rewrite matched the passing sample's *average* sentence length
and was rejected again, because regularising toward the mean is exactly the signal.

Measure, do not guess:

```
python3 tools/textcheck.py tasks/reaction-network-reconstruction/instruction.md <draft>
python3 tools/textcheck.py tasks/rollout-cache-coherence/instruction.md <draft>
```

A draft ships only when both report no findings. Run the two references against each other
once and the reaction brief trips a single stock-vocabulary hit; the rollout brief is the
stricter reference on that axis, and a draft carrying zero stock words clears both.

| axis | reaction | rollout | aim for |
|---|---|---|---|
| burstiness (sd/mean sentence length) | 0.938 | 0.926 | >= 0.90 |
| short sentences (<10 words) | 25% | 32% | >= 25% |
| long sentences (>30 words) | 18% | 20% | ~20% |
| sentence range | 5-140 words | 3-94 | wide |
| paragraph length sd | 38.5 | 37.5 | >= 35 |
| stock words / hedges / antithesis / triads | 1/0/0/0 | 0/0/0/0 | 0 |
| dash asides, first person singular | 0, 0 | 0, 0 | 0 |
| total words | 1103 | 878 | 800-1100 |

How to hit those honestly, since **faking human artifacts is banned** (no deliberate typos,
no staged informality, no contrived quirks: `AGENTS.md` D1, and detectors are trained against
exactly that):

- Verdicts get short sentences. "Ours is neither." "Throw those tokens away." "None of them
  care." "Both halves are measured."
- Specifications get long chained ones. The file-boundary paragraph and the rewind rule run
  60-90 words each, clauses joined with commas and a semicolon.
- Team voice, "we" and "our", never "I". Address the reader as "you".
- Ban the antithesis reflex outright: no "X is not Y, it is Z", no "not just A but B", no
  punchy closer at the end of a paragraph. Strongest model tell, and the checker counts it.
- Concrete numbers from the real environment. Quote actual token streams from a real run.
- One-line paragraph as a section pivot: "Some ground rules, because several of them are not
  what you would do elsewhere."

Content rules, separate from style and blocking on their own:

- Every behaviour the verifier checks must be stated. Every stated behaviour must be checked.
  Walk the assertion list against the brief line by line, both directions, before packaging.
- State the must-still-work side explicitly, or an overcautious solution fails a criterion it
  was never told about.
- State anything the grade depends on that is not derivable, such as queue discipline after a
  rewind.
- Never name the method, the algorithm, or which files to read first. Symptom, goal, rules.
- Do not name the wrong default plan either. "Both halves are measured" carries the
  requirement without telling the agent which plan to abandon.
- Plain ASCII, absolute paths, blank line, then the exact suffix with N equal to
  `[agent] timeout_sec`.

### 6. Cheats

Three families, all scoring 0.

**Single-mistake variants**: the *whole* reference solution with exactly one decision made
the way a solver who missed one piece would make it. Generate them in `authoring/emit.py` by
string-swapping an anchored block in the reference source; never hand-write them. A variant
that omits the other corrected files silently tests the shipped bug instead of the mistake
you meant to test. The most valuable ones produce **every output correctly** and fail only on
work accounting: four of the nine here do.

**Isolation probes**, required whenever the verifier executes agent code: background reward
rewrite, planted run output, garbage report, privilege probe, ground-truth read, forged
counters, verifier-directory sweep. Build these on the **shipped, broken tree**, not on the
reference. A probe built on the reference does the real work and scores 1 legitimately, which
proves nothing. This cost a debugging cycle here.

**A sweep cheat** that hunts the agent image for answer material and finds nothing.

Record the failure signature of each with `authoring/cheat_report.py` (which test) and
`authoring/field_report.py` (which field).

### 7. Gates

```
python3 tasks/<slug>/authoring/sync.py          refresh tests/pristine from environment/app_src
python3 tasks/<slug>/authoring/build_gt.py      regenerate ground truth, proving it
python3 tasks/<slug>/authoring/emit.py          regenerate solve.sh and the cheats
python3 tasks/<slug>/authoring/variant_check.py alternative correct solutions must score 1
python3 tasks/<slug>/authoring/field_report.py  no graded field is dead weight
python3 tasks/<slug>/authoring/cheat_report.py  which test catches each cheat
python3 tools/docker_trial2.py <slug> --all     every trial on the real two images
python3 tools/docker_trial2.py <slug> --variants alternative correct solutions, real verifier
python3 tools/textcheck.py <passed.md> <draft>  instruction cadence
python3 scripts/preflight.py tasks/<slug>
python3 scripts/package.py tasks/<slug>
```

`tools/docker_trial.py` and `tools/run_local_rollout.py` are the older, single-task versions,
hardcoded to `rollout-cache-coherence`. Use `docker_trial2.py` for anything new.

`scripts/` and `docs/QUALITY-REVIEW.md` were refreshed from kit v1.9.1 on 2026-08-12. That
version renamed the STATE.md field preflight looks for: the line must now read
`- Tactics making that true: ...` with the tactic names **on the same line, after the colon**
(`A1`, `B2`, or `prong A`). The older `- Tactics (docs/DIFFICULTY.md):` heading no longer
matches and both earlier tasks had to be edited for it.

`build_gt.py` must refuse to write a ground truth it cannot prove independently. Here every
expected token stream has to be reproducible from scratch, under one parameter snapshot, by a
sealed generator sharing no code with the engine.

## Verifier architecture that passed

The overlay pattern, for any task where the solution is code inside the repo:

- `artifacts` lists **only the editable paths**. Declare a wider candidate set than strictly
  needs changing, so the boundary does not hand over the diagnosis. One of the four files
  here needed no change at all.
- `tests/Dockerfile` bakes a pristine copy of the whole tree (`COPY . /tests/`, then
  `cp -a /tests/pristine /pristine`). `test.sh` copies it to a work dir and overlays the
  agent's declared files. Edits outside the declared set are structurally impossible.
- Ground truth in `tests/gt.json`, `chmod 600`, root-owned.
- Grade on three axes, all-or-nothing: outputs, exact work counters, lifecycle events.
- Re-prove ground truth at verification time with a sealed independent implementation.

### Collect the evidence outside the process you are measuring

`turn-seam-alignment` has now been passed twice by probes that did no work, and both got in
through the same door. A counter the run reports is a number it chose. A record the run
keeps is a list it can empty and refill: the second probe encoded every render whole, asked
the shipped tokenizer which resume positions were legal, and then rewrote the record to
describe the resume it never took - four lines, no merge table read anywhere, every entry
it left behind true.

Structural checks on that record do not help, because a submission that can afford a full
encode can afford to make the record honest. What helps is that asking and paying are the
same act. Put the metered operation behind a socket, serve it from a root process that
writes down what it was asked for as it answers, and grade that tape:

- the run cannot get ids without asking, and cannot ask without being counted;
- exploratory work stays on the tape, so "expensive, then rewrite" fails on the events it
  cannot remove - a scenario with four renders accounted for by eleven encodes;
- a run that answers everything without asking leaves an empty tape, which is graded as
  what it is rather than as a perfect report;
- the same service can carry the other counters (forwards here), which turns them from
  reported numbers into evidence for free.

Costs about 150 lines. The shipped client falls back to computing locally when the socket
is absent, so the agent's own container is unchanged and the run's only way to avoid the
meter is to leave no evidence. Make the authoring emulation start a meter too, or the local
gates go on scoring the run's own account of itself and a forgery looks clean until the
containers run.

Isolation, since the verifier imports agent code (`docs/VERIFIER-ISOLATION.md`):

```
chmod 700 /logs/verifier; echo 0 > reward.txt      # lock and default-deny first
cp -a /pristine/. /work/app; overlay declared files; chown -R sandbox /work
setsid --wait env APPDIR=/work/app setpriv --reuid=1002 --regid=1002 --clear-groups \
    timeout --signal=KILL 600 python /tests/runner.py /work/out.json
python /tests/reap.py 1002                          # kill double-forked survivors
pytest --ctrf ... && echo 1 > reward.txt || echo 0 > reward.txt
```

The run writes to a sandbox-writable work file. pytest runs afterwards as root, reads that
file defensively as hostile input, and never executes agent code. Confirm it: the privilege
probe should report `uid=1002` and `PermissionError` on the reward channel, the ground truth,
the pristine tree and the tests.

The scenario file is readable by the run and that is fine: knowing which op sequences execute
does not produce the token streams they expect. `cheat-peek-scenarios.sh` documents that.

## Traps that cost time here

- `setsid` without `--wait` can fork, so `wait` returns immediately and grading starts before
  the run finishes. Use `setsid --wait`.
- `pkill` is not in `python:3.12-slim`, and apt is unreachable in this sandbox. `tests/reap.py`
  walks `/proc` instead. `setpriv`, `setsid`, `timeout`, `useradd` are all already present, so
  the verifier image needs no apt layer at all.
- Comparing agent-generated events in order over-constrains a correct solution. Compare
  engine-generated events in order and agent-generated ones as a set, and state the queue
  discipline in the instruction so the counters stay well defined.
- A cached-block index and a page pool must be reconciled through code the agent cannot edit,
  or the answer becomes "invent the reconciliation", which is a different and worse task.
- Isolation probes built on the reference score 1 legitimately. Build them on the shipped tree.
- `pip install pytest==9.1.1 pytest-json-ctrf==0.5.2` is needed on the host before
  `run_local_rollout.py` will grade anything.
- A cheat whose prologue double-forks and sleeps holds the pipe open, so the host emulation
  blocks for the sleep duration. Expected; the container run reaps it.

## Sandbox notes

- Docker Hub returns 429. Pull `mirror.gcr.io/library/python:3.12-slim` and
  `docker tag ... python:3.12-slim`. `dockerd` usually needs starting by hand:
  `(dockerd >/tmp/dockerd.log 2>&1 &)` then poll `docker info`.
- Builds inside docker do not trust the sandbox's egress CA, so pip fails with
  `CERTIFICATE_VERIFY_FAILED`. `tools/docker_trial.py` injects `/root/.ccr/ca-bundle.crt` into
  a temporary copy of the build context. The shipped Dockerfiles stay unchanged.
- `deb.debian.org` returns 403 through the egress proxy, so any apt layer fails to build
  locally. Avoid apt entirely.
- `harbor` is not installed. `tools/docker_trial.py` reproduces the two-container trial with
  docker directly. Say plainly in the handover that `harbor check` was not run.

## Making the next one harder

Add **one more axis of discovery that the instruction cannot state without giving it away**.
Do not add more stated rules, which is grinding rather than difficulty, and do not add another
exact-match counter, which is where the run audit bites.

Two designed for the ML task and not built:

- **A second holder of the same cached state**, such as an offload tier that also caches and
  must be retired in step with the primary index. An agent that fixes one side gets every
  output right and the wrong counters. The instruction can state the requirement ("nothing
  computed before that point may be served after it") without hinting that two holders exist.
- **State that must be reconstructed rather than recomputed** across a lifecycle event, such
  as calibration scales restored from a host copy instead of reset to a default. It changes
  outputs after the cycle, and the requirement is stateable while the mechanism is not.

Guardrails: the reference must still pass every run by a path you can describe step by step,
the expert time estimate must stay honest, and every new graded quantity must survive the
variants suite. A design whose expert path is uncertain is rejected exactly like a trivial
one, and zero solves of eight is a rejection, not a triumph.

## Definition of done

- `preflight.py` clean, no warnings.
- `docker_trial.py --all`: oracle 1, nop 0, every cheat 0, including every isolation probe.
- `variant_check.py`: every alternative correct implementation scores 1.
- `field_report.py`: no graded field is dead weight, and none encodes a tie-break.
- `textcheck.py` clean against **both** passing instructions.
- Instruction-to-verifier coverage walked line by line, both directions.
- Built agent image inspected file by file for leaks.
- `STATE.md` current: verifier contract, difficulty argument, expert path, estimated solves,
  and every gate not run.
- Handover states honestly what was run and what was not. Packaging proves nothing.
- **Re-run `scripts/package.py` and send the rebuilt `tasks/<slug>.zip` back to the user**
  with `SendUserFile`, in the same reply that reports the fix. This applies to every turn
  that changes a task - a verifier hardening, a recalibration, a new task - not only to
  the first delivery. The user's next step is uploading that zip to the pipeline, so a fix
  described in chat and left sitting in the repo is a fix they cannot use. Package after
  the last content edit, never before, and check the zip's timestamp against the tree
  before sending it. `git status` clean on the zip means it matches what was committed,
  not that it matches the tree.
