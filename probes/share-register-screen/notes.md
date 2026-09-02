What the probe of 2 September 2026 measured, and what was done about it.

The three trials ran 3m52s, 3m58s and 2m30s against a 240 minute budget. Nobody explored
anything; the plan was available on sight.

Both defects are named in the solving agent's first substantive message, before it ran an
experiment, and the second one is in the brief's own words. Two sentences did it:

    Now put /app/regs/share.txt through it, where two named people sit on the register of
    every company in the file, and the first two come back no.

    What those holdings come to at a meeting is the whole of what the screen has to get
    right.

The first names a shipped file as exhibiting a fault and names the feature that makes it
faulty, so the case did not have to be found. The second names the quantity the task is
built on and says that quantity is the answer; it was written believing it stated the
input space.

Both are gone. tools/leakcheck.py run against solve-2026-09-02.md finds the second one and
names the sentence; run against the repaired brief it finds nothing above the floor. The
probe came back 0 of 3 and the task cleared the whole pipeline.

The submission itself is authoring/variants/ok-probe-solve and must keep scoring 1, because
it is correct. Note the first of its two judgement calls: it derived the treasury rule
unprompted, so the third graded decision added in the repair would not have stopped this
agent. The leak is what let it in.
