# grant-spread-order — working notes

Scratch for the next session. This file never ships: `package.py` excludes it and no gate
in the pipeline reads it. The load-bearing half of the verifier contract lives in the
module docstring of `tests/test_outputs.py`, which is the file the run audit and the
quality review actually read, so losing this one loses nothing.

## What the task is

A policy kernel over a tree of nodes. Entries placed on a node say a subject is allowed or
refused a right; placement materialises copies down the tree; questions are answered from
what is standing on the node. The agent rebuilds four decision files. Graded on the answers
(verdict plus the identity of the winning entry) and on the holdings (a store digest after
every operation, plus a full dump at the end), over 29 enumerated journals and 300 built
inside the verifier from a nonce made after the agent stops.

## Difficulty, in the four lines preflight reads

- Why a frontier agent cannot one-shot the plan: the ordering is stated outright and is
  therefore execution, while the two things that decide whether an implementation of it is
  correct - that a node's offer is a transformation of its holdings, and that an entry
  keeps the identity of the act that made it through every re-flow - are stated nowhere and
  produce a plausible store when they are got wrong.
- Tactics making that true: prong A (the memorised ordering is specifically wrong), prong B
  (the record layout, the offer and the re-flow are recoverable only by reading behaviour),
  prong C (a wrong reading surfaces only in the verifier), B2, C1, C4.
- My own attack on the plan: my first plan evaluated inheritance dynamically at read time
  and graded the effective rights at the end of the journal, which is wrong twice - dynamic
  evaluation makes the state derivable from the current tree so there is nothing to
  discover, and grading only the end state lets an implementation diverge in the middle and
  converge by the end.
- Estimated solves out of 8: 2 of 8, allowing for the realised rate drifting up.

## Why a frontier agent cannot one-shot the plan, at length

Every prior it has says a refusal outranks a permission and that the nearest rule in the
tree wins. Neither is true here, and both are stated in the brief, so the ordering is
execution rather than discovery. What is not stated, and what has to be derived from the
kernel's behaviour, is that what a node offers its children is a transformation of what it
holds rather than a copy of it, and that an entry keeps the identity of the act that made
it through every later re-flow. The first breaks the natural implementation of the
inheritance invariant on two scopes at once. The second breaks the natural implementation
of the third ordering key, because a re-flow puts entries carrying old sequence numbers in
after entries carrying new ones, so trusting the order of the store is right until a move
happens. Neither shows as a crash; both show as a store that is right for forty entries and
wrong for one, and there is no expected output anywhere in the tree to notice it against.

The prong B detail, since the summary above is compressed: no comments anywhere under
`environment/`, identifiers in the register of ordinary internal code, and twenty stated
rules that interact rather than sit beside one another. The C1 fences are the four
must-still-work cases, graded as hard as the rest. C4 is the 300 unseen journals under
all-or-nothing grading.

## The attack, at length

My first plan was to grade the effective-rights matrix at the end of the journal and let
inheritance be evaluated dynamically at read time. That is wrong twice. Evaluating
dynamically makes the whole thing a tree walk with no history in it, so the state is
derivable from the current tree and there is nothing to discover; and grading only the end
state lets an implementation diverge in the middle and converge by the end. Materialising
at operation time and digesting the store after every operation fixes both. The second
attack was that the ordering rule is a three-key sort, which a frontier model writes cold —
so the ordering is stated outright in the brief and the difficulty was moved into what the
store has to hold for that stated rule to keep meaning. `tools/onelinecheck.py` reports no
exact rule at depth <= 2 for three of the four graded decisions, which is the mechanical
version of that argument.

## What is measured, and what is not

Run from the repo root unless noted.

    python tasks/grant-spread-order/authoring/sync.py
    python tasks/grant-spread-order/authoring/build_gt.py --fuzz 800
    python tasks/grant-spread-order/authoring/emit.py
    python tasks/grant-spread-order/authoring/make_variants.py
    python tasks/grant-spread-order/authoring/determinism.py 40
    python tasks/grant-spread-order/authoring/fuzz.py 800
    python tasks/grant-spread-order/authoring/trial.py --all --count 60
    python tasks/grant-spread-order/authoring/variant_check.py 60
    python tasks/grant-spread-order/authoring/cheat_report.py --count 60
    python tasks/grant-spread-order/authoring/field_report.py --count 150
    python tools/onelinecheck.py grant-spread-order
    python tools/readingcheck.py grant-spread-order 60
    python tools/deadfieldcheck.py grant-spread-order
    python tools/solvecheck.py grant-spread-order
    python tools/forgecheck.py grant-spread-order
    python tools/hintcheck.py grant-spread-order
    python tools/simcheck.py grant-spread-order
    python tools/textcheck.py tasks/guard-mark-unwind/instruction.md tasks/grant-spread-order/instruction.md
    python tools/structcheck.py tasks/grant-spread-order/instruction.md
    python scripts/preflight.py tasks/grant-spread-order
    python scripts/package.py tasks/grant-spread-order
    python tools/zipcheck.py grant-spread-order

**NOT RUN: the two-image Docker trial.** Docker is not installed on this Windows authoring
host, so `authoring/trial.py` is a host emulation - real runner, real grader, real ground
truth, real pytest, no container. It does not cover the privilege drop to uid 1002, the
root-owned reward channel, the root-only ground truth and grader, the inherited descriptor,
the wall clock timeout or `reap.py`. The isolation probes graded there prove the grader's
logic rejects them; they do not prove the sandbox contains them. Two probes are inert under
the emulation for a knowable reason and would fire in the container: `cheat-plant-and-exit`
and `cheat-plant-run-output` both write `/work/run/out.json`, which does not exist on this
host, so their write fails and is swallowed.

## Traps hit while building this, so nobody hits them again

1. **`subprocess.run(["bash", ...])` on Windows is the WSL launcher.** With no distro
   installed it exits 1 having done nothing, and a trial harness that ignores that grades
   the SHIPPED tree while reporting that it graded a cheat. Every cheat scored 0 and the
   suite proved nothing. `trial.shell()` now resolves Git Bash explicitly and
   `trial.playbook()` raises on a non-zero exit.
2. **The generator was not deterministic across processes.** `twist()` shuffled a list
   built by iterating a set of node names; Python randomises string hashing per process;
   the runner and the grader are different processes. They built different journals from
   the same seed and the reference lost one journal in thirty. `authoring/determinism.py`
   is the permanent check.
3. **A cheat prologue in a new module never reaches the executed tree.** `test.sh` overlays
   only the four declared artifacts, so a probe that put its payload in `pol/_pre.py` died
   on an ImportError instead of exercising the layer it was aimed at. Prologues go inside
   `weigh.py`.
4. **Three cheats were lottery tickets.** `any-membership-is-one-hop`, `plant-returns-early`
   and `entry-returns-to-origin` differed from the reference on 4, 4 and 7 journals of 150.
   Fixed in the generator rather than in the grader: a crew chain is seeded, a quarter of
   placements land on a subject and right the node already carries, and `twist()` builds the
   barred-snapshot-below-its-origin shape on purpose. Now 17, 16 and 32 of 150.
5. **The fuzz found two real semantic holes in the reference**, both of which the enumerated
   set missed: a here-only placement replacing a spreading entry left the copies standing
   below, and an entry could be offered back to the node it was placed on after a barred
   node carried a snapshot below its origin. Both are now stated rules, enumerated cases and
   cheats.
