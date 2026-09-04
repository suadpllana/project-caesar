# alias-settle-report easiness probe, 2026-09-04: 3 of 3

The three trajectories beside this file are the agents' own words with the pasted brief
stripped (lines 1-22 of each upload), so `tools/leakcheck.py` can be run against them
without being circular. Commentary lives here and not in those files.

## Runtimes

| trial | runtime | output tokens | outcome |
|---|---|---|---|
| 1 | 2m 07s | 8.3k | reward 1 |
| 2 | 1m 47s | 6.4k | reward 1 |
| 3 | 7m 12s | 8.3k | reward 1 |

Budget 14400 s. Nobody explored anything. The plan was available on sight.

## The signature, identical in all three

1. One tool call: `find`, `cat run_bind.py`, `cat bind/*.py`. The whole environment is 186 lines.
2. One tool call: `cat` and run the three sets.
3. **One `Write` of `rch.py` and one of `hold.py`, both correct.** No intermediate wrong version.
4. A self-built fuzzer. Trial 3 built an exhaustive oracle that enumerates every legal
   continuation of ties and posts from any state and asks whether the line could change
   (750 sets, 0 disagreements). Trial 1 checked that at every held tick a legal continuation of
   up to four events existed that would move the line (1100 sets). Trial 2 checked filed lines
   against the end state (6000 sets).
5. Done, with a write-up that describes the reference rule to the letter.

## What they wrote, against what the task was built on

The difficulty argument said agents reconstruct single-matcher deduplication from their prior
and produce one of three wrong readings of the difference rule (two ends 3 percent, consecutive
steps 15 percent, ignored 63 percent of generated sets). **Zero of three did.** Each wrote the
reference's search over growing difference-free groups in its first write:

- trial 1: "A cell may join if some open tag pool touches both it and the blob, and no bar
  stands between it and any cell already in the blob."
- trial 2: "joined by a chain of open-tag pools where no standing difference sits between any
  two items on the chain, since such a weld can never happen."
- trial 3: "Because every item on a merge path ends up welded together, the whole gathered set
  must be pairwise free of standing differences, so the search grows bar-free sets rather than
  following plain paths."

## Attribution

- `leakcheck`: trial 1 reuses one four-word phrase, and it is a stated fence ("a tag whose pool
  lies wholly inside one item alters nothing"), not the discovery. Trials 2 and 3: nothing above
  the floor. **Not mode A.**
- `onelinecheck`: `file-now` has no exact rule at depth 2 over exposed fields. **Not mode B.**
- One-shot write, then a self-built oracle that goes green: **mode C**, and the specific form
  of it that "What can be brute-forced, and what cannot" in CLAUDE.md names as its fourth dead
  family - a decidable property of the input under stated transition rules. The graded question
  is literally "could any legal continuation change this line", the brief has to state every
  legal transition for the task to be fair, and a strong agent writes the definition of that
  question rather than any shortcut to it. The three wrong readings are shortcuts. Nobody took
  a shortcut.
