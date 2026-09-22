# ML / Training - exact resume of a packed, sharded sampler

Paste the block below as the first message of a fresh task-authoring session. It supplies
the seed and the distinctness constraints; `NEW-TASK-PROMPT.md` supplies everything else.

---

```text
Build one Frontier Bench task in this repository, filed under category `ML`, subcategory
`Training`. Follow `NEW-TASK-PROMPT.md` as the build contract in full: read
`docs/INSTRUCTION-CONTRACT.md` first, then `AGENTS.md`, then `docs/ORIGINALITY.md`,
`docs/DIFFICULTY.md`, `docs/QUALITY-REVIEW.md` and `docs/RULES.md`. Begin immediately, own
every part of the bundle, and ask me only when two materially different meanings of the
task remain after investigation. Never spawn subagents.

This message gives you the seed. It is a starting point with a planning attack already in
it, not a specification: deepen it where the measurements say it is thin, and replace it if
either record below will not reach its floor.

## The seed

Substrate: the input half of a training run, with no model in it. Documents of varying
length are drawn from several sources under per-source quotas, packed into fixed-length
blocks with a stated rule for splitting a document across blocks and for what the
remainder of a block carries, sharded across ranks, and consumed in microbatches that
accumulate into an optimizer step.

Mechanism: resume. A checkpoint is written between microbatches and records what the
trainer actually knows: blocks emitted per rank, the step and microbatch index, the source
quota counters and a seed. After a resume the block stream per rank has to continue
exactly as it would have without the interruption - same documents, same split points,
same order, same shard assignment.

Graded output: per rank, the blocks emitted after the resume - the document ids and the
byte ranges each block carries, in order - and the step and microbatch each belongs to.

## The planning attack

The first plan a frontier agent forms: reseed the sampler from the recorded seed, replay
the draw sequence, skip the documents already consumed, and continue. It is what every
resumable-dataloader write-up describes and it works whenever a block is one document.

The rule that breaks it: the packer's remainder is carried, and the checkpoint counts
blocks rather than documents, so "documents already consumed" is not a quantity the
checkpoint holds. The resume point can fall inside a document that was split, and the
partial block has to be rebuilt from the recorded remainder rather than redrawn - which
means the draw sequence cannot simply be replayed forward.

The second discovery, which forces a replan rather than a patch: the quotas are evaluated
per optimizer step, not per draw, and they are global across ranks while the draws are
local. A rank resuming mid-step must compute admission from the step's totals, which
include microbatches its own shard never saw - so a per-rank replay is wrong even when its
own stream is reproduced exactly. The implementation has to be rebuilt around the step as
the unit of state, with the shard as a projection of it.

The interacting pair to build the difficulty on: the packing rule decides where a document
is split and therefore how many blocks a step consumes, and the quota rule decides which
documents may be drawn in that step. Each changes the other's answer at exactly the
boundary where a resume lands.

The late case: a resume whose recorded remainder belongs to a document from a source whose
quota is exhausted in the step being resumed - the document must still be finished, and
the next draw must not come from that source.

## Distinctness

Stay off the crowded Training list in `docs/ORIGINALITY.md`: no mixture-of-experts
routing, no gradient accumulation arithmetic as the mechanism, no learning-rate schedule,
no mixed precision or loss scaling, no all-reduce or sharding of parameters, no early
stopping. There are no gradients in this seed at all - the graded work is entirely about
which bytes reach which rank in which step.

Before anything else, read `authoring/submissions.toml`. `expert-defer-shed` is already
there under this label. Do not reuse its substrate or any of its tags -
`sparse-expert-routing`, `token-dispatch`, `buffer-capacity-sizing`,
`gradient-accumulation`, `expert-parallelism`, `load-balance-accounting`. Note that it also
divides work across microbatches of a step; say in the record what makes this a different
task, and if you cannot say it in twenty concrete words, take another substrate.

Write `mechanism.sentence` in the originality record before you write anything else, and
hold it to the twin test: if that sentence could be the abstract of a tutorial, or could
describe a task someone else plausibly submitted this month, change the design.

Substrate roster, one to a task:
- exact resume of a packed, sharded sampler from a mid-step checkpoint (the seed);
- re-sharding at resume: the world size changed, and every rank's stream must be derived
  from a checkpoint written under the old one without replaying or dropping a document;
- loss masking and token accounting across packed documents, where a stated budget decides
  which tokens count and a document straddling two blocks counts once;
- a curriculum that admits a source only after a stated step, with a rule for what happens
  to a partially drawn document when the admission changes underneath it.

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

Training submissions reach for the optimizer, because that is where the published
difficulty is. Everyone who has actually run a long job knows the resume is where the
week goes, and the reason it is hard - a checkpoint records what the trainer knows, not
what the sampler needs - is folklore rather than documentation. Libraries publish
"stateful dataloader" APIs and leave the packing interaction to the user, which is the
gap this seed grades.

## What to check before writing code

- Determinism is the whole contract: pin every seed and every iteration order, and make
  the verifier compare the block stream exactly. No sampling in the verifier, none in the
  environment.
- Keep gradients and model code out of the tree entirely. They are provenance leaks
  wearing an ML costume: nothing graded depends on them, and they invite the agent to look
  for the difficulty in the wrong module.
