# note-carry-forward

Scratch notes for the next session. Never ships; `package.py` drops it.

## What is graded

The thread table at the head of every stream - id, state and span for each -
and the ordered log of what happened to the threads on the way. All or
nothing. There is no work counter anywhere in this task and no timing budget.

## Verifier contract, frozen before the environment was written

- graded: the table and the ordered log, per stream
- not graded: how the board stores state, what it computes first, how many
  times it walks the store, or the order it hunts overlapping pairs in
- ground truth: `tests/gt.json`, root-only, rebuilt by `authoring/build_gt.py`,
  re-proved at grading time by `tests/oracle.py`
- event order inside one revision is part of the contract and is stated in the
  brief. The absorb log names the thread that **ends up** holding the span, so
  a board that merges by connected components writes the same log as one that
  hunts pairs; `authoring/variants/ok-merge-by-components` is that board and it
  scores 1. Without that the log would grade a procedure rather than a result.

## Difficulty argument

- Why a frontier agent cannot one-shot the plan: the board is a state machine
  over threads that have spans, states and a history, and four of its twelve
  graded decisions need something no single revision supplies - the previous
  revision's verdict for that thread, the state a reply left behind, a merge
  fixed point, and a mapping that only differs from a rebuilt one on files
  that repeat themselves.
- Tactics making that true: prong A (the retrieved plan is specifically
  wrong), prong C (no oracle for the graded quantity in the agent's tree).
- My own attack on the plan: my first plan widened each thread to the change
  group it landed in and iterated absorption to a fixed point, and it is wrong
  because group-widened spans are aligned to disjoint groups, so intersections
  are decided before any absorbing happens and the fixed point never iterates -
  measured at 0 disagreements over 400 streams. Spans that are arbitrary sets
  of lines do chain, which is why the mechanism carries spans rather than
  groups: `merge-in-one-pass` moves 47% of streams.
- Estimated solves out of 8: 1, designed. Not probed since the rebuild.

## The twelve graded decisions

Measured by `authoring/readings.py` over 300 streams from the graded
generator. Every one of these ships as a generated cheat scoring 0, and every
one is caught by the hand-written set rather than only by the generated block.

| wrong reading | streams it moves |
|---|---|
| the mapping taken from the standard library's matcher | 93% |
| the mapping rebuilt from an ordinary LCS walk | 91% |
| a change read as the lines the script added | 91% |
| merging on equal spans instead of on overlap | 82% |
| an outdated thread dropped off the board | 68% |
| the older thread keeping its own span, not the union | 66% |
| the whole span required to be inside the change | 51% |
| raising every revision the thread stays caught | 49% |
| merging in one pass instead of to a fixed point | 47% |
| the merged thread not dragged open by an open half | 43% |
| a resolved thread raised along with the rest | 27% |
| an answered thread not reopened when it is raised | 24% |

## Expert path

Walk the store. Carry spans through the script the tool settled, outdate the
ones that empty and leave them listed, raise on first contact and reopen the
answered ones, admit new threads, apply replies and resolutions, merge
overlapping spans to a fixed point with the older taking the union. About a
hundred and forty lines across the two artifacts.

## Quality-review rejection on `difficult`, twice, and what finally changed

Round one failed `difficult` because the brief stated the method. Round two
passed the review and failed easiness 3 of 3 at 75 seconds a trial. Round three
failed `difficult` again, and the note is the one to read: "the shipped
kept/inside helpers are already correct, so the work reduces to replacing an
origin-to-head diff with a per-revision walk and changing should_raise to 'now
and not before'. A competent undergraduate could do this in well under a day."

That was accurate. The whole reference was 98 lines and its intellectual
content was one insight, so no wording change could reach it. **The count of
defects is not the difficulty; the depth of the least legible one is, and a
mechanism whose core is one insight is a half-day task however it is
described.**

What changed is the mechanism, not the brief. Threads now carry spans rather
than a line, have states that replies and resolutions move them through, and
merge by overlap to a fixed point. Twelve decisions are graded where two were
before, four of them need history no single revision supplies, and the
reference is about a hundred and forty lines. This is guard-mark-unwind's
shape - many stated rules whose interactions are the work - which is the only
bundle here that has cleared both probes.

## Earlier quality-review rejection, 2026-09-04, and what changed

Failed on four blocking criteria: `difficult`, `difficulty explanation
quality`, `instruction concision`, `no extraneous files`. The fixes:

- **difficult**: the brief stated the method. It said carry "one revision at a
  time", said what `pin.py` settles is what the board carries notes through,
  said `grp.py` says where a change begins and ends, and shipped a correct
  `rule.py` so the work was one file. The method sentences are gone, and
  `rule.py` now ships wrong in both of its functions, so the work is three
  independent decisions across two files rather than one careful replay.
- **difficulty explanation quality**: it omitted who does this for a living
  and what the streams actually are. Both are now stated, including that the
  streams are synthetic token lists and why that distribution is chosen.
- **instruction concision**: 926 words to 603. Narrative preamble, oblique
  phrasing and the paragraph describing verifier internals are gone.
- **no extraneous files**: `authoring/probe*.py` deleted (scratch, hardcoded
  paths, calls to a function that no longer exists); `readings.py` rewritten
  self-contained; `cheat_report.py` no longer imports anything outside the
  bundle.

`authoring/variants/` stays: `guard-mark-unwind` and `share-register-screen`
both ship variants and both cleared this review.

## Gates run (2026-09-04, Linux sandbox, Docker up)

- real two-image trial `--all`: **17/17** (oracle 1, nop 0, 15 cheats 0)
- real two-image trial `--variants`: **4/4** score 1
- `build_gt.py`: reference and sealed oracle agree on 15 hand-written and 360
  generated streams
- `textcheck` clean against all three briefs that cleared the AI screen;
  `structcheck` and `hintcheck` clean
- `preflight` clean of errors

## Gates NOT run

- the three-agent easiness probe (the important one)
- `onelinecheck`: the task ships no `authoring/decisions.py` in the format that
  tool wants. The wrong readings are measured instead by
  `authoring/readings.py`, which is self-contained and fails if any reading
  moves under a tenth of the set; its numbers are the table above.
- the apt layer, so `pkill` is unexercised; `tests/reap.py` walks `/proc`.

## 2026-09-04: the quality-review repair on `test instruction alignment`

The bundle failed the quality review on two blocking criteria. This session
fixed one of them completely and did not fix the other.

### Fixed: `test instruction alignment`

The reviewer named three corners the brief left undecided that the generated
streams exercise. All three reproduced. A sweep for others of the same class
found two more the reviewer had not named, one of them larger than any of the
three. Measured against the reference over 300 generated streams:

| corner | moves | now |
|---|---|---|
| talk aimed at an absorbed thread lands on its owner | 18.3% | stated, fixture, cheat |
| merging runs before the replies rather than after | 12.7% | stated, fixture, cheat |
| a resolved thread stops being tracked as reached | 4.0% | stated, fixture, cheat |
| a reply moves a resolved thread back to answered | 3.7% | stated, fixture, cheat |
| the merged thread keeps its own reach, not either half's | 0.3% | stated, fixture, cheat |

Two of the five were closed by making the **reference uniform** rather than by
adding a rule: it had two unstated exceptions (a resolved thread stopped having
its reach settled, and a merge discarded the absorbed half's reach), and
removing both makes the brief correct as it already stood. That matters because
the other blocking criterion is `difficult`, so every sentence added to the
brief costs something. Only the event order and the talk semantics needed new
prose, about sixty words.

`raise-on-one-line-of-the-span` graded nothing. Its change was a lone
replacement of the one line of the span the change touched, so that line fell
out of the span in the carry and the fixture produced an empty log - identical
to `no-raise-when-the-change-misses`, the fixture it is supposed to contrast
with. A lone deletion produces no change group at all under `grp.spans`, so a
raise needs the group to reach a **kept** line of the span, which only happens
where two edits sit close enough to take the kept lines between them. The
replacement fixture does that and leaves two lines of the span outside the
group.

`authoring/readings.py` now fails a reading that neither moves a tenth of the
generated set nor is separated by a named hand-written stream. Seventeen
readings, all seventeen pinned by a fixture.

### Not fixed: `difficult`

Round four on one mechanism, and rounds one and three failed it too. See
CLAUDE.md, "note-carry-forward and the wall two criteria make together". No
wording change was attempted, because the repo has measured twice that wording
does not move this criterion, and the alignment repair pushes it the wrong way.

### Gates

Host emulation only - docker is absent on this host, so `authoring/trial.py`
was written for it. It stages the tree the way `tests/Dockerfile` does
(`pristine` beside `tests/`), runs the real `tests/runner.py` in a subprocess
and grades with the real `tests/test_outputs.py` under pytest 9.1.1.

- trial `--all`: 24 of 24. Oracle 1, nop 0, twenty-two cheats 0
- trial `--variants`: 4 of 4 score 1
- every rule cheat is caught by `test_the_fixed_streams_match_the_rule`, so the
  hand-written set separates it and not only the generated block
- `cheat-probe-rewrite-frozen.sh` is caught by the executed-tree check and by
  nothing else
- `build_gt.py`: 22 hand-written and 360 generated streams, reference against
  the sealed oracle
- `readings.py` 300, `simcheck`, `solvecheck`, `deadfieldcheck`, `catcheck`,
  `structcheck`, `hintcheck` clean; `textcheck` clean against all three briefs
  that cleared the AI screen; `preflight` no errors
- NOT covered by the emulation: the privilege drop, the root-owned reward
  channel, the root-only ground truth, `reap.py`, and the POSIX-only probes
- NOT run: the three-agent easiness probe
