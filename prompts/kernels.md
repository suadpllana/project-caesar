# ML / Kernels - a warp execution model

Paste the block below as the first message of a fresh task-authoring session. It supplies
the seed and the distinctness constraints; `NEW-TASK-PROMPT.md` supplies everything else.

---

```text
Build one Frontier Bench task in this repository, filed under category `ML`, subcategory
`Kernels`. Follow `NEW-TASK-PROMPT.md` as the build contract in full: read
`docs/INSTRUCTION-CONTRACT.md` first, then `AGENTS.md`, then `docs/ORIGINALITY.md`,
`docs/DIFFICULTY.md`, `docs/QUALITY-REVIEW.md` and `docs/RULES.md`. Begin immediately, own
every part of the bundle, and ask me only when two materially different meanings of the
task remain after investigation. Never spawn subagents.

This message gives you the seed. It is a starting point with a planning attack already in
it, not a specification: deepen it where the measurements say it is thin, and replace it if
either record below will not reach its floor.

## The seed

Substrate: a model of a single multiprocessor, driven by kernels written in a small
instruction language - arithmetic, predicated branches, shared-memory loads and stores
with computed addresses, and barriers. A launch configuration fixes the block size, the
warp width, the number of banks and the bank width. There is no GPU anywhere in the task:
the environment is a simulator and `gpus = 0`.

Mechanism: report what the hardware model does with a kernel. Threads of a warp issue
together under an active mask; divergent branches are serialized and reconverge at the
immediate post-dominator rather than at the textual end of the branch; a barrier is
reached by whichever threads are active, and the stated rule says what happens when that
is not the whole block; a shared-memory access costs cycles according to how its addresses
fall across banks, with identical addresses broadcasting and an access wider than the bank
width splitting under a stated rule.

Graded output: per barrier, the set of warps that arrived and the step they were released;
per shared-memory instruction, the number of cycles it cost; and, when the kernel cannot
finish, the deadlock report naming the barrier and the warps stuck on it.

## The planning attack

The first plan a frontier agent forms: simulate each thread independently, count a
conflict whenever two threads touch the same bank, and treat a barrier as a rendezvous for
all threads of the block. Straight from the programming guide's mental model.

The rule that breaks it: the cost is per access phase of a warp under its active mask, not
per pair of threads. Broadcast collapses identical addresses to one cycle; a masked-off
thread costs nothing; and a thread-independent simulation has already thrown the mask away
by the time the cost is computed.

The second discovery, which forces a replan rather than a patch: the reconvergence point
is a property of the control-flow graph, not of the source order, and a barrier inside
divergent control flow changes which threads are active after reconvergence - so the
active mask at issue time, which the cost depends on, depends on a graph the simulator has
to build first. An implementation written as an interpreter over the instruction list has
to be rebuilt around a reconvergence structure.

The interacting pair to build the difficulty on: the reconvergence rule decides the active
mask, and the banking rule prices an access against that mask. Settle either alone and the
other's answer changes.

The late case: a kernel where a predicated store inside a divergent branch touches the same
bank as a load after reconvergence, and the whole warp being predicated off is the only
thing separating a costly access from a free one.

## Distinctness

Stay off the crowded Kernels list in `docs/ORIGINALITY.md`: no tiled GEMM, no flash or
fused attention, no warp reduction or prefix scan as the mechanism, no fused normalization,
no occupancy tuning, no sparse formats. Writing a fast kernel is the crowded task; this one
never multiplies anything - it reports what a machine model does.

Before anything else, read `authoring/submissions.toml`. No task under this label is in the
ledger yet, so the neighbourhood to check is the public one: bank conflicts and divergence
are taught in every CUDA course. What is not taught is the interaction - the mask at issue
time pricing the access - and the record has to say that in `collision.departure`, because
a reviewer will otherwise read the tags and see a course exercise.

Write `mechanism.sentence` in the originality record before you write anything else, and
hold it to the twin test: if that sentence could be the abstract of a tutorial, or could
describe a task someone else plausibly submitted this month, change the design.

Substrate roster, one to a task:
- a warp execution model: reconvergence, barrier participation, bank conflicts (the seed);
- an asynchronous copy pipeline with commit groups and waits, where a stage's data is
  visible only after the stated group has been waited on and a wait may cover several;
- settling how many blocks are resident given register and shared-memory allocation with
  stated granularity rounding, and which launch is rejected outright;
- a tile schedule over a work grid with a stated swizzle, reporting which tiles land on
  which partition and where the schedule leaves a partition idle.

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

A Kernels task usually means "make this fast", which needs a GPU, a benchmark and a
tolerance - three things that make a verifier fragile and a submission look like every
other one. Modelling the machine instead keeps the label honest, grades exactly, runs on
`gpus = 0`, and moves the difficulty to the place the courses skip: the interaction between
the active mask and the memory system.

## What to check before writing code

- The instruction language is part of the contract. Every opcode, every rule about
  predication and every banking constant belongs in `instruction.md`, or the verifier
  grades something the text never states (`docs/INSTRUCTION-CONTRACT.md`).
- Keep it deterministic and integral: cycles are counts, never estimates. If any graded
  number needs a tolerance, the model is under-specified.
- Check the label fits what you built. If the graded work turns into scheduling or memory
  bookkeeping with no machine model left, it is an Algorithms task wearing a GPU costume,
  and the category check in the quality review reads the graded work, not the story.
