# Task state

Working memory for `alias-settle-report`. This file never ships: `package.py` drops it and no
pipeline gate reads it. It records the post-probe redesign so the next session can audit the
difficulty decision instead of treating it as a cosmetic change.

## Current stage

`Stage 7 - gates`, post-easiness-probe hardening and quality-review alignment. The previous bundle passed the structural,
AI, similarity and reference gates, but failed the easiness band: 2 of 3 low-effort screening
agents solved it. The supplied trajectories show the same shortcut in both successful runs:
they read the small tree, implemented exhaustive legal-group search, and built a self-checking
oracle from the stated transition rules. The task was revised without changing its observable
filing contract, and the subsequent pipeline run passed both the easiness and difficulty probes.

## Task summary

`Software / Algorithms`. The tree under `/app` is the filing end of an evaluation harness.
Runs post scores for items under keys; matchers declare that two keys are one item, or that two
keys are not; a board must be handed exactly one line per watched key, carrying the smallest key
in that key's item and the score of the first post the item holds. The graded decision is when
each line may be written: at the first tick at which nothing that could still happen would move
it, and not before. Both directions are graded, so an eager policy and a conservative one fail
alike.

## Why the original probe was too easy

The original probe result was 2 of 3 solved, with low reasoning effort. All three trajectories
used the same high-level method. Once they saw the small state space and the precise event rules,
they immediately planned a group enumerator, copied the same fixed-point idea into `hold.py`,
and then made a brute-force oracle or fuzzer to validate it. The verifier's hidden cases added
coverage but did not change the plan, because every hidden state was still small enough for the
enumerator.

The root cause was planning-stage mode C: the graded question was a fully specified, decidable
predicate over a small state. The definition itself supplied the algorithmic plan. This was not
a leak and the verifier was not weakened.

## Revised difficulty strategy

- Why a frontier agent cannot one-shot the plan (the strategic answer): the obvious plan remains
  exact group enumeration when differences are present, but it is now resource-infeasible on
  broad no-difference states. A solver must notice and prove the special graph property that
  removes the exponential subgroup search, while retaining the exact all-pairs difference rule
  on states where it is needed. The input brief does not announce the scale distribution, and
  the generated wide cases do not exist until after the agent finishes.
- Tactics making that true: A1, A2, B1, B2, C1, C2, C3, and C4. A1 poisons the usual
  union-find-plus-reachability prior with a resource boundary; A2 describes the behavior without
  naming the optimization; B1 spreads the relevant facts across the machine, editable policies,
  and sealed differential generator; B2 stacks fixed-point filing, stale tag pools, item-level
  differences and the scale condition; C1 fences the editable artifacts from the sealed machine;
  C2 denies an expected-output oracle; C3 resource-gates exhaustive subgroup enumeration while
  the reference uses a decisive component closure; C4 grades all rows and filings all-or-nothing.
  The route-around is blocked by nonce-generated cases, root-only expected data, and the
  unchanged-tree and attestation checks.
- Assistant's attack on the original plan: I first implemented the same group-by-group search
  the screening agents used. It agrees with the model on small and barred cases, but on a single
  open tag spanning roughly thirty keys it must enumerate an exponential family of legal
  groups. That makes it the wrong plan for the revised input distribution even though its
  answer is mathematically correct on states it can finish.
- Revised attack on the plan: I compared the slow trajectory-style implementation with the
  optimized reference on the wide generated seed. The reference completed the case in about
  0.07 seconds locally; the exhaustive implementation was still running after more than
  70 seconds and was interrupted. The reference/model differential check then passed on 900
  generated sets, including wide cases. The four independent correct variants also pass after
  receiving the same no-difference optimization.
- Estimated solves out of 8: the difficulty probe passed after hardening. The exact solve count
  was not recorded in this workspace; the previous measured result was 2 of 3 on easiness before
  the new scale boundary.
- Difficulty score anchor: the previous submission's anchor was the 2-of-3 easiness rejection;
  the revised anchor is the measured decisive runtime gap on the hidden wide family.

## Revised input boundary

The observable filing semantics are unchanged from the contributor-approved fixed-point version.
The instruction now states the verifier's 600-second completion limit and that graded no-bar
tag pools can contain 25-30 keys. The generated verifier sets include a broad no-difference family every twelfth generated
seed. Each such set has 25-30 keys, four to six watched keys, one open tag spanning all keys,
and no bars. There is also a fixed `wide-no-bars` enumerated case. A no-difference connected
component is exactly the union of every legal group reachable from the seed, so the reference
and sealed model use a linear component closure there. The exact group search remains in place
for all states with differences.

## Verifier contract

- Artifacts the agent produces: `/app/bind/rch.py`, `/app/bind/hold.py`, `/app/bind/card.py`,
  `/app/bind/seq.py`.
- What is checked: the ordered rows emitted by the machine and the filing table collected
  beside them, exactly and with no partial credit. There are 37 enumerated sets plus 300
  nonce-generated sets built inside the verifier after the agent has finished.
- The expected outputs are sealed in `tests/gt.json` and `tests/oracle.py`; the generated sets
  are evaluated directly by the sealed model. The agent environment receives neither.
- The verifier also checks the executed tree against pristine files, sealed machine function
  fingerprints, emitter and interpreter counts, the run nonce, unprivileged execution, the
  root-only reward channel, and process cleanup.
- The contract was not loosened. The added wide cases exercise the same rows, filing table,
  fixed-point rule, and attestation layers as the existing cases.

## Decisions and reasons

- The no-bar fast path is a mathematical optimization, not a semantic exception: without a
  difference every reachable subgroup is legal, so its union is the ordinary connected
  component. A correct implementation may use it or derive the same result another way.
- The reference/model agreement is checked before ground truth is written. `gt.json` contains
  the 37 enumerated sets, and the 300 generated sets are rebuilt from the per-run nonce.
- Correct variants are generated from the reference with independent representations and all
  pass the same model. Their tallies remain floors because one variant folds reachability into
  the readiness test.
- `card.py` and `seq.py` ship correct. The brief says not all four files need changing;
  establishing that is part of the work.
- Every watched key is posted at least once, and every run and tag shuts before the set ends.

## Gates run after hardening

- `make_variants.py`, `fuzz.py 900`, `build_gt.py 900`, and `determinism.py` passed.
- `variant_check.py 300` passed all four independent correct variants.
- `field_report.py`, `tiecheck.py`, `normalise.py`, `readingcheck.py`, `onelinecheck.py`,
  `deadfieldcheck.py`, `solvecheck.py`, `hintcheck.py`, `simcheck.py`, `structcheck.py`,
  `catcheck.py`, and `preflight.py` passed. The text-style comparison against the generic
  template is only diagnostic; it reported a narrower vocabulary and did not change the
  contributor-approved instruction.
- The package was created and `zipcheck.py` passed after repairing the Windows ZIP mode bits.

## Local limitations

The Docker reference/nop trials and the full cheat suite could not run because this Windows
machine has no Docker executable and WSL has no installed Linux distribution. The local
three-agent probe and `harbor check` were also unavailable. The external pipeline result is the
authority for the reported easiness and difficulty passes.
