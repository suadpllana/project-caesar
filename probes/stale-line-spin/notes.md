What the easiness probe reported on 23 September 2026, and what was done about it.

Three trials against the bundle at commit ef7a40e. All three solved it. The transcripts are beside
this file with the brief stripped from the top of each (everything up to the harness's first
`[clipped]` marker), so that `tools/leakcheck.py` compares the solver's words against the brief
rather than the brief against itself. Nothing else was removed or reworded.

All three took the same route, in the same order:

1. One read of the six editable files and the frozen tree, then a list of every shipped defect
   against the rule it breaks (trial 1 line 254, trial 2 line 678, trial 3 line 712), then the six
   files rewritten in one pass. The worked example came out right on the first run in every trial.
2. A profile of the two large samples, then a generic speed-up: while every ready block on a
   multiprocessor spins, global memory cannot change, so each multiprocessor evolves on its own;
   remember its (rotation, cache) state, jump when the state repeats, and wake it on a placement,
   a wake or a store it can see (trial 1 line 447, trial 2 line 1027, trial 3 line 1313). Trial 1
   added a closed form for multiprocessors whose spinners all bypass the cache (line 740). The
   large launches ran in 0.7 to 2.9 s each.
3. A brute-force cycle stepper written from the brief, then thousands of random and structured
   launches diffed against it: 4471 in trial 1 with no disagreement, 4200 in trial 2 after one bug
   (a spin passing straight into another spin left the repeat key unchanged, line 1794), about
   6800 in trial 3 after one bug (a block leaving its work straight onto a spin, line 1165).

None of the three needed the derivation the design rested on - when a spin attempt leaves its
cache as it was - because detecting a repeated state answers the same question without asking it.
The self-built stepper answered every other question the sealed verifier was meant to keep closed.

The repair is recorded in tasks/stale-line-spin/STATE.md under "Easiness recovery - 2026-09-23".
