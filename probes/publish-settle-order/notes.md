What the easiness probe of 9 September 2026 measured, and what was done about it.

Three trials against the bundle at commit 654a50c. Two solved it. The three transcripts are
beside this file with the brief stripped from the top of each, so that `tools/leakcheck.py`
compares the solver's words against the brief rather than the brief against itself. The
transcripts carry no verdicts: which of the three failed, and on what, cannot be read from
them.

What all three have in common is the shape of the first substantive message. Each read the
six editable files and the frozen tree once, ran `tiny.txt`, and then listed every defect of
the shipped host against the sentence of the brief it violated - fallback ranking, missing
scopes, startup calls after the closure, uses surviving a retirement, ordering edges and dead
units counted for retention, a sweep taking the first unwanted unit and rescanning. None of
them ran an experiment before committing to the plan. All three then wrote the six files in one
pass, profiled `wide.txt` once, and replaced the scan with buckets per name and scope and the
rescanning sweep with a heap keyed by publication serial or position. The two derivations the
task rested on were each agent's first idea.

`tools/leakcheck.py` finds one shared phrase in trial 1 ("a unit of the same name coming back
up", from the sentence that states the identity rule) and nothing above the floor in trials 2
and 3. The plan did not come from quoted prose. It came from the rules being individually
implementable and the structures each rule wants being the standard ones.

Each trial flags one judgement call, and the population exercised none of the three:

  trial 1   a unit that names itself as a dependency does not keep itself up
  trial 2   `act` on a scoped unit keeps that unit reading its own scope afterwards
  trial 3   two units that name each other as dependencies stay up after every hold is gone

All three corners are now stated in the brief rather than left to a reading.

The repair is recorded in tasks/publish-settle-order/STATE.md under "Easiness recovery -
2026-09-09 (probe 2 of 3)".
