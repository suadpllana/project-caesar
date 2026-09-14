# The instruction is the contract

**Mandatory reading, before anything else.** Every session reads this file in full first -
before `AGENTS.md`, before any other doc, and before creating a new task or fixing, recovering,
renaming or resubmitting an existing one. It applies at every stage, not only when
`instruction.md` is drafted, because the gaps it describes are designed in at Stage 2 and
survive every later gate.

Reviewers reported on 2026-09-14 a common pattern in human review: the instruction file is below
contract quality. Whole tasks died on a rank base and on a +d versus -d sign. Neither was hard
work for the solver; the contract was incomplete. The task should be hard because the problem is
hard, never because the contract is incomplete.

## The one rule that matters most

Every graded assertion must trace to a sentence in the instruction.

Walk the test files line by line. For each assertion, find the sentence that tells the agent
about it. If there isn't one, write it or stop grading it. The converse in `AGENTS.md` D1 still
holds: every sentence needs a test.

In this repository's verifier shape a graded assertion is more than an `assert`:

- every `assert`, `pytest.fail` and test function in `tests/`;
- every enumerated case, because each one pins a rule;
- every branch of the sealed model (`tests/model.py`, `tests/oracle.py`) that can change a graded
  token. `assert got == want` hides every rule the model applies, so when output is compared
  against a model, the model is the test file and it is walked line by line like one;
- every condition in `tests/test.sh` and the runner that can turn a run into a 0: the wall clock,
  memory caps, which files are collected, the frozen-file seal, required entry points and
  exports, the output location and its exact format, forbidden constructs and source strings.

Discoverable is not stated. A fact the agent could dig out of the shipped tree still needs its
sentence when the verifier grades it. Prong B withholds the plan (`docs/DIFFICULTY.md`); it never
withholds the contract, and describing a concept without naming it (A2) is still a complete
description.

## Where the gaps cluster

Put every graded quantity through all four.

1. **Boundaries and conventions.** 0- versus 1-based indexes and ranks; `<` versus `<=` at a
   timestamp, a limit or a capacity; ties and the order that breaks them; units; signs; empty,
   missing and zero cases; rounding and number format; output order; duplicates; case
   sensitivity; what happens exactly at a limit. A convention the text leaves open is a coin the
   solver flips, and all-or-nothing grading scores the flip.
2. **Definitions of graded quantities.** If the verifier grades `residual_m`, `attempts`,
   `real_tokens` or `cost`, the instruction defines it: what counts, what is excluded, when it is
   measured, its unit and its rounding. A name is not a definition, and a field name the agent
   must emit is itself a requirement.
3. **Docs that contradict the reference.** A spec asserting an invariant the oracle violates, or
   a stale count - "forty scrapes" when 26 ship. After any change to the reference, the model,
   the generator or the environment, re-derive every number and every "always", "never", "each"
   and "only" in the instruction and in the `task.toml` explanations from the code, not from
   memory (`CLAUDE.md`: counts drift with the generator). `tools/hintcheck.py` checks
   work-counter figures against `gt.json`; the rest is a grep for digits and number words.
4. **Verifier requirements absent from the instruction.** Internal field names the tests read,
   file-layout rules, which files are collected, forbidden source strings, required exports and
   entry points, the wall clock, memory caps, and the printed format down to separators and line
   order.

## Write the walk down

The walk lives in `authoring/<slug>/trace.md`, outside the task folder, so it never ships. Start
it from the verifier, not from memory:

    python tools/tracecheck.py <slug> --skeleton

That writes a trace with a row for every test function, enumerated case, collected artifact,
clock, memory cap and tolerance, every top-level function of the sealed model, and every wrong
reading in `authoring/<slug>/readings.py`. Fill every row, and split each model row into one row
per rule it applies, citing its lines (`tests/model.py:120-134`). The four sections are tables:

    ## Graded assertions   | Verifier site | What it grades | Instruction sentence |
    ## Readings            | Reading | Sentence or published example that rules it out | Case that separates it |
    ## Shortcuts           | Strategy | Result |
    ## Tolerances          | Tolerance or limit | Independent implementation | Measured |

Cite the instruction word for word inside double quotes, four words or more. Quote the
distinctive span rather than the whole paragraph, and leave out any double quote inside it. A
decision the instruction does not settle is written `NOT STATED` and then fixed: write the
sentence, or stop grading it. Then run:

    python tools/tracecheck.py <slug>

It fails on a quote that is no longer in `instruction.md`, a `NOT STATED` or `TODO` row, a row
that cites nothing, a test function, enumerated case or wrong reading with no row, a `file:line`
that does not exist, a declared artifact the instruction never names, a clock, memory cap or
tolerance the instruction never states, a limit validated against nothing on disk or only against
`solution/`, and an empty Shortcuts table. It cannot tell whether a quoted sentence actually
settles the decision it is cited for. That judgment is yours, and it is what review reads.

Re-run it after every change to `instruction.md`, `tests/`, the model, the generator or the
environment. A trace is evidence only while its quotes are still in the file.

## Identifiability

Enumerate the readings a competent solver might try, not just your own candidate list. These
sources produce readings an author would not think of:

- the four clusters, applied to every rule: the other index base, strict against non-strict, the
  other tie-break, the opposite sign, empty as zero against empty as skipped;
- the model's prior: the textbook convention for the domain, which is what a solver writes first;
- the shipped broken code: whatever it does is a reading someone will keep;
- every earlier revision of the reference and every probe trajectory, winning or losing;
- the other parse of each sentence: the scope of "each", "before", "within", "at most", "until".

Keep the readings that reproduce all published evidence - every statement in the instruction,
every worked example, every printout whose correct output the instruction gives - and score the
survivors against the graded set.

- A survivor that disagrees with the reference on the graded set is a hole: nothing published
  tells a solver which of the two is meant. Add discriminating evidence rather than more prose -
  a worked example or a stated case whose correct output differs between the two. For a
  convention (a base, a sign, a tie) give the example freely; it is not the difficulty. Where the
  survivor reads the load-bearing mechanism, the worry in `CLAUDE.md` that a worked example
  becomes an oracle is real, so choose evidence that decides that one reading and nothing else -
  but add it. Difficulty that rides on an undecidable reading is an incomplete contract.
- Survivors that agree with the reference on the whole graded set are correct: promote them to
  correct variants that must score 1.
- A reading the published evidence rules out still needs an enumerated case that fails it, so a
  failure names the rule. `tools/readingcheck.py` measures that half.

Record every reading in the trace's Readings table.

## Shortcuts

Score the dumbest positional or constant strategy you can think of, each as a cheat
(`AGENTS.md` Stage 6):

- the shipped tree unchanged (the nop);
- a constant: the most common value of every graded field in the ground truth, or one fixed
  output for every case;
- positional: always the first candidate, the last, input order, sorted order, the earliest owner;
- the worked example's output replayed, and the previous revision of the reference.

If one passes, regenerate the data. Record the fraction of cases each strategy matches as well as
its score: all-or-nothing grading turns a strategy that matches 90% of cases into a 0 and hides
that the data barely exercises the rule. Shape the generator around the mechanism (`CLAUDE.md`:
an unshaped population moved one wrong reading on 3.7% of programs, the shaped family on 42.5%).

## Tolerances and limits

Validate every tolerance and limit - float comparisons, work ceilings, wall clocks, memory caps -
with a second, independently written implementation, never only against your own reference. A
limit tuned on the reference measures the reference; a correct implementation with another
summation order, data structure or constant factor must still pass. Use the sealed model where
it was written apart from the reference, or a correct variant under `authoring/<slug>/variants/`.
Measure its headroom against each limit under the declared CPU and memory caps, record it in the
Tolerances table, and state the limit in the instruction (`CLAUDE.md`: headroom is measured
against the slowest plausible executor, not the authoring machine).

## The cold reader

You know the answer, so your instruction reads as complete. Hand it to someone who has never seen
your reference and ask what decisions the text doesn't settle. Each one is a sentence or a worked
example you owe them.

A session that wrote the model cannot un-know it, and `CLAUDE.md` records that a self-probe
reported as cold by a contaminated author is worse than none. So put the reader's questions
mechanically and record the pass as author-run:

1. List every graded output: each printed token, field and file.
2. For each, list every decision that determines it - the model branches that touch it.
3. Put the four clusters to each decision as questions.
4. Answer each with a quote from the instruction or a worked example. An answer you can only give
   by reading the model is a gap.

A fresh session that sees only `instruction.md` and the agent-facing tree, asked only which
decisions the text leaves open, is the stronger form of the same test. Record which form ran.

## Length

A complete contract costs characters. The structural gate refused `fix-layered-config` on
2026-09-13 with `instruction.md` at 11042 characters against a 10000 cap (commit `5e93544`,
branch `claude/new-session-mph2dy`). Buy completeness with tighter prose: say each rule once, and
replace a paragraph that circles a convention with one worked example. Never leave a graded rule
unstated to make it fit; if it cannot fit, stop grading it.

## Where it runs

- **Before anything else.** This file, read in full, whether the session creates or fixes a task.
- **Stage 2, contract.** List every graded decision with the sentence it will need. A decision
  that cannot be stated without handing over the plan is a design problem now, not at Stage 5.
- **Stage 5, instruction.** Write it, then walk the trace, the identifiability check and the cold
  reader until `tracecheck` is clean.
- **Stage 6, anti-cheat.** The shortcut strategies are cheats, and they score 0.
- **Stage 7, packaging.** `tracecheck` is clean on the final bundle and the instruction-contract
  fields of `STATE.md` are answered. `preflight.py` errors when `STATE.md` carries that section
  with a field unanswered or no trace on disk, and warns when the section is missing.
- **Fixing a task.** Any change to the instruction, `tests/`, the model, the generator or the
  reference re-runs the walk before any other gate is re-run.

## Measured on the bundles in this checkout

`tracecheck --bundle` was run on 2026-09-14 over the 30 task folders present in the local
checkout. 23 are clean. Seven are not, and on reading, each finding is a real gap:

- five of the eight AI-passed bundles impose a wall clock on the graded run that their instruction
  never states - `delta-view-retraction`, `focus-return-point`, `guard-mark-unwind` and
  `sheet-block-place` at 600 seconds, `share-register-screen` at 540 - and `scope-hold-release`
  does the same at 600;
- `reach-pair-sweep` collects five declared files that its instruction names only as "the five
  files under `/app/col`", so nothing in the text says a new file there is never collected.

Whether review would stop on a clock that generous is not known; under the rule it is a graded
condition without a sentence. The first run also produced false positives, fixed before these
counts were taken: four briefs write their clock in words ("six hundred seconds"), and
`packed-doc-settlement` puts a literal `timeout=5` on the grader's own wait after a kill. The
check now reads number words and ignores `wait` and `join`.

The trace checks were proved on a scratch fixture. A complete trace is clean, and each of thirteen
seeded defects fails with its own message: a stale quote, a `NOT STATED` row, a row citing
nothing, a case, test or reading without a row, a reading without a separating case, a site past
the end of its file, a limit validated only against the reference, no shortcut scored, a
tolerance or clock without a row, and a clock or artifact missing from the instruction.

The bundles in `tasks/` are recorded in `README.md` as passing the AI review; none recorded as
passing human review is in this checkout. The retained set is therefore not calibration for this
rule, and a clean `--bundle` result says only that a bundle's artifacts and limits are named.
