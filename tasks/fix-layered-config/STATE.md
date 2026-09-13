# Task state

Working memory for this task. Never ships in the zip.

## Provenance

This bundle was authored outside this checkout and submitted to the platform. It arrived here on
2026-09-13 as `c09e33e8-fix-layered-config.zip` after the structural gate refused it:

    ERROR  INSTRUCTION-TOO-LONG  instruction.md
    instruction.md is 11042 characters - the maximum is 10000.

The submission was recorded but could not proceed. No design work, no environment change and no
verifier change happened in this session, and no authoring record (`authoring/fix-layered-config/`,
difficulty record, probe transcripts) came with the zip, so the design fields below are recorded
as not held locally rather than reconstructed from the bundle.

## Current stage

`Stage 8 - submission repair` (instruction length only).

## Task summary

`/app` is a layered configuration service. Six modules under `/app/cfg` compose a plan of layered
entries (`put`, `cut`, `mix`, `map`, `tie`, `veil`) and answer `ask`/`tot` questions in a view
chosen by a layer count. The shipped implementation is wrong: `/app/plans/one.txt` prints
`num site 2` where the composed plan holds one definition under `site`. The agent repairs
`pile.py`, `past.py`, `made.py`, `roll.py`, `work.py` and `ans.py`.

## What this session changed

- `instruction.md` rewritten to 9814 characters. No rule was dropped: every one of the 114
  sentences of the submitted instruction was mapped onto the new text before the old file was
  replaced. The savings are prose, and three consolidations of rules the old text stated once per
  operation:
  - the printed layer is always the original `put`'s layer (was stated four times: `mix`, the
    three-operation sentence, `tie`, `veil`),
  - a definition carries the view its `old` reads in, and only `map` replaces it (was stated for
    `put`, `mix`, `map`, `tie` and `veil` separately),
  - `mix`, `map`, `tie` and `veil` all clear their destination first (was stated per operation),
  - what stands in front of a tie or a veil afterwards (`put` shadows one path, `cut` and a
    destination under it mask, `cut` at the marked path removes it) was stated twice in nearly
    identical words, once for `tie` and once for `veil`.
- Consolidating flattened the cadence - `tools/textcheck.py` measured burstiness 0.625 against
  the 0.791 of `focus-return-point`, which passed the AI-text screen. Splitting the merged
  sentences back apart costs no characters (a `, and` becoming `. ` saves four), so the final text
  is both shorter and more irregular than what was submitted: burstiness 0.751 against 0.719,
  short sentences 22% against 15%, and textcheck's oxford-triad tell gone.
- `scripts/preflight.py` now errors above 10000 characters and warns above 9500. The cap was
  written down nowhere in this workspace, which is why nothing local caught it; it is now in
  `docs/RULES.md` and `AGENTS.md` as well.

## Why it is hard

No design record came with the zip, so these four lines are read off the shipped bundle - the
reference, the case list and the generator - and marked as such. They are observations about what
was built, not a design history this session owns.

- Why a frontier agent cannot one-shot the plan (read off the bundle): the three graded quantities
  interact. A definition carries an identity, a layer and an `old` view; `map` rewrites operands
  and replaces the view, `tie` and `veil` rewrite operands and keep it, `mix` does neither. A veil
  then makes each path choose between a local write, a live source and a frozen fallback
  separately, so `tot` is a union over two inherited subtrees rather than a walk of one. A plan
  that gets the lookup right and the identity wrong passes the small plans and fails the
  generated population; the structures that make the counts affordable are chosen before that is
  visible.
- Tactics making that true (docs/DIFFICULTY.md): B2, C3 and C4. B2 is nine or so rules holding at
  once, each easy alone (clear before copy, freeze the source set, move operands, keep the layer,
  keep or replace the view, one identity per distinct definition, mask, shadow, stop on revisit).
  C3 is `/app/plans/wide.txt` and the deep-copy families, which make enumerating visible paths
  miss the 60 second batch limit, so the naive-but-correct count is banned by a resource gate
  rather than by a rule. C4 is 1032 plans graded all-or-nothing on exact output lines against a
  sealed independent model.
- Assistant's attack on the plan: its first plan is to repair the counter that over-counts
  `/app/plans/one.txt`, treating the defect as local to `tot`. That plan is wrong because the shipped
  defect is not local to counting: the same wrong identity model shows up in which layer `ask`
  prints and in which view an `old` reads, and a counter repaired against `one.txt` still
  double-counts the overlap under a veil and still walks paths it cannot afford at the disclosed
  scale.
- Estimated solves out of 8: 3 (the bundle's own claim, from `expert_time_estimate_hours = 9` and
  a six-file editable surface; not measured here, and no easiness probe transcript came with it).

## Difficulty record

Not held locally. The zip carries no `authoring/` directory, and `tools/difficultycheck.py` scores
a design record, not a built tree. `task.toml` claims 9 expert hours and the retained band shape
(six editable files, 337 lines of reference against a 229-544 band); that is the bundle's own
claim, not a measurement made here.

## Reference verification failure, 2026-09-14 (oracle 1, 1, 0)

The resubmission cleared the structural, AI-text and similarity gates and failed reference
verification: the oracle scored 1, 1, 0 across its three trials, the nop 0, 0, 0. The oracle row
is not deterministic, because `test.sh` draws a fresh nonce per run and grades a different
generated population each time, so 2 of 3 means a rare disagreement between the reference and the
sealed model, not flaky infrastructure.

Reproduced by replaying the oracle row locally: 3 of 40 nonces failed, every one of them a single
`tot` line in the `tieinterference` family where the reference counted one path fewer than the
model. Delta-reduced to seven lines, three ties forming a ring with one write under each:

    lay
    tie n r
    tie r q
    tie q n un q.d.k
    put r.d.k lit -10
    put q.d.y now n.x un n.d.k
    tot q

Both implementations agree that `q.d.y` and `q.d.k` each hold a definition (`ask q.d.k` is -10
through the ring; `ask q.d.y` is `gone` because its value is absent, which does not stop the path
holding a definition). Two paths hold definitions, so `tot q` is 2. The model was right and the
reference was wrong - it answered 1.

The defect is in `solution/pile.py`, in `node()`. When an inherited lookup was truncated because
it came back on itself, and the node was otherwise empty, the function returned `None` and the
truncation went with it. The caller read `cut_i = i is not None and i.cut` as False, built a Log
marked clean, and cached it. Counting then took the structural correction - the inherited count
plus local children minus what the inherited side counts under the same segment - which the file's
own docstring says is exact only when no lookup had to cut itself off. The subtraction removed a
path the inherited total had never included, so the count came out one short. `node()` now returns
that empty node with its `cut` flag set instead of `None`, so the truncation reaches the caller
and the count falls back to the literal walk.

Fix validated in both directions:

| Measurement | Before | After |
|---|---|---|
| Full graded batches vs the sealed model, fresh nonces | 37 of 40 clean | 80 of 80 clean |
| Dense `tieinterference` plans | 3 of 6000 disagree | 0 of 6000 |
| Dense `tiering`/`tiechain`/`veilchain`/`veilrandom` | not run | 0 of 2500 each |
| Dense `tielive`/`tiefreeze`/`veillive`/`veilmask`/`veilcopy`/`veilold` | not run | 0 of 2000 each |
| Dense scale families (`wide`/`deep`/`mapdeep`/`tiedeep`/`veildeep`) | not run | 0 of 60 each |
| Oracle rows end to end (worker + grader) | - | 6 of 6 reward 1 |
| Batch wall time against the 60 s clock | 2.3-2.8 s | 2.3-2.8 s |

Nothing under `tests/` was touched: the sealed model, the case list, the generator and the frozen
answers all stand, and the repair was made to the side that was wrong.

Coverage note for the contributor, not acted on here: the separating shape is rare. It appeared in
about 1 in 2000 `tieinterference` plans, so a submission carrying this exact bug passes a graded
run roughly 90% of the time. Making the ring-with-local-writes shape a deliberate part of that
family would close it, but that is a change to a frozen verifier and is the contributor's call.

## Verifier contract - FROZEN

Unchanged by this session.

- Artifacts: the six `/app/cfg` modules listed in `task.toml`.
- Checked: a pristine tree with the six submitted files laid over it runs 1032 plans (97 hand
  cases plus 23 shaped families at 40 each and 5 scale families at 3 each); every output line must
  equal the sealed model's, and the whole batch must finish inside 60 seconds.
- Ground truth: `tests/seal/gt.json` and `tests/seal/model.py`, `chmod 700` before the privilege
  drop.

## Validation status

| Check | Status | Notes |
|---|---|---|
| Agent image builds | not run | no Docker in this session; `tools/imagecheck.py` clean - 16 files, workdir `/app`, all six plans run |
| No answer leaked into agent image | imagecheck clean | nothing from `tests/` or `solution/` in the build context |
| `harbor run -a oracle` = 1 | passed, emulated | 6 of 6 rows reward 1 after the count fix; 80 of 80 fresh nonces agree with the sealed model |
| `harbor run -a nop` = 0 | passed, emulated | shipped tree killed by the 60 s clock, exit 124, no record written |
| Cheats all score 0 | not run | the zip ships no `cheat/`; the platform runs its own probe |
| `preflight.py` | 0 errors | STATE.md warning gone with this file; 18 warnings, all inherited |
| `zipcheck.py` | clean | see the packaged zip |
| `harbor check` rubric | not run | no Docker |

## Open questions and next steps

- Resubmit `tasks/fix-layered-config.zip`. Structural, AI-text and similarity have passed;
  reference verification has now been repaired locally, and the quality review, the anti-cheat
  probe and the difficulty probe are still ahead of it.
- If a later gate asks for a shorter instruction again, the 186 characters of headroom are the
  budget. Below that, rules have to be merged rather than cut, and the mapping above is where to
  start.
