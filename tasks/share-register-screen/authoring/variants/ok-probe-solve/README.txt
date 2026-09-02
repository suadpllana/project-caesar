The submission that solved this task in the easiness probe of 2 September 2026, transcribed
from its own trajectory, unedited.

It is kept for two reasons. It is a correct alternative implementation authored by someone
other than the reference's author, and it differs from the reference in three places that
are all implementation choice: the combined hand is called "\x00list" rather than "+", the
seat count is reached by looking for the hand or any member among the takers, and the
closure is driven by collecting the whole round before adding it rather than adding as it
goes. Requiring it to score 1 is the sharpest guard this bundle has against grading a
choice instead of a behaviour.

And it is the regression test for the repair. The probe returned 3 of 3, and this
submission is why: its own write-up derives the combined hand in its first message, before
running any experiment, in the brief's own words. Two sentences of the instruction handed
it over and both are gone. Re-grade this file after any change to the task; it must keep
scoring 1, because it is right.

Worth knowing before reading it as evidence about difficulty: it also derived, unprompted,
that a company's own stock standing in a nominee's name is silent, and said so as a
judgement call it had to make. That rule was unreachable in the graded set at the time and
is graded now. So the axis added in the repair would not have stopped this agent. The leak
is what let it in.
