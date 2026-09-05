# Round 3 easiness probe, 2 of 3 solved (2026-09-05)

Trial 1 (L7br5fJ) and trial 3 (zcG4WG8) solved. Trial 2 (wweSnRN) failed.

The failing agent is identified by its own flagged judgment call: it counts a line the
script DELETES as reached, on top of the lines `grp.spans` reports. Trials 1 and 3 both
took reach strictly from `grp.spans` against the carried span, and both said so
explicitly -- trial 1 "a hunk that only deletes lines reaches nothing ... I kept that
behaviour because the reader is not mine to change", trial 3 "a reached line is one in a
hunk of the pinned script as grp.spans defines it, taken against the carried span".

The published results confirm it. On `rework.txt` trials 1 and 3 both report
`thread 0 answered 2`; trial 2 reports `thread 0 open 2` with an extra `raise 0, reopen 0`,
which is exactly the extra raise its deletion rule produces.

So the one failure was the single prong-A discovery in the bundle, and the two solves were
transcription. Every other decision -- carry from the pinned script, any-line reach,
overlap merge, outdated stays listed, the reached flag and edge-triggered raise, reopen
placement, the merge fixed point, log order -- was got right by all three, in 4 to 9 tool
calls, with no intermediate wrong version in any trajectory.

## What this says about the two repairs of the previous rounds

Both were found on sight and neither separated anybody:

- **The resource gate** (wide streams, the pair settled once a revision) was the
  2026-09-05 C3 repair. All three agents cached the script per revision pair without
  being prompted, and all three measured their own wide synthetic at about 3 seconds and
  said the 600 s budget was safe. It no longer costs anyone anything.
- **The merge fixed point.** Trials 1 and 3 both reached for union-find unprompted;
  trial 2 used repeat-until-stable, which is also correct. The stated
  "one sweep does not settle it" sentence hands this over.

## Runtimes

4 to 9 tool calls, 6 to 11 steps, against a 14400 s budget. Trial 2 wrote both files in a
single tool call. Nobody had an intermediate wrong version, so no plan was ever revised:
the mode-C signature this repo already documents.
