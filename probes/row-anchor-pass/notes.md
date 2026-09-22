What the easiness probe of 22 September 2026 measured, and what was done about it.

Three trials against the bundle the contributor supplied as `row-anchor-pass.zip` (never in this
repository; its reference, instruction and `task.toml` are kept in
`authoring/row-anchor-pass/submitted/`). All three solved it. The transcripts are
beside this file with the brief stripped from the top of each, so that `tools/leakcheck.py`
compares the solver's words against the brief rather than the brief against itself.

All three took the same route, in five or six steps and three or four tool calls:

  1. one command that printed every file of the tree and the event files;
  2. a list of the shipped defects, each against the sentence of the brief it breaks: the hold
     taken at the offset instead of the anchor line, the band never pushed off, overscan below
     only, the foot flag read before the movement, a single pass, a delete re-choosing the hold;
  3. all six files rewritten in one pass, with the geometry held as a Fenwick tree (trials 1
     and 2) or per-group prefix arrays rebuilt lazily (trial 3) over the groups;
  4. the tiny and pair files run and both large files timed (0.2 to 0.5 s each);
  5. trials 2 and 3 wrote a brute-force model of the brief and fuzzed 3000 generated documents
     against their pane, with no mismatch.

No trial ran an experiment before committing to its plan. The earliest point at which each had
the whole plan is the end of its first read of the tree. The brute-force model in step 5 is an
oracle for the brief, and it confirmed every rule at once.

`tools/leakcheck.py` finds one shared phrase in trial 2 ("before the first visible item to K",
from the sentence that states the window rule) and nothing above the floor in trials 1 and 3.
That sentence states a graded rule and has to stay. The plan did not come from quoted method
prose: it came from a brief whose paragraphs are each one rule, each rule being implementable on
its own, one paragraph per shipped module, and a fast structure that is the textbook one.

The reference in the bundle reproduces all three agents' printed lines exactly, including the
`wide.txt` and `deep.txt` end lines.

The repair is recorded in tasks/row-anchor-pass/STATE.md under "Easiness recovery - 2026-09-22".
