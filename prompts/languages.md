# Software / Languages - name resolution as a fixed point

Paste the block below as the first message of a fresh task-authoring session. It supplies
the seed and the distinctness constraints; `NEW-TASK-PROMPT.md` supplies everything else.

---

```text
Build one Frontier Bench task in this repository, filed under category `Software`,
subcategory `Languages`. Follow `NEW-TASK-PROMPT.md` as the build contract in full: read
`docs/INSTRUCTION-CONTRACT.md` first, then `AGENTS.md`, then `docs/ORIGINALITY.md`,
`docs/DIFFICULTY.md`, `docs/QUALITY-REVIEW.md` and `docs/RULES.md`. Begin immediately, own
every part of the bundle, and ask me only when two materially different meanings of the
task remain after investigation. Never spawn subagents.

This message gives you the seed. It is a starting point with a planning attack already in
it, not a specification: deepen it where the measurements say it is thin, and replace it if
either record below will not reach its floor.

## The seed

Substrate: the front half of a compiler for a small module language. Modules declare
items, import other modules by name or by glob, re-export what they import, and gate items
on configuration flags. A program is a set of modules and a list of references to resolve.

Mechanism: resolve every reference to the item it names, or to a diagnostic. An explicit
import shadows a glob; a glob's contribution is whatever the source module itself resolved,
so a glob that re-exports a glob is defined only as a fixed point; two globs offering the
same name are ambiguous unless one of them is gated off by the configuration; and an
ambiguity reports the candidates it found, in declaration order across modules.

Graded output: one line per reference, naming the module and item it resolved to, or the
diagnostic with its candidate list in order.

## The planning attack

The first plan a frontier agent forms: build a symbol table for each module, then resolve
imports recursively with memoization, marking modules in progress to break cycles. This is
how every teaching compiler does it, and it is right for explicit imports.

The rule that breaks it: a glob import cannot be resolved by recursion, because what it
contributes depends on what the source module's own globs contribute, and two modules can
glob each other. Resolution is a least fixed point over the whole module set, reached by
iterating until nothing changes - and the memoizing recursive resolver silently returns an
answer for the in-progress case that the fixed point would not give.

The second discovery, which forces a replan rather than a patch: shadowing is not a filter
applied at the end. An explicit import shadows a glob even when the explicit import is
itself unresolvable, which turns what would have been an ambiguity into a different
diagnostic - so a resolver that collapses each name to a winner as it goes cannot produce
the candidate list the diagnostic requires. Provenance has to be carried through the
iteration, which the first implementation threw away.

The interacting pair to build the difficulty on: the gating rule decides which candidates
exist, and the shadowing rule decides which of them can be reported. A name can be
unambiguous under one configuration and, under another, not merely ambiguous but ambiguous
with a candidate list whose order comes from a module the reference never mentions.

The late case: a cycle of re-exports in which one arm is gated off, so the fixed point
converges to a smaller set than the first iteration suggests, and a reference that resolves
in the first iteration must end up as a diagnostic.

## Distinctness

Stay off the crowded Languages list in `docs/ORIGINALITY.md`: no garbage collector, no
cancellation or structured concurrency, no type inference, no bytecode VM, no tokenizer or
parser, no closures and scope chains, no borrow checking, no optimizer pass. This seed
never executes anything - there is no runtime in it at all - which is what keeps it away
from the two runtime tasks already in the ledger.

Before anything else, read `authoring/submissions.toml`. `guard-mark-unwind` and
`reach-pair-sweep` are both there under this label. Do not reuse their substrates or any
of their tags - `structured-concurrency`, `cancellation-propagation`,
`cooperative-scheduler`, `exception-unwinding`, `generational-collection`,
`write-barriers`, `remembered-sets`, `weak-references`. Two runtime tasks under one label
is already the edge; a third would be the flag.

Write `mechanism.sentence` in the originality record before you write anything else, and
hold it to the twin test: if that sentence could be the abstract of a tutorial, or could
describe a task someone else plausibly submitted this month, change the design.

Substrate roster, one to a task:
- name resolution as a fixed point over globs, re-exports and gated items (the seed);
- operator fixity that is itself imported, so how an expression parses depends on which
  declarations are in scope where it appears;
- macro expansion with hygiene: renaming introduced bindings, nested quotation, and a
  stated rule for what a macro's own expansion can capture;
- deciding which trait or interface implementation applies when several are in scope
  through different import paths, with a stated specificity order.

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

Language tasks go to runtimes and type systems, because those are the famous hard parts.
Name resolution is famous for being boring, and it is where real compilers keep their
ugliest code: two implementations of the same module system disagree on the gated-ambiguity
case, and the documentation of either describes the rules one at a time without settling
their interaction. Rules that are each documented and never documented together is the
position `docs/DIFFICULTY.md` calls a public technique with a private constraint set.

## What to check before writing code

- The diagnostic is graded, so its candidate ordering is part of the contract. Write that
  sentence in the instruction before building, or half the grading will trace to nothing
  (`docs/INSTRUCTION-CONTRACT.md`).
- Watch for a one-file collapse. If the fixed point, the shadowing and the diagnostics all
  live in one function, the quality review will read roughly a hundred lines of editable
  code and fail `difficult` (`CLAUDE.md`, 2026-09-09).
