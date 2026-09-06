# scope-hold-release

Working notes. Never ships; `package.py` drops this file.

## The frozen verifier contract

Graded artifact: the container's teardown dump, record for record, in order, over 22
named cases and 300 streams generated inside the verifier from a nonce minted after the
agent has finished. Records are `torn name scope cause` and `refused name scope`.

Real work, safe to grade: which instances are created, the scope each is owned by, the
order within a scope, and which resolutions are refused. Two correct implementations
agree on all four by construction.

Implementation choice, never graded: instance numbering, the internal name of the root
scope, the ledger's data structure, and the order two separate scopes are torn down in
relative to each other.

The contract also lives in the module docstring of `tests/test_outputs.py`, which is the
copy that ships.

## The difficulty strategy

- Why a frontier agent cannot one-shot the plan: the ownership rule is stated, the
  capture is not, and no shipped case separates the two readings.

The instruction states the ownership rule outright, so nothing load-bearing is withheld.
What it does not state is where the capture is taken. The container resolves a factory's
scoped dependencies against the scope its holder was built in, so a factory invoked from
two different nested scopes hands back the same dependency instance; that identity is the
only thing in the system that says where the capture lives, and recovering it takes an
experiment the shipped case files do not perform. Measured: a submission that fixes the
three visible files and takes the capture at invocation matches the reference on all four
shipped cases and is wrong on 38.3% of the graded set; a submission told the ownership
rule that still captures at invocation is wrong on 600 of 600 corner streams.

- Tactics making that true: prong A, prong B, prong C, A1, B1, C2 - the active-scope
  charge is the shape every container write-up has, the capture is recoverable only from
  the frozen core's behaviour, and no shipped case separates the two readings, so a
  self-built harness goes green on a wrong answer.

## The self-attack

- attack on the plan: my first plan is to charge each instance to the active scope and
  reverse the teardown list, which is right on every test I would think to write and wrong
  on every stream where a factory is invoked in a scope opened after its holder. I would
  also thread the active scope down the recursion, which gets a transient two steps under
  a singleton wrong. Both were measured before the environment was written.

## Estimated solves

- Estimated solves out of 8: 2 of 8, designed for the bottom of the band

The first submission failed the quality review on `difficult` ("four short functions in a
~150-line codebase"). The repair enriched the environment rather than the brief, which is
the only thing CLAUDE.md records as working on that criterion: marks that pin a
registration to a scope, wrappers, dependency cycles and parting calls at teardown, taking
the environment from 237 to 318 lines, the reference from 40 to 60, the wrong files from
four to six and the graded readings from four to six. That criterion has documented
run-to-run variance; this raises the odds rather than settling it.

## The reference-verification rejection, 2026-09-06

The enriched bundle failed reference verification. Cause: `solution/solve.sh` was
hand-written with a hardcoded four-file list (`own hold gate tear`) and the enrichment had
grown `solution/` to six. The oracle agent therefore ran with the shipped broken `pin.py`
and `shut.py` - readings that move 6.3% and 22.3% of the graded set - and scored 0.

The local trial missed it because its oracle row copied `solution/*.py` directly instead of
running `solve.sh`. Both are fixed: `emit.py` now generates `solve.sh` from whatever
`solution/` holds, and `trial.py` runs the real `solve.sh` the way the platform does.
Validated in both directions - with the four-file list restored the trial reports the
oracle at 0 on `test_the_named_cases_match_the_rules`, and at 1 with the generated one.

A sweep of every other place the artifact list is hardcoded (`task.toml`, `tests/test.sh`,
`tests/test_outputs.py`, `trial.py`) found all four already in agreement; `solve.sh` was
the only one that had drifted.

## Gates run

Host emulation `authoring/scope-hold-release/trial.py --all`: 22 rows, 0 unexpected
(oracle 1 **through the real solve.sh**, nop 0, 4 variants 1, 16 cheats 0).
`determinism.py` identical across 5 hash seeds. `readings.py` 6 of 6 pinned by named cases.
`cheat_report.py` 16 of 16, each attestation probe caught by its own layer and nothing
else. `build_gt.py` proved the reference against the sealed oracle on 22 named cases and
400 generated streams. `onelinecheck` reports no exact rule at depth <= 2 on either graded
decision. `simcheck` conceptually clear. `deadfieldcheck`, `solvecheck`, `catcheck`,
`hintcheck`, `structcheck`, `extraneouscheck`, `forgecheck` clean. `textcheck` clean
against `guard-mark-unwind` and `grant-spread-order`; one burstiness finding against
`rollout-cache-coherence` (0.820 vs 0.929).

## Gates NOT run

Docker is absent on this host, so the real two-image trial did not run: the privilege
drop, the root-owned reward channel, the root-only ground truth and `reap.py` are all
unexercised. `cheat-reward-*.sh` probes are graded by the emulation, which proves the
grader rejects them but not that the sandbox contains them. The three-agent easiness probe
was not run, per the owner's no-subagents rule.
