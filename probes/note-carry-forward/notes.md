# note-carry-forward, easiness probe, 2026-09-04

Rejected 3 of 3. Runtimes **1m16s, 1m17s and 1m14s** against a 14400 s budget, at
4.1k to 4.6k output tokens. `trial1.md`, `trial2.md` and `trial3.md` hold the agents'
own words only, with the brief stripped off the front of trials 2 and 3 so that
`leakcheck.py` is not circular.

## Attribution

| check | result | rules out |
|---|---|---|
| `leakcheck` on all three | nothing above the floor | the *wording* of the brief |
| one `Write` of each file, no intermediate wrong version, all three | mode C signature | "too hard" |
| runtimes at 0.5 per cent of budget | the plan was available on sight | mode D |

`leakcheck` being quiet is what made this worth writing down. It matches phrases, and
all three agents restated the brief's rules in their own vocabulary - "longest common
subsequence", "hunks", "the pinned change script" - so nothing crossed its floor. The
brief was still the source: walking the graded decisions against the sentence that
decides each one puts three of the six reasoning steps in the brief outright, and those
three are the three the difficulty argument rested on.

## The reconstruction

`solve/` is the submission rebuilt from the trajectories' own prose. Against the
bundle as probed it scores **1**, which is what says the solve was real rather than a
probe artifact. Against the repaired bundle it scores **0**. Re-grade it after any
change to the rule:

    cp -r probes/note-carry-forward/solve tasks/note-carry-forward/authoring/probe-solve
    python3 tools/docker_trial2.py note-carry-forward --dir authoring/probe-solve
    rm -rf tasks/note-carry-forward/authoring/probe-solve
