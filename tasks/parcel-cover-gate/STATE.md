# Task state — parcel-cover-gate

Scratch for the next session. It never ships; `package.py` drops it and no pipeline gate
reads it. Everything that outlives this task belongs in the repo's CLAUDE.md instead.

## Current stage

`Stage 7 — gates run, bundle packaged`. Built 2026-09-03. Never submitted.

## Assistant's assigned role

You are a senior engineer on replicated stores and the client libraries in front of them;
you have spent years with version histories, session guarantees, and faults where every
component behaves exactly as written and the data still never arrives.

## Source repository (repo-based tasks only)

- Repo URL: none - idea-based task, machine written from scratch.

## Task summary

`/app` is a settings fabric. Workers write settings, publish a picture of a named band of
settings, hand those pictures (parcels) to one another, and show one version of each setting
they have caught up with. The shipped tree merges a handed-over parcel pointwise by version
number and throws away whatever it cannot use immediately. Four editable files decide what
may come to be shown; the graded artifact is the ledger of reads and settlings plus the
picture every worker is left holding.

## Why it is hard

- Expert time estimate: 8 hours
- Why a frontier agent cannot one-shot the plan (the strategic answer): the answer turns on two facts that sit in frozen code and nowhere in the brief, and both look settled after the obvious reading - version numbers are handed out globally in write order and sit on every version, so standing-after reads as `>=`, which is right on every history that never forks and wrong the moment two workers write one setting from the same picture; and once standing-after is understood as a walk back through what a version was written on, the walk everybody writes follows a single link, which is right until a settling records two, after which half the history is unreachable and the only symptom is parcels sitting in bags with nothing visibly wrong.
- Tactics making that true: A1 the pointwise merge every replicated cache uses is the poisoned default, B1 the version graph lives in `base/tape.py` which is frozen and which the brief never describes, C2 there is no oracle because whether a worker has caught up is the question itself, C4 all-or-nothing over 31 named feeds plus 300 built from a nonce drawn after the agent stops.
- Your own attack on the plan (your first plan, and where it is wrong): my first plan is a coverage-checked merge with a held bag worked to a standstill, which is right in shape, and inside it I compare version ids in `runs` because they are integers sitting right there, and I write the ancestry walk as one `while a != -1` loop; both of those are wrong, neither raises anything, and the second one only shows up once a settling is put in front of it.
- Estimated solves out of 8: 2 of 8, aimed at the hard edge of the band

## Verifier contract (frozen 2026-09-03)

- Artifacts: `/app/bay/desc.py`, `cov.py`, `stand.py`, `gate.py`. Nothing else is overlaid.
- Graded: the row list (`rd` answers and `sh` settlings, in step order) and the closing
  picture per worker, exactly, all-or-nothing. No counters anywhere and no budget.
- 31 named feeds from `tests/cases.py` against `tests/gt.json`; 300 generated from the run
  nonce and answered by `tests/oracle.py`, which shares no code with the tree.
- Attestations: guarded trace appender; sealed-function digests at import and at feed end
  against a baseline the grader compiles from `/pristine`; interpreter counts on `tape.make`
  and `wire.pack` as floors, plus whether the counting was still armed; executed tree hashed
  against `/pristine` outside the four artifacts, with the compared-file count asserted.

## Measured

| | number |
|---|---|
| shipped tree already right on named feeds | 17 of 31 |
| `cheat-version-order` (numbers, not descent) | 178 of 200 generated |
| `cheat-first-parent` (one link, not the graph) | 114 of 200 generated |
| `cheat-presence-covers` | 159 of 200 |
| `cheat-no-self-cover` | 153 of 200 |
| `cheat-drop-unripe` | 77 of 200 |
| `cheat-one-sweep` | 34 of 200 |
| `cheat-latest-first` | 1 of 181 generated, pinned by `rival-parcels` |
| `cheat-past-must-cover` | 2% generated, pinned by `past-entry-not-asked` |
| `cheat-drop-doomed`, `cheat-gone-needs-nothing` | 7% each, both pinned by a named feed |
| reference against the sealed second reading | 531 feeds, 14767 rows, no mismatch |

Four cheats sit in single-figure percentages of the generated space. Each is pinned by a
named feed, so each scores 0 every time rather than by luck, and a submission that fails one
fails a feed with a name on it. They are fences, not axes: do not read those percentages as
difficulty, and do not delete the named feeds that carry them.

## Traps already hit, so nobody hits them again

- Two things written as variants scored 0 and were right to: `past-must-cover` and
  `drop-doomed`. Settling makes both of them genuinely different rules, not different code.
  Both ship as cheats with `past-entry-not-asked` pinning them.
- One thing written as a cheat scored 1 and was promoted: `ok-number-apply`. Applying by
  higher number is provably the same as applying by descent, because `ripe` has already ruled
  out the branches.
- `ok-reverse` passed the host emulation and failed the container. The pass is NOT confluent:
  putting a version of a setting up where the worker had none puts the other branch out of
  reach for good, so two ready parcels can compete. The rule is now stated (earliest handed
  wins), `rival-parcels` pins it, and the reverse walk is a cheat.

## Gates not run

- The three-agent local probe. This is the only local gate that measures what the easiness
  probe rejects for, and it is the first thing to run on this task.
- The apt layer: neither image installs anything, so nothing there is exercised.
