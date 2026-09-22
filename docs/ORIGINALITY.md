# Distinctness, and the screen that rejects a task for being someone else's

The pipeline screens every submission for similarity against public material and against
tasks already submitted by other contributors (`docs/RULES.md`, "Originality and internet
policy"). The contributor reported on 2026-09-22 that of their last fifteen submissions,
eight came back flagged as similar to a task somebody else had submitted. That is the
majority of a batch rejected on a gate that has nothing to do with how hard the task is,
how complete its contract is, or how clean its bundle is.

A flag is not a plagiarism finding. It is two people, reading the same textbooks and
mining the same well-known systems, arriving at the same mechanism. The counter is not
more careful wording. It is choosing a mechanism that the other twenty contributors this
month are not going to choose, and being able to say in one sentence why.

## What the screen compares

Assume the screen reads the mechanism, not the story. Two tasks collide when a reviewer
holding both would say they grade the same thing, and a reviewer says that when these
surfaces line up:

1. **Mechanism** - the rule family being implemented. Eviction order. Reachability.
   Focus restoration. Commit validation. This is the surface that decides a flag on its
   own: nothing else separates two tasks that grade the same mechanism.
2. **Substrate** - the system the mechanism lives in. A cooperative runtime. A widget
   tree. A commit path. Two tasks in one substrate read as one task even when the rules
   differ, because the shipped tree is what a reviewer sees first.
3. **Graded output** - what the verifier reads, in the shape it reads it. A per-event
   trace, a per-record settled position, a per-step emission.
4. **Failure mode** - the wrong plan the task exists to punish.
5. **Interaction** - the pair of rules whose combination carries the difficulty.

Separate three or more of the five and the tasks are different work. Separate one - the
substrate, usually, which is the easy one to change - and the task is a reskin, which
`docs/RULES.md` rejects by name.

## The crowded archetypes

These are the shapes several contributors reach independently, because the textbook, the
interview question and the course exercise all point at them. The list is per label, for
the labels a `NEW-TASK-PROMPT.md` session may file under.

**Algorithms.** LRU/LFU/ARC caches and TTL eviction; topological sort and dependency
resolution with cycles; interval merging and sweep lines; Dijkstra and A*; union-find
connectivity; diff and longest common subsequence; regular-expression engines; rate
limiters (token bucket, sliding window); string search (KMP, Aho-Corasick, suffix
structures); the classic dynamic-programming set (knapsack, edit distance, coin change,
n-queens, sudoku); priority-queue scheduling and earliest deadline first.

**Databases.** MVCC and snapshot isolation, write skew, SSI; B-trees, LSM trees, SSTables
and compaction; write-ahead logging and ARIES-style recovery; query planning, join
ordering and cardinality estimation; two-phase commit; lock managers and deadlock
detection; incremental view maintenance; buffer-pool replacement.

**Data engineering.** Exactly-once delivery and idempotent dedup; watermarks and
late-arriving events; lakehouse small-file compaction and merge-on-read; schema evolution
and column compatibility; DAG schedulers with retries and backfills; shuffle and partition
skew; change-data-capture ordering from a binlog.

**Frontend.** Virtual-DOM reconciliation and keyed children; focus management and focus
traps; undo/redo command stacks; form validation state machines; virtualized and infinite
lists; state stores with memoized selectors; routers with nested layouts and guards; drag
and drop reordering; optimistic updates with rollback.

**Languages.** Garbage collectors (mark-sweep, generational, write barriers, nurseries);
async schedulers with cancellation and structured concurrency; Hindley-Milner type
inference; bytecode VMs and opcode dispatch; tokenizers and recursive-descent or Pratt
parsers; closures and scope chains; borrow checking and lifetimes; exception unwinding;
the classic optimizer passes (constant folding, dead-code elimination, register
allocation, SSA construction).

**Training.** Gradient accumulation and mixed precision; learning-rate schedules and
warmup; all-reduce, DDP and FSDP gradient synchronization; mixture-of-experts routing and
expert capacity; checkpoint save and resume; data-loader shuffling and sharding; early
stopping and gradient clipping.

**Inference.** KV caches, paged attention and block tables; continuous or in-flight
batching; speculative decoding and acceptance rules; streaming detokenization, stop
sequences and UTF-8 boundaries; top-k/top-p sampling and determinism;
grammar-constrained decoding and logit masks; quantization and dequantization.

**Evaluation.** pass@k estimation; LLM-as-judge rubrics and pairwise preference;
contamination and train/test overlap detection; flaky retries and quarantine; leaderboard
ranking, Elo and Bradley-Terry; bootstrap confidence intervals; answer normalization and
exact-match canonicalization.

**Kernels.** Tiled GEMM; flash and fused attention with online softmax; warp-level
reductions and prefix scans; fused normalization kernels; coalescing and shared-memory
bank conflicts; occupancy and register pressure; sparse kernels (SpMV, CSR).

Being on the list does not kill an idea, and two retained bundles sit squarely on it:
`reach-pair-sweep` is a generational collector and `token-seam-emit` is streaming
detokenization. What kills an idea is *being* the archetype - grading the thing every
write-up of it already explains. The usable form is the archetype entered from a side no
write-up enters from: a stated invariant the published algorithms never have to satisfy,
and a graded output the archetype's own formulation cannot produce.

`tools/originalitycheck.py` carries a narrow regex for each entry and reads it against the
mechanism sentence, the substrate and the tags. A hit is not a verdict - it is a prompt to
answer `collision.archetype` honestly.

## The rules that follow

1. **Name the archetype, always.** An archetype you cannot name is one you have not
   checked. "None of them fits" is an answer only after you have said which came closest.
2. **Write the twin sentence first.** One sentence, mechanism first, story removed. If
   that sentence could be the abstract of a tutorial, or could describe a task someone
   else plausibly submitted this month, the design is the problem and no rewording fixes
   it. This is the sentence `mechanism.sentence` holds and the checker measures.
3. **Rotate the substrate.** Never build two tasks in one substrate. The ledger records
   every substrate already used, and the checker measures overlap against it.
4. **Keep tags mechanism-specific.** Measured across the twelve bundles in `tasks/`: the
   only tag any pair shares is `differential-testing`, a testing method. No pair shares a
   mechanism tag. Two shared tags with anything in the ledger is a hard stop.
5. **Rotate the label.** Nine labels are open (`Software`: Algorithms, Databases, Data
   engineering, Frontend, Languages; `ML`: Training, Inference, Evaluation, Kernels).
   `Software`/`Systems` is retired. Submitting three Algorithms tasks in a row raises the
   collision odds against your own earlier work before anyone else's is considered.
6. **Prefer a composite invariant to a named one.** A mechanism that has a name has
   write-ups; a mechanism that is two invariants holding at once, where the standard
   answer to each breaks the other, has none. That property is also what the difficulty
   doctrine asks for, which is why the two gates usually move together.
7. **Record the flags you get.** When the platform flags a submission, put it in the
   ledger with `verdict = "flagged-similar"`, what it was flagged against, and the wording.
   It is the only evidence this repository can hold about a screen it cannot run.

## The record and the checker

The record lives at `authoring/<slug>/originality.toml`, outside the bundle, and never
ships. `template/originality.toml` documents every field. Write it at Stage 1, before the
difficulty record, because a design that has to be replaced for collision should be
replaced before it is scored for difficulty.

    python tools/originalitycheck.py <slug>

Seven axes, 100 points: mechanism stated (15), nearest public work (15), nearest submitted
task (20), distinctness surfaces (20), search evidence (10), crowded-archetype check (10),
ledger separation (10). The floor is **90**, and it is set by construction rather than
fitted: the rubric has seven axes, a record at 90 has answered all of them with at most one
ten-point axis short, and losing either twenty-point axis puts a record under it. No
similarity verdict from the platform is recorded in this checkout, so there is no
passed-and-flagged set to fit a floor to. When verdicts arrive in the ledger, recalibrate.

Hard stops cap the score at 40: the nearest public work plans the task; the nearest
submitted task grades the same mechanism; a twin was found; the label is retired or does
not belong to its category; the tags share two or more entries with a ledger task; the
built instruction is past a corpus stop.

Three things are measured rather than read from the record: tag overlap, substrate reuse
and mechanism-sentence distance against every entry of `authoring/submissions.toml`, and -
once `tasks/<slug>/instruction.md` exists - that instruction against every other
instruction in `tasks/` plus any `--corpus` directory of earlier submissions.

    python tools/originalitycheck.py <slug> --corpus ~/submitted-tasks
    python tools/originalitycheck.py --nearest tasks/<slug>/instruction.md

## Measured on this checkout, 2026-09-22

`--calibrate` compares all 66 pairs of the 12 instructions in `tasks/`. The pipeline holds
those bundles alongside each other, so the distance they keep is what accepted-distinct
looks like in this metric:

| measure | median | maximum | pair at the maximum |
|---|---|---|---|
| tf-idf cosine | 0.203 | 0.273 | `guard-mark-unwind` / `token-seam-emit` |
| 5-word shingle overlap | 0.0006 | 0.047 | `guard-mark-unwind` / `token-seam-emit` |

The ceilings are those maxima rounded up: cosine **0.28**, shingle **0.05**. Above a
ceiling is a warning. The stops, at **0.40** and **0.15**, are set by construction at a
distance no accepted pair comes within 0.12 of.

What this does not measure: instructions here describe the concept and never name it
(`docs/DIFFICULTY.md` A2), so two tasks can grade one mechanism in disjoint vocabulary and
still score far apart. The corpus half catches reworded prose and shared setting. The
mechanism sentence, written by the author, is what catches the rest - which is why the
record exists and why no number in it is worth padding.

`python tools/originalitycheck.py --selftest` proves the rubric fires: a complete fixture
scores 100, and twelve seeded defects each produce their own stop or their own lost
points - a public page that plans the task, a declared reskin, a found twin, a retired
label, a label outside its category, two tags already in the ledger, two surfaces instead
of three, a crowded archetype declared clear while the sentence matches it, an unnamed
nearest task, a search run twice, a reused substrate and a restated mechanism sentence.
Two further cases check the corpus metric itself: an instruction reworded word by word
lands past both stops against its original, and no two accepted instructions cross the
ceilings.

`authoring/controls/originality/` holds three records written for this checkout, not
submitted designs, standing for the three ways a task gets flagged: an archetype entered
from the front (37), a reskin of a ledger task (40, hard stop), and a design whose tags
give it away without the record admitting anything (40, hard stop). `--calibrate` fails if
a rubric change lets any of them reach the floor.

## Where it runs

- **Stage 1, idea intake.** Write the record, run the checker, and replace the idea if it
  is below the floor. Before the difficulty record, not after it.
- **Stage 5, instruction.** Run it again once `instruction.md` exists: the corpus half now
  has something to measure, and a brief that drifted toward a neighbour shows up here.
- **Stage 7, packaging.** Run it with `--corpus` pointed at every earlier submission you
  still have, and add the task to `authoring/submissions.toml` the day it is submitted.
- **After a verdict.** Record it in the ledger, flagged or passed. A flag with its wording
  is worth more to the next design than any amount of doctrine.

## How not to use it

A distinct task that is easy is still rejected, and a hard task that is a reskin is still
rejected. These are separate gates with separate records, and neither substitutes for the
other. Do not reword an instruction to move a cosine: the screen compares mechanisms, and
the number moves without the task moving. Do not drop the archetype name to dodge the
regex; the field exists so the next session knows what was checked.
