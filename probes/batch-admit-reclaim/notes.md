Commentary on `cold-solve.md`, kept separate so that `tools/leakcheck.py` is not
made circular by a file that quotes the brief.

This is a self-probe rather than a three-agent probe: the same session that built
the task solved it, so it cannot be cold in the strict sense. What it can measure
honestly is whether the plan recorded in the proposal, before any code existed,
would have passed. Both submissions were graded through the real verifier, not by
my own report.

  the first plan, patched for the merges and for the finishers' releases
                                        reward 0, 189 of 300 generated traces wrong
  the same plan with the count replaced by playing the step out on a copy
                                        reward 1, first write

The second row is the finding that matters and it is a mode C signature: a
careful reading of the specification, written once, is correct. At the time of
that solve the brief carried a full description of the machine - the step order,
block identity, the merge, the difference between releasing a block and giving it
up - and the play-out is a transcription of that description. The repair was to
cut all of it out of the brief and leave it where it actually lives, in the frozen
engine under `/app/eng`, which the agent has to read and run. The brief now
carries only what the four policy files must achieve, the fences, the input space
and the output shape; everything about how the machine behaves is in the code.

That repair raises the exploration cost and is not proof of anything. It is not
measured here, because the only instrument available in this session already knows
the answer. Recorded plainly rather than claimed: the pre-cut brief was solved on
the first write, the post-cut brief has not been probed cold by anyone.

Two guesses are recorded at the end of `cold-solve.md`. Both were closed in the
brief afterwards: the entry condition now says "without a request being put out on
its account", which decides the first, and "everything it was holding" is stated
against what the engine holds, which decides the second. An undecided rule is the
most expensive defect in this repository and these two were found the only way
they can be found, by someone writing the files and noticing they had to choose.
