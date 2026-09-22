# One seed prompt per label

`NEW-TASK-PROMPT.md` is the build contract: what the session reads, which gates it runs,
what it owns, and what it may not ask the contributor to decide. It does not choose the
idea. These files do, one per label a Software or ML task may be filed under, and the idea
is where both gates that actually reject tasks are won or lost:

- **the similarity screen**, which flags a task for grading the same mechanism as someone
  else's submission (`docs/ORIGINALITY.md`);
- **the easiness probe and the `difficult` criterion**, which reject a task whose correct
  plan forms in one shot (`docs/DIFFICULTY.md`).

Each file holds one paste-ready block. Paste it as the first message of a fresh session.
The block names the label, the substrate, the mechanism, the planning attack, the crowded
archetypes to stay away from, and the two records that must be scored before any code is
written. Everything else - stages, isolation, packaging, metadata, the instruction
contract - comes from `NEW-TASK-PROMPT.md`, which the block tells the session to follow in
full.

| label | file | seed mechanism |
|---|---|---|
| Software / Algorithms | [`algorithms.md`](algorithms.md) | inferring the operations a lost span of an append-only log must have contained |
| Software / Databases | [`databases.md`](databases.md) | deferred constraint checking across savepoints and a mid-transaction mode flip |
| Software / Data engineering | [`data-engineering.md`](data-engineering.md) | the minimal recompute plan for a retroactive correction across mismatched grains |
| Software / Frontend | [`frontend.md`](frontend.md) | scroll anchoring: holding a node still while content above it changes height |
| Software / Languages | [`languages.md`](languages.md) | name resolution as a fixed point over globs, re-exports and gated items |
| ML / Training | [`training.md`](training.md) | exact resume of a packed, sharded sampler from a mid-step checkpoint |
| ML / Inference | [`inference.md`](inference.md) | batch composition under an adapter bank with swap latency and an age bound |
| ML / Evaluation | [`evaluation.md`](evaluation.md) | merging partial reruns into one scored report under supersession rules |
| ML / Kernels | [`kernels.md`](kernels.md) | a warp execution model: reconvergence, barrier participation, bank conflicts |

`Software`/`Systems` was retired on 2026-09-10 and has no file. Work that would once have
been filed there goes to the label the graded work actually exercises: a runtime or loader
to **Languages**, a store or commit path to **Databases**, a pipeline or scheduler over
data to **Data engineering**, a settlement or ordering problem to **Algorithms**.

## The rule that makes these reusable

**Never run the same seed twice.** A seed used a second time collides with your own earlier
submission, which is the cheapest flag there is. Every file carries a substrate roster and
the same instruction: check `authoring/submissions.toml`, take a substrate no entry uses,
and add the task to that ledger the day it is submitted. The checker measures substrate
reuse, tag reuse and mechanism-sentence distance against that file, so a repeat is caught
before the build rather than after the review.

Rotate labels too. Nine labels are open; three tasks in a row under one of them raises the
odds of colliding with your own work before anyone else's is considered.

## What a seed does not do

No prompt makes a task pass every gate in one go. What these do is front-load the two gates
that cause rebuilds rather than edits: a design that is flagged or judged easy is a rebuild
from Stage 1, while a thin instruction or a missing artifact parent is an afternoon. Both
records are scored before any environment code exists, and both refuse a padded answer -
`tools/originalitycheck.py` measures tags, substrate and mechanism against everything
already submitted, and `tools/difficultycheck.py` scores the design against the shape of
the tasks that passed. A seed that will not reach both floors is replaced, not defended.

A seed is also not a substitute for the contributor's own work. Where they have a real
incident, a real legacy system or a real artifact near the seed's mechanism, mine that
instead and keep the distinctness discipline: reality supplies twists no roster can
(`docs/DIFFICULTY.md`, "Where real tasks live").
