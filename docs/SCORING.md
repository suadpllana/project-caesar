# The difficulty score

A single number the contributor can watch move as they adjust the task. Its only job is to make
difficulty changes **measurable and directional**, so that when the pipeline reports 8-of-8 or
0-of-8 the contributor can act and see whether the action worked.

It is not a prediction of the solve rate, and it is not comparable between tasks. It is an anchor
plus a delta, for one task, over time.

## The rule

```
reported score = anchor + (rubric now - rubric at anchor)
```

- **The anchor is 50**, set at the first complete submission and approved by the contributor.
- Every later report is that anchor plus however much the rubric moved.
- **Re-anchor when the pipeline returns real data** — that is the only ground truth available.

Scoring must take **seconds**: the deterministic half comes from `preflight.py`, the judged half
from the assistant scoring ten rows it already has the evidence for. No extra harbor runs, no
rebuilds, no subagents. If scoring starts costing minutes, it is being done wrong.

## The rubric — ten rows, 0-10 each

Score from evidence in the bundle, not from intent. "I meant it to be hard" is 0.

| # | Row | 0 | 10 |
|---|---|---|---|
| 1 | **A1 deviation** | spec matches what every source says | required behaviour contradicts the convention all retrieval returns |
| 2 | **A2 unnamed concept** | the term of art is in the instruction | described operationally; forming the search query is itself the hard step |
| 3 | **A3 technique conflict** | one textbook method satisfies everything | constraints no single known technique meets; a hybrid must be synthesised |
| 4 | **B1 distribution** | readable in two tool calls; facts adjacent | tree exceeds what fits in attention; the plan needs facts correlated across it |
| 5 | **B2 rule interaction** | rules independent and separately checkable | getting one right changes what "right" means for another, or no per-rule feedback |
| 6 | **C1 both-side fencing** | only the failure side tested | must-fail and must-still-work both enumerated; overshooting fails too |
| 7 | **C2 oracle denied** | a standard tool or "run it and see" confirms correctness | wrongness invisible in casual testing; only the verifier's constructed cases reveal it |
| 8 | **C3 resource gate** | any correct implementation passes | a naive-but-correct implementation fails a real bound |
| 9 | **C4 adversarial grading** | a few fixed cases, loose tolerance | seeded-random over the space plus enumerated corners; all-or-nothing |
| 10 | **Leak audit + guard** | unused affordances, manifests, self-labelling data, a shipped oracle, free join keys, wide edit surface | nothing lets an agent discover, name or verify a mechanism without reasoning; artifacts narrow |

**Solvability is a gate, not a row.** If the reference solution does not pass reliably, there is no
score — report "unscoreable until the oracle passes every run" and fix that first.

## Setting the anchor honestly

The anchor is 50 whatever the rubric totals, because it measures movement rather than absolute
difficulty. But do not let that hide a thin task: **when you set the anchor, say how many rows
scored 0, and what that implies.** A task can total 7 out of 100 and still be reported as 50 — the
contributor would then submit it, come back with 8-of-8, and have lost a whole cycle learning what
you already knew.

So the anchor report carries a one-line reading of the rubric's shape:

```
Difficulty: 50 points (anchor).
Rubric shape: 6 of 10 rows score 0 (A1, A2, A3, B1, B2, C3) - the task currently rests on
verification alone. I would expect this solved most times out of 8. Worth strengthening
before submitting.
```

Versus a healthy one:

```
Difficulty: 50 points (anchor).
Rubric shape: every prong carries something, weakest row is C3 (no resource bound).
```

Three or more rows at zero, or a whole prong empty, is worth saying out loud. That costs the
contributor one line and can save them an entire submission cycle.

## Reporting

Minimal. One line, plus at most three naming what moved:

```
Difficulty: 80 (+30 from the 50 anchor)
  B1 4 -> 8   environment now spans 40 modules; the join key is derived, not shipped
  C2 2 -> 7   the reference tool no longer agrees with the spec on voided fixtures
  leak 6 -> 9 removed store.json and the unused load_void()
```

Never a paragraph. The contributor wants the number and the reason, not an essay.

## Re-anchoring on pipeline feedback

The anchor is a guess until the pipeline scores the task. When it does, correct it — this is the
one place real data exists, and it makes every later delta more honest:

| Pipeline result | What it means | New anchor |
|---|---|---|
| 7-8 of 8 | the anchor was far too high | 20 |
| 5-6 of 8 | slightly too high, but in band | 40 |
| 1-4 of 8 | anchor was about right, task is in band | keep 50 |
| 0 of 8 | the anchor was too low, or the task is unverifiable | 85 |

State the correction plainly: *"the pipeline solved it 8 of 8, so our 50 was really about 20 — your
current version scores 55 on the same rubric."*

After re-anchoring, aim for the **upper half of the in-band zone, roughly 55-70**. That follows
from the design aim in `docs/DIFFICULTY.md`: you are designing for 1 solve of 8, the hard edge,
because realized difficulty drifts *down* between design and probe. Below 40 the task is likely
solved every time; above 80 it risks zero solves, which is rejected the same way. These bands are
heuristics and get better as results accumulate — log each task's anchor, final score and pipeline
result in `docs/QUALITY-REVIEW.md` so the mapping earns its calibration instead of assuming it.

## When the pipeline rejects: what to change

**Solved 7-8 of 8 — too easy.** Find the row scoring lowest and fix that prong. In order of how
often it is the culprit: run the leak audit first (row 10) — usually the mechanism existed and was
leaked, which is cheaper to fix than to redesign; then C2 (something confirmed the plan early);
then A1 (the spec matched the literature, so retrieval worked).

**Solved 0 of 8 — rejected as unverifiable.** This is almost never "too hard" in the intended
sense. The usual causes, in order: the verifier tests something the instruction never stated; the
must-still-work side was never specified, so every attempt overshoots; a resource bound no real
implementation meets; or an instruction so terse the goal is ambiguous. **The fix is stating more,
never weakening the verifier** — D2 still holds. Raising row 6 (both-side fencing) and clarifying
the goal usually recovers the task without losing difficulty.

## What this score cannot do

It cannot predict the solve rate, cannot be compared across tasks, and rewards the appearance of
the rubric as much as the substance — so treat it as a diagnostic, never a target. A score that
rises because a leak was removed is real; a score that rises because the instruction got vaguer is
a rejection waiting to happen, since the pipeline explicitly refuses tasks that are hard through
ambiguity.
