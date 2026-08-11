# Task state

Working memory for this task. Assume the next session starts with no memory of this one.

## Current stage

`Stage 7 - Pre-flight and packaging` (bundle complete and re-hardened after an easiness probe;
gates re-run, see Validation status)

## Assistant's assigned role

"You are a firmware engineer on a rack team; you own the apply path that puts rail settings on
a slow control bus, and the budget you are judged on is a transaction count rather than a
clock."

Assigned implicitly by the contributor's choice of category (Software / Systems). The
`relevant_experience` in `task.toml` is the contributor's own and is deliberately honest about
not being a firmware background.

## Source repository (repo-based tasks only)

- Repo URL: none - idea-based task. The part, its datasheet, the bench model and the shipped
  apply path under `environment/app/` are authored for this task.

## Task summary

A power-management part on a compute sled takes batches of rail settings from a rack
controller. One editable file, `/app/src/driver.c`, turns a batch into bus transactions. The
shipped path replays the batch as it arrives and is correct; it costs 6.09x what a well-made
path costs. Grading is a transaction count against a ceiling of 1.10x what the reference
planner in `/tests` spends on the identical sessions, plus a correctness floor (45 named
sessions, 12 generated from a run-time seed, 8 long ones) that a careless optimisation faults.

## Why it is hard

Four ideas, each stated in `/app/README.md` or the brief and none of them concluded. The
ceiling is set so that an otherwise flawless apply path missing **any single one** lands
outside it, and so that one which has all four and packs its frames by hand rather than by
dynamic programming lands inside with three to five percent to spare.

1. **The batch is a target, not a script.** The disables the config layer asks for before a
   retrim do not have to happen. Performing them: 1.26x.
2. **The pair register (`SLED_PAIR`).** Sixteen bits, both halves landing in the same beat, so
   it is checked only against itself. It therefore walks a live rail downwards in one write
   *and* carries a one-half change by restating the other half - which is the part most
   readings miss, because the register looks like it is "for" rails where both halves move.
   Using it only there: 1.23x. Never using it: 1.30x.
3. **The frame, and what may ride inside one.** Two transactions for up to eight consecutive
   registers of a bank. Never restating an untouched neighbour: 1.27x. Restating without
   checking: would be 0.96x, and faults - a rail parked under its own limit refuses a restated
   pair word (`PAIR_INVERTED`) and a restated voltage (`VSET_OVER_ILIM`), while restated limits
   and enables are always safe. There is deliberately **no** fair route that declines to pad.
4. **Settling.** A mode change costs two looks at the status register before the part will take
   a single write, and a staged frame is exempt because its preamble covers the settling. Lead
   every mode window with a frame and it is free. Paying it: 1.23x.

- Expert time estimate: 14 hours
- Why a frontier agent cannot one-shot it: each idea on its own is reachable from the
  datasheet, but the run is graded on all four at once against a ceiling that is never quoted,
  and a merely expensive run looks exactly like a fine one from inside. The earlier revision of
  this task (no pair register, no settling cost, four-word frames, ceiling 1.15x) was solved
  3/3 by a frontier model in an easiness probe; ideas 2 and 4 and the removal of the
  decline-to-pad route are the response to that.

## Verifier contract - FROZEN

- The apply path never runs in the process that decides anything. `driver.c` is compiled by the
  unprivileged `verifier` account against `/probe/runner.c` and `/probe/include/sled.h` from
  the verifier image; the binary asks for bus transactions on a pipe.
- The part model, the fault rules, the sessions, the reference planner and the counter are
  Python in `/tests`, root-owned, mode 700.
- `pytest` writes a verdict carrying a `/dev/urandom` nonce; `test.sh` refuses a reward on an
  exit code alone. `crosscheck.py` re-grades with its own seed and its own build, no pytest.
- `/app/include/sled.h`, `/app/src/sandbox.c` and `/app/Makefile` are fingerprinted against
  `/tests/pristine` before any session runs.
- The 45 named case ids are asserted present individually, and 45 is written down in
  `test_driver.py` rather than counted from `cases.py`.

## Decisions and their reasons

- **`SETTLE_LOOKS = 2`** rather than one. With one look the frame exemption is worth about six
  percent, which is under the noise band a fair ceiling has to leave; with two it is worth
  twenty-three and can carry a gate of its own.
- **`BURST_MAX = 8`** rather than four. Wide frames are what make padding compulsory and what
  make a dense pair bank pay, which is what turns idea 2 into a gate rather than a nicety.
- **The pair register cannot express a parked rail** (voltage over limit). That keeps the
  voltage and limit banks load-bearing, keeps the ordering rules alive, and gives the padding
  trap its teeth.
- **Session mix**: roughly two fifths of the rails a batch touches move one half only. That is
  what separates "pairs everything" from "pairs where both halves move".
- **Ceiling 1.10x**, from the measured table in the docstring of `/tests/plan.py`.
- The instruction deliberately no longer editorialises about which rules matter; the datasheet
  states them and draws no conclusions.

## Validation status

Measured with `part.py` counting, 8-session groups of 20 rails x 10 batches, 20 independent
groups:

| profile | min | max | verdict |
|:--- |:--- |:--- |:--- |
| all four ideas, DP packer | 1.000 | 1.004 | pass |
| all four ideas, hand packer | 1.052 | 1.070 | pass |
| pays the status read | 1.207 | 1.252 | fail |
| pairs only where both halves move | 1.251 | 1.345 | fail |
| obeys the disables | 1.265 | 1.404 | fail |
| no padding | 1.313 | 1.404 | fail |

- `solution/driver.c` matches the Python planner transaction for transaction on every session
  either has been run against, and passes `pytest test_driver.py` (50 tests) on several seeds
  and `crosscheck.py`.
- The shipped `environment/app/src/driver.c` passes every correctness test and fails only
  `test_long_run_inside_the_ceiling`, at 6.09x.
- All three `cheat/` drivers still compile against the new header and fall through to the
  shipped behaviour; the two that can be run outside the container score 0 on cost.
- Reckless padding faults 4 of the 45 named cases and about one generated session in seven;
  sending each limit before its voltage faults 11 of 45 (23 if it also never pairs).
- Hill-climbing the pair-versus-split routing choice with the reference's own cost function
  beats the reference by 0.5%, so the ceiling is not measured against a straw planner.

## Open questions and next steps

- Re-run the easiness probe. The target is at most one solve in three.
- If it still comes out easy, the next lever is the session mix rather than the part: raising
  the share of parked rails widens the gap between a planner that reasons about pad legality
  per bank and one that treats all four banks alike.
