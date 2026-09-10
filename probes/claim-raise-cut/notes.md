What the difficulty probe of 10 September 2026 measured, and what was done about it.

Eight trials of Fable 5.1 at xhigh effort against the bundle as uploaded (`claimraisecut.zip`,
the version that had passed the easiness probe 0 of 3). None solved it. Three transcripts are
beside this file with the brief stripped from the top of each, so that `tools/leakcheck.py`
compares the solver's words against the brief rather than the brief against itself. The
transcripts carry no verdicts beyond the probe's 0 of 8.

What all three have in common is that they did the work. Each read the five editable modules
and the frozen tree once, listed every defect of the shipped service against the sentence of
the brief it violates, rewrote all five modules, wrote a slow literal model of the brief in
/tmp, and fuzzed the rewrite against it on hundreds to thousands of generated programs with
hundreds of cuts and zero mismatches. Each generated the two large shapes at graded scale and
timed them in well under a second. Trial 2 found and fixed two ordering bugs in its incremental
relation by fuzzing; trial 1 found a shape the graded set does not contain (thousands of raises
stuck behind one blocker), profiled its engine from 67 s to 0.25 s on it, and shipped that.

Each trial then listed the points on which it had made a judgement call, and the same item is
on every list:

  trial 1   "resumption is depth-first": a resumed transaction's own grants run before the
            next queued transaction, and its driver yields into them at once
  trial 2   the driver resumes each granted transaction inside the sweep that granted it
  trial 3   "nested cascades run before the outer transaction continues"

The sealed model keeps one FIFO line: a granted transaction joins the back, the line runs
after the step, and what a running transaction grants joins the back behind everything
granted before it. The brief said "they resume in the order they were granted, one at a time,
each running the steps it was holding until it is stopped again" and nothing about what a
running transaction's own grants do; the shipped `txn.py` ran them nested, and all three
agents kept that structure while fixing everything around it. Measured with
`authoring/claim-raise-cut/altmodel.py`, the nested reading moves 20.3 per cent of the
generated population and no enumerated program caught it. Under all-or-nothing grading that is
0 of 8 with three engines that were otherwise right.

The other judgement calls the trials record all match the model: the held mark rather than each
claim in the stack (trial 2 measured the two apart on 5 of 300 programs and chose the model's
reading), the victim chosen across every ring rather than the first found, the ring check only
after top-level steps, end and cut releasing every claim before any sweep.

`tools/leakcheck.py` finds two rule phrases quoted back in trial 1 and nothing above the floor
in trials 2 and 3; the task was not solved, so no plan leaked, and the phrases are rules
restated in the agent's own docstrings.

The repair is recorded in tasks/claim-raise-cut/STATE.md under "Difficulty recovery -
2026-09-10 (difficulty probe 0 of 8)": the brief now states the line, two enumerated programs
name the two resumption readings, and two cheats carry them.
