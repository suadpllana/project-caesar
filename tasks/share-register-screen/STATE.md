# Task state

Working notes. Never ships (package.py drops it) and no pipeline gate reads it. What matters
between sessions belongs in CLAUDE.md; this is the per-task detail while the task is alive.

## Current stage

`Stage 7 - gates` (built 2026-09-02; failed the easiness probe 3 of 3 the same day and was repaired)

## Assistant's assigned role

You are a senior financial-crime systems engineer; you have spent years on ownership and
control screening, corporate registries and the arguments with regulators about what
"control" means when nobody holds a majority.

## Source repository (repo-based tasks only)

- Repo URL: none - idea-based task, simulator written from scratch
- Upstream-diff check: nothing is vendored, so there is no upstream to diff against

## Task summary

A sanctions screen reads a register of company filings, replays them, and decides for each
company whether a programme reaches it through the parties it has named. The shipped screen
walks the register once and counts the seats whose taker is on its list. Both are wrong. The
list is closed under itself, so the walk repeats until it settles; and the parties on the
list arrive at a meeting as one hand, so the board has to be filled against their combined
holding rather than against each of them separately.

## Why it is hard

- Expert time estimate: 7 hours
- Why a frontier agent cannot one-shot the plan (the strategic answer - required): the memorised model of ownership screening is a percentage chain with a fifty per cent threshold, and the graded question is a board filled seat by seat by running averages, where a group of holders takes more seats together than its members take apart; nothing in the tree says so, the screen prints a plausible determination under either reading, and the registers that separate them are generated inside the verifier after the agent has stopped.
- Tactics making that true: A1, A2, B2, C1, C2, C4, prong C
- Assistant's attack on the plan (its first plan, and where that plan is wrong): my first plan was to build the holding graph, seed the list with the named parties, and repeat - for each company, ask the shipped allocation for its board and add the company when more than half its seats went to holders on the list; that plan is wrong in one line, because it asks the allocation for a board in which the list's holders stand apart, and the seats they take apart are fewer than the seats they take together. I would have shipped it.
- Estimated solves out of 8: 2, and that estimate is now the second one. The first build
  came back 3 of 3 on the easiness probe because the brief stated the collapse in prose;
  both sentences are gone and a third graded decision went in. The closure half still
  announces itself in the shipped output and most attempts will fix it; the collapse half
  and the treasury half have no local signal at all.
- Probe result: 3 of 3, 2026-09-02, runtimes 2m30s to 3m58s against 240 minutes. The
  solving submission is kept verbatim at authoring/variants/ok-probe-solve and must keep
  scoring 1, because it is correct. Re-grade it after every change.
- Leak audit: nothing in the environment reports whether holders are treated together;
  there is no field, flag or helper that names a group; deadfieldcheck is clean, so nothing
  is written and never read; onelinecheck finds no exact rule at depth <= 2 over the exposed
  fields for either graded decision, including over `apart`, the number of seats the list's
  holders take standing alone, which is the natural wrong answer and is one call away.
- Expert path: read reg/lex.py and reg/book.py to recover the filing language; read
  reg/site.py for what a holding is worth and who casts it; read reg/poll.py and notice the
  board is filled one seat at a time by running averages rather than shared out in
  proportion; run screen_reg.py over regs/ring.txt and see a company off the list on a row
  saying the list took two of its three seats; make the sweep repeat until it settles; then
  read the requirement again, notice it asks what the parties on the list CAN appoint,
  work out that a group of holders is one hand at a meeting, collapse them in voice.py, and
  fix tally.py to count that hand rather than looking for members among the takers.
- Originality check: searched for write-ups of group control under seat-by-seat board
  allocation. The fifty per cent aggregation rule is documented everywhere; the board
  apportionment method is documented everywhere; the combination, and the fact that a
  coalition gains seats under it, is not written up as a screening rule anywhere found.

## Verifier contract - FROZEN after Stage 2

- Artifacts the agent produces: /app/pol/screen.py, /app/pol/voice.py, /app/pol/tally.py,
  /app/pol/note.py
- What is checked: the determination record for every company of every register, in
  incorporation order - company, on the list or not, seats the list took, seats it has, and
  who took each seat. All or nothing.
- Tolerances: none. Integer arithmetic throughout.
- Ground truth: tests/gt.json for the 23 enumerated registers, re-proved at verification
  time by tests/oracle.py; the 320 generated registers are answered by tests/oracle.py after
  the run, from a nonce made at trial time.
- Deliberately not graded: consultation counts, caching, sweep order, and the name a
  submission gives a combined hand.

## Decisions and their reasons

- Registers are generated tie free, and every shipped register is checked. A seat taken on a
  tied average is settled by the name of a hand, and the name is the submission's business.
  The variant ok-latekey exists to hold that line: it is the reference with the hand named
  so it sorts late, and it disagreed with the reference until the tie guard went in.
- The programme names only natural persons. A named company would be a further decision
  needing its own sentence in the brief, and nothing grades it.
- No work counter anywhere. Five tasks in this repo grade work against a budget and the
  similarity screen rejected the fifth for it.
- Nominee arrangements may point at a company, including the company whose own register the
  nominee stands on. That was unreachable in the first build, which left a whole rule
  ungraded; it is now about a quarter of generated registers and it is the decision that
  breaks the natural implementation of the collapse.

## Validation status

| Check | Status | Notes |
|---|---|---|
| Agent image builds | pass | docker_trial2, both images |
| No answer leaked into agent image | pass | file-by-file walk of the built image |
| oracle = 1 | pass | real two-image trial |
| nop = 0 | pass | real two-image trial |
| Cheats all score 0 | pass | 21 of 21, each caught by the layer aimed at it |
| Variants all score 1 | pass | 6 of 6, real verifier, incl. the probe's own solve |
| `preflight.py` | pass | 13 unused-public-function warnings, the documented false positive |
| `harbor check` rubric | not run | harbor is not installed here |

## Open questions and next steps

- The repair is UNVERIFIED by probe. All three local probe agents died on the account
  session limit before writing a line, so nothing has re-measured the band since the
  rejection. Running the three-agent probe is the first thing to do next session, before
  any further change.
