# note-carry-forward__zcG4WG8  (7 steps, 5 tool calls) -- SOLVED

I'll start by reading the code and the streams.

[Bash] find . -type f | grep -v __pycache__ | sort, then cat run_review.py and rev/store.py
[Bash] cat note/board.py and note/rule.py, then run the driver on the three streams
[Bash] wrote note/rule.py and note/board.py
[Bash] python3 -c ... check the pinned script against grp.spans on a repeating file
[Bash] a hand stream exercising raise/reopen, chained merging, and timing on a wide stream

The pinned script deletes the head of the file, so the thread following it to line 0 is
consistent. Now I'll exercise raise/reopen, chained merging, and timing on a wide stream.

Both files are fixed, and all three streams plus a randomized wide stream behave as the
rules describe.

**What was wrong**

- `rule.kept` ran its own longest-common-subsequence instead of the pinned script from
  `scr/pin.py`. On repeating files it picked a different alignment, which is why the
  thread in `repeat.txt` landed on the wrong lines.
- `rule.touched` required every line of the span to be in a hunk. It now fires when any
  line is.
- `rule.merges` required identical spans. It now checks for a shared line.
- The board deleted outdated threads. They now stay on the table with state `outdated`
  and an empty span, and nothing carries, raises, merges or aims at them afterwards.
- The board had no notion of "reached", so it raised open threads every revision and
  never reopened answered ones. Each live thread now carries a reached flag, settled at
  every revision including resolved ones. A raise happens only on the first reached
  revision after a let-go, and an answered thread gets `reopen` logged right after and
  returns to open.
- Merging was a single sweep. It is now a union-find over line ownership, so chains
  where the union creates a new overlap settle to one holder. The oldest id holds, takes
  the union of spans, is open if any member was open, and is reached if any member was.
  Absorb entries are logged in ascending order of the absorbed thread.

**Results**

    guard.txt   -> thread 0 outdated -   / log: outdated 0
    repeat.txt  -> thread 0 resolved 0   (follows the pinned script, which deletes the file head)
    rework.txt  -> thread 0 answered 2, thread 1 open 4

A hand stream with replies, resolves and three overlapping threads produced outdated,
raise, reopen and chained absorb entries in the required order. A 300-line random file
over six revisions with 360 threads builds in about three seconds, nearly all of it in
the frozen script table, so the wide streams fit the time limit.

**Assumptions I made**

- A newly opened thread starts unreached, and a reached line is one in a hunk of the
  pinned script as `scr/grp.spans` defines it, taken against the carried span.
- When an answered thread absorbs a resolved one, or the reverse, the holder keeps its
  own state. Only an open member forces the survivor open.
- Script readings are cached per revision pair inside `rule.py` so per-thread `touched`
  calls do not recompute the script.
