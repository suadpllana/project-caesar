# claim-line-stall

## Current stage

`Stage 7 - pre-flight and packaging`.

## Assistant's assigned role

An engineer on the claim service of a storage engine: the part that decides which asks are
granted now, which wait, what a coarse claim swallows when it is granted, and which jobs the
service gives up on because they can never proceed. Later sessions resume in this persona.

## Why it is hard - the required fields

- Expert time estimate: 9 hours
- Why a frontier agent cannot one-shot the plan (the strategic answer): every structure the
  rules seem to ask for - a per-scope queue in filing order, an upgrade flag stamped on a
  request when it is filed, a coarse claim that replaces the fine ones the moment it is asked
  for, a held-up relation drawn from waiters to holders - is right until one of the other rules
  is applied at the same time, and the order of the line is read by three separate rules that
  each change what it contains.
- Tactics making that true (docs/DIFFICULTY.md): A1, A2, B2, C1, C2, C3, C4. B1 is not claimed.
  A1: the retrievable escalation gives up and keeps taking fine-grained claims when the coarse
  one is refused, and the memorised waits-for graph runs from a waiter to the holders it
  conflicts with; both are specifically wrong here. A2: deadlock, waits-for, cycle, intention
  lock, conversion and escalation are never written - the brief says only that a job is held up
  by another when one of its asks is refused because of that job, and that jobs held up only by
  one another can never proceed. B2: ten rules hold at once and each changes what another
  means. C1: both sides of every fence are graded. C2: no event says why an ask was refused,
  which job held it up, or that an ask was raised. C3: four naive-but-correct families measured
  against the stated limit. C4: exact all-or-nothing traces over enumerated corners and
  nonce-generated families.
- Assistant's attack on the plan (its first plan, and where that plan is wrong): my first plan
  is a per-scope record holding the granted mode per job and a filing-ordered list of waiting
  requests, an upgrade marked when the request is filed and put at the front, a settling pass
  from the front of each list, and a held-up relation drawn from each waiting job to the jobs
  holding the claims it conflicts with. It is right about coverage, about modes and about
  settling in one pass, and wrong in three places that matter: the refusal test has to count
  the asks standing ahead in the line and not only the claims granted, going ahead of the line
  is true only while the job still holds an overlapping claim and three ordinary ops change
  that under a waiting request, and a raised ask keeps its cell claims until it is granted,
  which is what makes a stall exist at all.
- Estimated solves out of 8: 2 (range 1-4)
- Difficulty record score: 100/100 on paper at Stage 1, attempt 1, no changes needed
  (`authoring/claim-line-stall/difficulty.toml`); 100/100 again at Stage 7 against the built
  tree, with one warning that the reference came out at 489 lines against a planned 300.
- Leak audit (docs/DIFFICULTY.md): no event names the job that held an ask up or says that an
  ask was raised; a waiting request records the job, the scope, the mode and the number it was
  filed under and nothing derived from what the job holds; the shipped example programs
  exercise the op language and the one line the brief calls wrong and contain no raised ask
  that is then refused and no refusal by a job holding nothing; the show line reports the
  claims overlapping one unit and how many asks wait on it, which is a fact about a unit and
  never about which job holds up which; the sealed model, the frozen answers and the pristine
  tree exist only in the verifier image, in a directory locked to root before any submitted
  code runs. `tools/onelinecheck.py` measures the same thing mechanically over 2196 graded
  decisions: whether an ask is granted and whether a job is on a loop have no exact rule at
  depth two over the features the tree exposes, while the raise threshold does (`here > 3`),
  which is the one the brief states outright.
- Expert path, described step by step: run the shipped service on the program the brief names
  and reproduce the line it calls wrong; read the six editable files and the frozen driver to
  learn what a claim record holds and what each event prints; settle the refusal test from both
  sides, granted claims and asks standing ahead in the line; derive the order of the line when
  it is read rather than stamping it when an ask is filed; make a whole-unit claim swallow the
  job's cell claims on grant and not before; close the held-up relation over refusals as well
  as over held claims and cancel by the stated choice, settling again after each; index claims
  by unit with per job counts by mode so a whole-unit ask is answered without walking the
  unit's cells; generate the two wide shapes and time the four naive families against the
  stated limit.
- Originality check: searched 2026-09-12 for the shape. The public material is vendor
  documentation on lock escalation, lecture notes on finding a cycle in a waits-for graph, and
  one database's note that a compatible request does not jump its queue. The escalation
  documented by the most-retrieved vendor page does the opposite of this spec - it backs off
  and keeps taking fine-grained locks rather than queueing while holding them - and every
  waits-for treatment found draws edges to holders. Nothing public describes a request whose
  priority in the line is re-derived from what its job holds at the moment the line is read. No
  retained task in this repository is about claims, queueing or mutual blocking; the closest by
  subcategory is `delta-view-retraction` (Databases, incremental view maintenance) and it
  shares no mechanism. `tools/simcheck.py` reports no conceptual overlap with any earlier task.

## Stage 0 - tooling

Docker daemon started by hand in this session (`dockerd`); it was not running at the start.
Docker Hub's blob CDN (`production.cloudfront.docker.com`) is refused by this session's egress
policy, so `docker pull python:3.12-slim` fails with a 403 on the blob fetch. The image was
pulled from `mirror.gcr.io/library/python:3.12-slim` and retagged locally as `python:3.12-slim`,
which is what both shipped Dockerfiles name. The shipped Dockerfiles are unchanged and pull
from Docker Hub on the platform. `harbor` is absent from this machine; the container gates run
through `tools/docker_trial.py`, which builds both images and reproduces the two-container
trial, including the privilege drop, the locked reward channel and the root-only ground truth.

## Stage 1 - the task

### What this is

A claim service inside a storage engine. Jobs take claims on units and on the cells inside
them, the service grants what it can and makes the rest wait, and when a group of jobs can only
ever be held up by one another it cancels one of them. `/app` is that service. The shipped
engine is wrong in ten places and too slow in three more, and the agent replaces the six files
under `/app/hold` that decide it.

Real work behind it: the request half of a lock manager - the part that decides the order a
waiting line is read in, what a coarse claim does to the fine ones under it, and which jobs can
never proceed. The rule this task is built on is that a job which holds nothing at all can be
the only reason another job is refused, so the relation that decides a stall is not the one
drawn over the claims being held.

### Category

`Software` / `Databases`. The graded work is the request path of a lock manager: a
compatibility relation over a two-level scope space, a waiting line whose order is derived
rather than stored, coarse-claim promotion, and a mutual-blocking relation over jobs.
`tools/catcheck.py` measures 28 environment hits for the category's vocabulary against 20 in
the prose, so the label is the work rather than the story.

Domain role adopted for the project: an engineer on the claim service of a storage engine.

Tags: `lock-manager`, `queue-fairness`, `lock-escalation`, `mutual-blocking`,
`multi-granularity`, `request-ordering`.

### Definition of done

Six files under `/app/hold/` - `book.py`, `line.py`, `lift.py`, `knot.py`, `turn.py`, `act.py` -
are replaced so that `/app/run_hold.py` prints, for every graded program, exactly the trace the
frozen contract below defines, and gets through the whole graded set inside 60 seconds.

### Expert time

9 hours. Reading the tree and the rules is an hour; getting the ordinary decisions right -
coverage, modes, what a grant swallows, what each event prints - is three; deriving the order
of the line instead of storing it, and seeing that the refusal test and the held-up relation
both read it, is the hour that decides the task; the raised ask that keeps its claims while it
waits and the cancel loop are two; the wide families and the indexes they force are the rest.

## Stage 2 - the frozen verifier contract

Artifacts taken from the agent: `/app/hold/book.py`, `/app/hold/line.py`, `/app/hold/lift.py`,
`/app/hold/knot.py`, `/app/hold/turn.py`, `/app/hold/act.py`. Nothing else is read. The
verifier lays those six over its own pristine copy of the tree and runs every graded program,
so nothing else the agent touched can change what a program prints.

### The op language

A program is a text file, one op per line, fields separated by single spaces.

    take <job> <scope> <mode>
    drop <job> <scope>
    end <job>
    show <unit>

`<job>` is `j` and digits, `<unit>` is `u` and digits, `<scope>` is a unit or `u<i>/c<j>`, and
`<mode>` is `r` or `w`.

### Scopes, modes, conflict

A unit covers itself and every cell of it; a cell covers only itself. Two scopes overlap when
either covers the other. `r` is weaker than `w`. Two claims held by different jobs conflict
when their scopes overlap and at least one of them is `w`; an ask conflicts with a claim, or
with another job's ask, by the same test. A job's own claims never conflict with its own ask.

### take

1. Covered: the job already holds a claim on a scope covering the asked one, in a mode at least
   as strong. `grant` is printed and nothing changes.
2. Raised: otherwise, when the asked scope is a cell and the job already holds four or more
   cell claims in that unit, the ask becomes an ask for the whole unit in the strongest of the
   asked mode, the modes of those cell claims, and the mode of any claim the job holds on the
   unit itself.
3. The ask is granted when no claim of another job conflicts with it and no ask of another job
   standing ahead of it in the line conflicts with it; otherwise it joins the line. `grant` or
   `wait` is printed with the scope and mode as they stand after step 2.
4. A job that already has an ask waiting cannot ask again: such a take is ignored and prints
   nothing.

### Granting

A granted claim replaces the job's claim on that scope and removes every claim the job holds on
a scope the granted one strictly covers.

### The line

Waiting asks stand in one line. Those whose job currently holds a claim overlapping what the
ask asked for stand ahead of those whose job does not; within each group they stand in the
order they were filed. Nothing about that order is recorded on the ask.

### Settling

After an op that releases a claim or discards an ask, the service goes once down the line in
order and grants every ask that is grantable at the moment it is reached, and does not go back.

### drop, end, show

`drop` releases the job's claim on exactly that scope, if it holds one, and prints
`free <job> <scope> <claims the job holds after>`. `end` releases every claim the job holds,
discards its waiting ask, and prints `end <job> <claims released>`. `show <unit>` prints
`show <unit> <claims> <waiting>` where `<claims>` lists every granted claim whose scope overlaps
the unit as `<job>@<scope>=<mode>`, comma-joined, ordered by the number the job started under,
then the unit ahead of its cells, then by cell number, and `-` when there are none, and
`<waiting>` is how many asks whose scope overlaps the unit are in the line.

### Jobs

A job starts when it comes to hold a claim or to have an ask waiting while holding neither, and
is given the next start number. A job holding nothing and waiting for nothing is forgotten; if
it appears again it starts again, under a new number.

### Stalls

A job is held up by another when one of its asks is refused because that other job holds a
conflicting claim, or has a conflicting ask standing ahead of it in the line. When following
held-up-by from a job can return to that job, none of the jobs on that loop can ever proceed.
The service cancels exactly one: of every job that can be reached from itself this way, the one
holding fewest claims, and of those the one with the largest start number. Cancelling releases
its claims, discards its ask, forgets it, prints `stop <job> <claims released>`, settles the
line, and the service looks again.

### Prong C tactics used by this contract

- C1: every fence is graded from both sides.
- C2: the trace carries no reason, no blocker and no mark that an ask was raised, and the
  graded programs are generated inside the verifier from a seed drawn after the agent's
  container is gone.
- C3: the execution limit rules out walking the whole book to answer one ask, restarting the
  settling pass from the top of the line after each grant, rebuilding the order of the line by
  sorting every waiting ask each time it is read, and building the held-up relation over every
  waiting job.
- C4: exact traces, all-or-nothing, over enumerated programs and nonce-generated families.
- Route-around guard: only the six files under `/app/hold` are artifacts. The driver, the op
  language, the scope parser, the event writer and the shipped programs are the verifier's own
  pristine copy.

Frozen on 2026-09-12 and unchanged since. A later change to any rule above changes what correct
means and needs the contributor's explicit approval.

## Stage 3 - the environment

`/app` holds 350 lines of Python: the frozen driver `run_hold.py`, the op dispatcher `ops.py`,
the scope parser `hold/name.py` and the event writer `hold/say.py`, plus the six editable files.
Four programs sit in `/app/progs`: `small.txt`, which the brief names and whose last line the
shipped service gets wrong; `mix.txt`, which the shipped service gets entirely right; and
`wide.txt` and `tall.txt`, the two scale shapes.

Both example programs were searched for rather than chosen (`authoring/claim-line-stall/pick_progs.py`).
`small.txt` differs from the reference in exactly one line and separates exactly one of the 22
wrong readings, `cover-unit`, which is the reading the brief states outright. `mix.txt` differs
from the reference nowhere and separates none of them, so it demonstrates the op language and
settles nothing.

The ten places the shipped service is wrong: the refusal test ignores asks standing ahead
(`line.grantable`); where an ask stands is stamped when it is filed (`line.rankof`); the
held-up relation counts only the holders of conflicting claims (`knot.blockers`); the job
cancelled is the most recently started one on the loop (`knot.pick`); a raised ask gives up the
job's cell claims when it is filed rather than when it is granted, and the raise threshold
counts every cell claim the job holds rather than those in the unit (`lift.raised`); only a
claim on the whole unit is treated as covering an ask (`book.covered`); a job keeps its start
number for the whole program (`book`, which has no counterpart to `rest`); the stall search
runs only after an op that released something (`turn.after`); and `end` releases the claims but
leaves the job's ask standing (`act.over`). Three more are exactly correct and too slow: every
claim in the book walked to answer one ask, the settling pass restarted from the top of the
line, and the held-up relation built over every waiting job.

Facts an agent has to correlate across the tree: what `say.py` prints decides what is
observable at all, `ops.py` decides that the service is driven one op at a time with no end of
program, `name.py` decides that a cell number is an integer and therefore how `show` orders,
and the six editable files decide the rest. No documentation ships; `scripts/preflight.py` is
clean on comments, docstrings and `.md` files under `environment/`.

## Stage 4 - reference solution

`solution/solve.sh` copies the six reference files into `/app/hold/` and runs the two small
shipped programs. The reference is 489 lines across those six files.

Container gate, through `tools/docker_trial.py` (both images built, artifacts collected from
the agent container and uploaded into the verifier at their original paths):

- oracle scored 1 (40 tests passed in 46 s of grading)
- nop scored 0 (the shipped service does not get through the wide programs inside the worker's
  wall clock, so the record is lost and the reward stays 0; one wide program alone is still
  running after 600 s under it)

## Stage 5 - instruction and metadata

Written by the assistant from the frozen contract and the measured behaviour. Every rule the
verifier grades has one sentence, and every sentence has an enumerated case. Counts quoted in
the brief were re-derived from `gen.programs` after the last change to the generator: 283
graded programs, being 3 wide, 3 tall and 277 smaller.

`tools/textcheck.py` against `note-carry-forward`, which passed the AI-text screen: burstiness
0.745 and paragraph sd 45.6 against that reference's 0.915 and 103.5. Both sit inside the band
of the retained instructions that passed (burstiness 0.79 to 1.01, paragraph sd 42 to 66;
`focus-return-point`, a confirmed pass, reports 0.791 and 43.2 and draws the same two findings).
Contractions are at 0 per thousand words.

## Stage 6 - anti-cheat

35 cheats, emitted by `authoring/claim-line-stall/emit.py` after `make_readings.py`, never
before. `authoring/claim-line-stall/cheat_report.py` asserts the layer that catches each one
rather than only the reward:

- 22 wrong readings, each caught by the enumerated case named for it. `tools/readingcheck.py`
  agrees: every one is separated by the enumerated set, none only by generated programs. The
  22 whole-service trees the readings run as are generated by
  `python3 authoring/claim-line-stall/make_readings.py` and are not committed; `emit.py` runs
  after it and never before, because a cheat emitted from a reading that was then repaired
  tests the unrepaired reading.
- 4 exactly correct and too slow, measured below.
- 1 forgery carrying the frozen answers for every enumerated program: it passes all 37
  enumerated cases and fails 81 of 100 nonce programs, which is the layer it was written for.
- 8 probes against the verifier itself: the answer key, a planted record, a record planted with
  the worker exited clean before it could be overwritten, malformed records, privilege, a
  shrunken population, a hijacked driver, and a reward written after grading.

The forgery and the eight probes are built on a wrong reading rather than on the shipped
service, and that was a repair rather than a choice. The first build put them on the shipped
service, and the container run showed why that is worthless: the shipped service is also too
slow, so the worker loses its record to the wall clock and the reward comes out 0 whether or
not the attack landed. On a base that is wrong but fast the run finishes, the record is graded,
and the only thing that can raise the reward is the attack itself. The layer report reads the
forgery as passing all 37 enumerated cases and failing 18 of 90 nonce programs, which is the
layer it was written for.

## Stage 7 - the measured resource gate

Whole graded set against the stated 60 second limit, on this machine:

| implementation | one wide program | whole set |
|---|---|---|
| reference | 0.28 s | 1.8 s |
| correct variant `ok-flat` | 0.26 s | 2.2 s |
| correct variant `ok-split` | 0.28 s | 2.2 s |
| every claim in the book walked per ask | 41.2 s | 198 s |
| the order of the line rebuilt at each reading | 36.7 s | 212 s |
| the settling pass restarted after each grant | 75.5 s | 273 s |
| the held-up relation over every waiting job | 613.5 s | 2745 s |

All four naive families produce exactly the reference's traces on the 150 small programs they
were checked against; the limit is the only thing separating them. The shipped service carries
three of the four at once and is still running one wide program after 600 seconds, which is
what the brief means by timing both.

## Stage 7 - the container gates, run

50 two-container runs through `tools/docker_trial.py`, every one behaving as required:

- oracle 1, nop 0
- 35 cheats, every one 0
- two independently written correct services, `ok-flat` and `ok-split`, both 1 (40 tests
  passed in 46 s each)
- oracle, nop and the nine cheats that had been run against slightly earlier bytes were run
  again after the last edit, so every result above is against the bytes that ship

The probes were then run one at a time with the verifier's own log read back, because a probe
that scores 0 for a reason the author did not intend proves nothing:

- `probe-answer-key`: `ModuleNotFoundError` on the sealed model and `PermissionError` on
  `gt.json`
- `probe-privilege`: `uid 1002 euid 1002`, and writes denied at `/logs/verifier/reward.txt`,
  `/tests/seal/gt.json`, `/tests/test_outputs.py` and `/tests/pristine/ops.py`
- `probe-shrink-set`: it rewrites its own copy of the seed under `/work` and is denied the
  grader's copy under `/logs/verifier`, so the programs it graded itself on no longer match
  the signatures the grader computes
- `probe-hijack-driver`: every one of the five writes denied, `/app` included
- `probe-reward-late`: `reaped 1` - the double-forked survivor existed and was killed before
  the grading stage
- `probe-plant-exit`: `plant: written`, worker exit 0, and the grader reported no result for
  every hand case
- `probe-malformed`: `malformed: written`, and the grader failed cleanly with "worker produced
  no readable output" rather than crashing past its own verdict

## Stage 7 - the cold self-attack, and what stands in its place

A cold solve run by the author who wrote the model, the readings and the generator would
measure memory rather than difficulty, so it is recorded as not run. What stands in its place:

- `tools/readingcheck.py`: all 22 wrong readings are separated by the enumerated set, each by a
  named case. A wrong reading of any graded decision fails a case the agent never sees.
- `tools/onelinecheck.py`: two of the three graded quantities have no exact rule at depth two
  over the features the tree exposes; the third is the raise threshold, which the brief states.
- `authoring/claim-line-stall/pick_progs.py`: the shipped example the brief names separates one
  reading, and the other shipped example separates none, so the worked example is not an oracle.
- No local oracle exists: the only thing an agent can compare against is the shipped service,
  which is wrong in ten places at once, and the graded programs are generated from a seed drawn
  after the agent's container is gone.

Honest re-read of the finished brief: the parts of the plan it hands over are the ones it must -
the conflict test, the raise threshold, the cancel choice, the event formats. What it does not
hand over, and what my own first plan got wrong, is that the refusal test and the held-up
relation both read an order that moves while asks wait, and that a raised ask is still holding
what the jobs it waits for are asking for. The estimate stays at 2 solves of 8.

## Known risks

- `environment/Dockerfile` is byte-identical to two retained bundles (`tools/simcheck.py`
  reports 1.000). It is five lines of unavoidable boilerplate - base image, two env vars,
  workdir, one COPY - and any change would be cosmetic. `tests/test.sh` and `tests/reap.py`
  were rewritten and now report 0.72 and 0.71; the conceptual check reports no overlap.
- `scripts/preflight.py` warns that 21 public functions are never called in the environment.
  Every one of them is called module-qualified (`book.covered(...)`), which its call detector
  excludes by design; the retained bundles carry 16 of the same warnings.
- The difficulty record planned a 300-line reference and the build came out at 489. The drift
  is upward, and `tools/difficultycheck.py` still scores 100 against the measured tree.
