The submission that solved this task in the easiness probe of 2 September 2026, transcribed
from its own trajectory, unedited apart from the docstring it shipped with.

It is kept for two reasons. It is a correct alternative implementation authored by someone
other than the reference's author, and it reaches the assignment by a route no other policy
in this bundle takes: it never calls the accessors at all, reading `core.ms` directly to
build a holder-to-waiters map, and it takes the maximum over the base priorities of the whole
transitive closure rather than over the effective priorities of the direct waiters. Those two
are equivalent, and the equivalence is not obvious - any task lifting a waiter is itself
inside that closure. Requiring this file to score 1 is the sharpest guard this bundle has
against grading a route instead of a state.

And it is the regression test for the repair. The probe returned 3 of 3, and all three
trajectories read the same way: read the files, then one write of the finished policy, before
running any experiment. The rule was in the brief and they transcribed it. The sentences that
handed it over are gone. Re-grade this file after any change to the task; it must keep
scoring 1, because it is right.

Worth knowing before reading it as evidence about difficulty: all three submissions were the
same shape as `ok-full-solve`, which was written before the probe ran, so the repair is not
that this route was unforeseen. The repair is that the value the route computes was printed.
