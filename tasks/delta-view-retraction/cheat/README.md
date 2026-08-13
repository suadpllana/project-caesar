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
forged counters, a privilege probe, a ground-truth read and a sweep of
everything the run's uid can reach.

Regenerate with `python3 authoring/emit.py`. Do not hand-edit these files.
