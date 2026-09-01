# Cheat suite

Every script here must score 0. Two families:

**Single-mistake variants** are the whole reference solution with exactly one
decision made the way a solver who missed one piece would make it. They are
generated from `solution/ref/route.py` by `authoring/emit.py`, so they always
carry the rest of the fix and test only the mistake they name. The interesting
ones produce every value correctly and fail on the work counters alone.

**Isolation probes** are built on the shipped tree and attack the verifier
rather than the problem: a backgrounded reward write, a planted run output, a
planted output followed by a hard exit, wrong-typed junk from the report,
forged counters, a privilege probe, a ground-truth read, a rewrite of the
non-editable engine in the tree being run, and a sweep of everything the run's
uid can reach.

**Forgery probes** are generated from `tests/gt.json` and are therefore handed
every answer: the view, the emitted values, the trace and both counters, which
they return by hijacking the driver's report. They exist because a report is a
claim made inside the process that ran the agent's file, so the graded thing is
the work journal underneath it. One offers no journal, one pads a journal to the
counts it claims, and one does the shipped tree's work and then deletes records
until the counts match. All three must score 0.

Regenerate with `python3 authoring/emit.py`, after `build_gt.py`. Do not
hand-edit these files.
