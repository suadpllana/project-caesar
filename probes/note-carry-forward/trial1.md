**What was wrong**

- `note/board.py` jumped each note straight from its opening revision to the head with one longest-common-subsequence match, so a note whose line was deleted could reattach to a lookalike line typed in later. It also only checked raises against the final revision.
- `note/rule.py` used its own LCS instead of the settled change script from `scr/pin.py`, so it disagreed with the script the rest of the tool uses whenever several equal-length scripts exist.

**What I changed**

- `note/rule.py`: `kept` now walks the script from `pin.script` and `pin.reading` and maps kept before-lines to after-lines. `raised` asks whether the line falls in any hunk from `grp.spans`. A small `touched` helper returns that set once per revision.
- `note/board.py`: `build` replays the store revision by revision. For each new revision it retires notes whose line the script deletes, moves the survivors, raises those landing inside a hunk, then admits the notes opened at that revision and merges any that share a line, lower id owning the line. Log entries per revision are retirements, raises, then absorbs, each in ascending note order.

**Driver output now**

```
guard.txt   -> retire 0                       (no live notes)
repeat.txt  -> note 0 1                       (carried through both deletions)
rework.txt  -> retire 0, retire 1             (both edited lines went)
```

A hand test with notes opened mid-stream on an occupied line logged `absorb 0 2` and kept the older note, as specified.

One judgment call to flag: raising follows `grp.spans` exactly, which treats only added lines and kept lines sandwiched between nearby changes as part of the change. Kept 