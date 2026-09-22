# ML / Inference - batch composition under an adapter bank

Paste the block below as the first message of a fresh task-authoring session. It supplies
the seed and the distinctness constraints; `NEW-TASK-PROMPT.md` supplies everything else.

---

```text
Build one Frontier Bench task in this repository, filed under category `ML`, subcategory
`Inference`. Follow `NEW-TASK-PROMPT.md` as the build contract in full: read
`docs/INSTRUCTION-CONTRACT.md` first, then `AGENTS.md`, then `docs/ORIGINALITY.md`,
`docs/DIFFICULTY.md`, `docs/QUALITY-REVIEW.md` and `docs/RULES.md`. Begin immediately, own
every part of the bundle, and ask me only when two materially different meanings of the
task remain after investigation. Never spawn subagents.

This message gives you the seed. It is a starting point with a planning attack already in
it, not a specification: deepen it where the measurements say it is thin, and replace it if
either record below will not reach its floor.

## The seed

Substrate: the admission half of a serving stack. Requests arrive naming an adapter; the
server holds a bank of a fixed number of adapter slots; bringing an adapter in occupies its
slot for a stated number of steps before it can serve, and during those steps the slot
serves nothing. Adapters have ranks, and a batch may mix ranks only within a stated width.

Mechanism: decide, step by step, which requests form the batch. The rules interact: a
resident adapter may not be evicted while any in-flight request holds it; a swap may only
be started when the bank it produces admits at least one runnable request at the step the
swap completes; and no request may wait longer than a stated age bound, measured from
admission.

Graded output: per step, the requests in the batch and the swaps started or completed, and
per request the step it first ran and the step it finished.

## The planning attack

The first plan a frontier agent forms: each step, take the oldest waiting request, batch
everything else that shares its adapter and fits the width, and evict the least recently
used adapter when a swap is needed. Greedy, per step, exactly what a scheduler write-up
suggests.

The rule that breaks it: a swap is not free and not instantaneous, so a greedy pick can
leave the bank with every slot either held by an in-flight request or mid-swap, and
nothing runnable at the next step. The stated rule forbids starting a swap that leaves the
bank in that state, which means the scheduler has to reason about the step the swap
completes, not the step it starts.

The second discovery, which forces a replan rather than a patch: the age bound is measured
from admission, so a request that ages out forces a swap that may preempt a partially
decoded request - and a preempted request's state is either kept, which charges the bank,
or dropped, which restarts it and resets nothing about its age. A scheduler written as a
sequence of independent per-step decisions cannot express that choice; the step has to
carry forward what it committed to.

The interacting pair to build the difficulty on: the eviction rule decides which adapters
can leave the bank, and the age bound decides which requests must run - and the second can
demand a swap the first forbids, so the specification's tie-break becomes the whole
answer.

The late case: two requests of different ranks age out in the same step, where serving
either one alone is legal and serving both requires a width the bank cannot give, so the
tie-break decides who waits and the other request's deadline then falls inside a swap.

## Distinctness

Stay off the crowded Inference list in `docs/ORIGINALITY.md`: no KV cache or paged
attention as the mechanism, no continuous-batching arithmetic for its own sake, no
speculative decoding, no detokenization or stop sequences, no sampling, no
grammar-constrained decoding, no quantization. Nothing in this seed decodes anything -
there are no tokens in the graded output at all.

Before anything else, read `authoring/submissions.toml`. `token-seam-emit` is already
there under this label. Do not reuse its substrate or any of its tags - `byte-level-bpe`,
`incremental-detokenization`, `stop-sequences`, `utf8-boundaries`, `streaming-responses`.
Reference-counted residency also appears in `publish-settle-order`; if your design leans
on refcounted teardown, say in the record what makes it a different question, or move the
weight onto the age bound instead.

Write `mechanism.sentence` in the originality record before you write anything else, and
hold it to the twin test: if that sentence could be the abstract of a tutorial, or could
describe a task someone else plausibly submitted this month, change the design.

Substrate roster, one to a task:
- batch composition under an adapter bank with swap latency and an age bound (the seed);
- deciding which requests may share a captured execution graph given shape buckets, where
  capturing costs steps and a bucket may be retired while requests still hold it;
- admission under a shared token budget where a prompt may be truncated by a stated rule
  and truncation changes which budget class the request lands in;
- sharing cached prefix blocks between requests that fork, with copy-on-write and a stated
  rule for which fork pays when a shared block is extended.

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

Serving submissions go to the cache and the decode loop, because those are the parts with
famous papers. Multi-adapter residency is a production problem with a thin literature: the
published work measures throughput, and the rules that decide a batch - who may be evicted,
when a swap may start, what a deadline does to a partially decoded request - are settled
inside each server's scheduler and written down nowhere as a set.

## What to check before writing code

- Grade the schedule, not a score. Per-step batches and swap events compare exactly; a
  throughput number invites a tolerance and a tolerance invites a cheat.
- The age bound is the load-bearing rule, so measure what a wrong reading of it moves. If
  ageing out never collides with a forbidden eviction in the generated population, shape
  the population until it does.
