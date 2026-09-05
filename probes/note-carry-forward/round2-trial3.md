# note-carry-forward__YoHRKou (easiness round 2, 2026-09-05)

8 steps, 6 tool calls. Agent's own words only.

---

I'll start by reading the code and the streams.

Bash(find . -type f | grep -v __pycache__ | sort && cat rev/store.py scr/pin.py scr/grp.py note/board.py note/rule....)

Bash(for f in streams/*.txt; do echo "== $f"; cat $f; echo "-- output"; python3 run_review.py $f; done)

Bash(cat > note/rule.py <<'EOF' from scr import grp from scr.pin import script, reading def kept(before, after): ou...)

Let me check the settled scripts for repeat.txt to confirm that span is what the script implies.

Bash(python3 -c " from scr.pin import script, reading from scr.grp import spans a='a|b|a|b|a|b|a|b'.split('|'); b='...)

Both carries follow the settled script, so the repeat result is consistent. One more hand-made
stream to exercise raise, reopen, and squeeze-merging.

Bash(cat > /tmp/t.txt <<'EOF' rev a|b|c|d|e|f|g|h|i|j open 0 1 2 open 1 5 6 reply 0 resolve 1 open 2 8 9 rev a|b|c|...)

Bash(cat > /tmp/t2.txt <<'EOF' rev a|b|c|d|e|f|g|h open 0 1 2 reply 0 open 1 5 6 resolve 1 rev a|b|c|d|e|f|g|h open...)

---

Done. Both files are rewritten and the three shipped streams plus two hand-made ones behave as
the rules describe.

**What was wrong and what changed**

- `note/rule.py`: `kept` ran its own longest-common-subsequence and could pick a different
  alignment than the settled script. It now derives the line mapping from the K steps of
  `scr.pin.script` read through `reading`. `touched` demanded every span line be reached and
  now fires on any shared line. `merges` required identical spans and now fires when spans
  share a line.
- `note/board.py`: outdated threads were deleted from the table. They now stay with state
  `outdated` and an empty span, and are skipped by carrying, raising, talk and merging. Each
  thread carries a reached flag, so a raise is logged only on the transition from unreached to
  reached, resolved threads are tracked but never raised, and a raised answered thread goes
  back to `open` with a `reopen` logged directly after. Merging loops to a fixpoint so a union
  can pull in a third thread, the survivor becomes `open` if either was, and inherits reached
  if either had it. The returned table exposes only id, span and state.

**Results on the shipped streams**

```
guard.txt   thread 0 outdated -      log: outdated 0
repeat.txt  thread 0 resolved 0      (carried 2,3,4 -> 0,1,2 -> 0 along the settled script,
                                      which deletes the leading a|b each time)
rework.txt  thread 0 answered 2 / thread 1 open 4
```

**One judgment call to know about.** Reached is judged on the carried span against the hunk
sets `scr.grp.spans` returns, which are in head-revision coordinates. A pure deletion inside a
span with no nearby addition produces no hunk lines, so it does not raise the thread. That
follows the frozen grp output rather than an extra rule I invented.
