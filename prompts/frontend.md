# Software / Frontend - scroll anchoring

Paste the block below as the first message of a fresh task-authoring session. It supplies
the seed and the distinctness constraints; `NEW-TASK-PROMPT.md` supplies everything else.

---

```text
Build one Frontier Bench task in this repository, filed under category `Software`,
subcategory `Frontend`. Follow `NEW-TASK-PROMPT.md` as the build contract in full: read
`docs/INSTRUCTION-CONTRACT.md` first, then `AGENTS.md`, then `docs/ORIGINALITY.md`,
`docs/DIFFICULTY.md`, `docs/QUALITY-REVIEW.md` and `docs/RULES.md`. Begin immediately, own
every part of the bundle, and ask me only when two materially different meanings of the
task remain after investigation. Never spawn subagents.

This message gives you the seed. It is a starting point with a planning attack already in
it, not a specification: deepen it where the measurements say it is thin, and replace it if
either record below will not reach its floor.

## The seed

Substrate: the layout and scrolling half of a view toolkit. A document is a tree of boxes
with heights; a frame applies a batch of mutations - a box resolves to its real height, a
row expands, a node is inserted or removed, a header becomes stuck or unstuck - and then
the view is painted.

Mechanism: keep the content the user is looking at where it is. Each frame selects an
anchor from the boxes intersecting the viewport under stated eligibility rules, and after
the mutations are applied the scroll offset is adjusted so the anchor stays at the same
position. Suppression is stated too: an explicit scroll in the same frame, or a mutation
inside a box marked as excluded, turns anchoring off for that frame.

Graded output: per frame, the scroll offset after the adjustment and the identity of the
anchor used, or the reason anchoring was suppressed.

## The planning attack

The first plan a frontier agent forms: before applying the mutations, record the first box
intersecting the viewport and its offset from the viewport top; after applying them, set
the scroll offset so that box lands back at the same place. It is the plan every
"maintain scroll position" answer online gives, and it holds for every simple case.

The rule that breaks it: eligibility is evaluated on the box as it stands after the
mutations, not before. A box that becomes out of flow, or is removed, or falls inside an
excluded subtree, disqualifies the anchor - and the fallback is not the recorded offset but
the anchor's nearest eligible ancestor, whose own position moved for different reasons.

The second discovery, which forces a replan rather than a patch: the adjustment changes
which sticky boxes are stuck, and a sticky box that becomes stuck changes the effective top
of the viewport, which changes where the anchor is supposed to land. A single pass is
wrong; the frame settles, with a stated iteration cap and a stated answer when it does not
converge. An implementation built as record-then-restore has to become a fixed point over
the frame.

The interacting pair to build the difficulty on: the eligibility rule decides which box is
the anchor, and the sticky rule decides what "the same position" means for it. Settle
either alone and the other's answer changes.

The late case: a frame where the anchor is eligible, the adjustment unsticks a header, the
unsticking makes the original anchor ineligible, and the fallback ancestor is itself inside
the mutation. Ordinary frames never reach the second iteration.

## Distinctness

Stay off the crowded Frontend list in `docs/ORIGINALITY.md`: no focus management or focus
traps, no virtual-DOM reconciliation or keyed children, no undo and redo stacks, no form
validation state machine, no router, no drag and drop, no optimistic update with rollback.
There is no event handling in this seed at all, and no widget state - only geometry that
settles - which is what keeps it clear of the label's usual neighbourhood.

Before anything else, read `authoring/submissions.toml`. `focus-return-point` is already
there under this label. Do not reuse its substrate or any of its tags -
`focus-management`, `modal-dialogs`, `tree-mutation`, `deferred-resolution`. A second task
about where something lands after a tree mutation will read as the same task however
different the rules are, so keep the anchor question geometric and say so in the record.

Write `mechanism.sentence` in the originality record before you write anything else, and
hold it to the twin test: if that sentence could be the abstract of a tutorial, or could
describe a task someone else plausibly submitted this month, change the design.

Substrate roster, one to a task:
- scroll anchoring under mutations and sticky boxes (the seed);
- text composition: an input method's pre-edit span, its interaction with autocomplete
  replacement, selection anchoring and how undo groups a composition;
- a resize observation loop that must settle within a stated depth, reporting which
  observers are notified in which pass and which are dropped;
- selection and range normalization across nested editable regions with boundaries that
  move under the selection.

## Gates before any code

1. Copy `template/originality.toml` to `authoring/<slug>/originality.toml`, answer every
   field, and run `python tools/originalitycheck.py <slug>`. Floor 90, no hard stop.
2. Copy `template/difficulty.toml` to `authoring/<slug>/difficulty.toml`, answer every
   field, and run `python tools/difficultycheck.py <slug>`. Band 95 to 100, no hard stop.
3. Record every attempt's score and what changed between attempts in `tasks/<slug>/STATE.md`.

Neither record is tuned to its number. If a record will only reach its floor by padding,
the design is what changes.

## Shape

Aim inside the retained band: 229 to 544 environment Python lines, 1 to 7 editable files,
110 to 424 reference lines, `[agent] timeout_sec = 14400`, `gpus = 0`, and an honest solve
estimate of 1 to 3 out of 8 - never 0, never 8. Re-run both checkers at Stage 7, where they measure the built tree instead of reading
the record.
```

---

## Why this seed is off the crowded centre

Frontend submissions cluster on component behaviour, because that is what tutorials teach.
Scroll anchoring is a browser-internal settlement with a published specification that
almost nobody implements, and the specification deliberately leaves the sticky interaction
and the iteration behaviour to the implementation - so retrieval hands an agent the
vocabulary and none of the answers, which is exactly the search-test position
`docs/DIFFICULTY.md` asks for.

## What to check before writing code

- Grade geometry, not rendering. The output is offsets and identities; keep floats out of
  it entirely and work in integer units so the verifier can compare exactly.
- Prove the iteration is reachable: measure how many frames in the generated population
  need a second pass. If it is a handful, shape the generator around sticky boxes until it
  is not.
