Agent trajectory

permit-strand-relay__7GNaMMU

11 steps · 9 tool calls

[brief omitted: the agent's own words only, per CLAUDE.md]

I'll start by reading the machine under `/app/lnk/`, the four policy files, the driver, and the test streams.

Bash(find . -type f | sort && echo "-----" && cat /app/relay.py && echo "----- book.py" && cat /app/lnk/book.py)

./cases/handover.json
./cases/lull.json
./cases/strand.json
… +196 lines (click to expand)
Bash(echo "----- mach.py" && cat /app/lnk/mach.py && echo "----- rd.py" && cat /app/lnk/rd.py)

----- mach.py
from lnk.book import Book, LINK
from pol import adm, emit, tear
… +172 lines (click to expand)
Now the four policy files and the three streams.

Bash(for f in adm rtn tear emit; do echo "===== pol/$f.py"; cat /app/pol/$f.py; done)

===== pol/adm.py
from lnk.book import LINK
… +132 lines (click to expand)
Bash(for f in strand lull handover; do echo "===== cases/$f.json"; cat /app/cases/$f.json; echo; done)

===== cases/strand.json
{
 "ev": [
… +794 lines (click to expand)
Let me run the current relay on all three streams to see the baseline behaviour.

Bash(for f in strand lull handover; do echo "===== $f"; python3 relay.py cases/$f.json; done)

===== strand
["pull", 7, 3, 12]
["drop", 11, 0, 39]
… +92 lines (click to expand)
Thinking… (click to expand)
Bash({"command":"cat > /app/pol/rtn.py <<'EOF'\n\"\"\"Return of permit.\n\nWhat each level has finished with, and w…)

===== strand
["pull", 7, 3, 12]
["drop", 11, 0, 39]
… +100 lines (click to expand)
Thinking… (click to expand)
Bash(cat > /tmp/edge.json <<'EOF' {"name":"edge","ticks":20,"feeds":[0,1],"ev":[ [0,"a",0,30], [1,"a",1,6], [2,"x",…)

EDGE STREAM MATCHES HAND-DERIVED EXPECTATION

[stdout]
… +2 lines (click to expand)
Thinking… (click to expand)
Bash(ls -la --time-style=full-iso /app/lnk/ /app/pol/ | grep -v '^total' && echo "----- fuzz" && python3 - <<'EOF' …)

Exit code 1
/app/lnk/:
drwxr-xr-x 2 root root 4096 2026-09-05 12:13:48.047991727 +0000 .
… +18 lines (click to expand)
Thinking… (click to expand)
Bash(python3 - <<'EOF' import random, sys sys.path.insert(0, "/app") from lnk import mach as M from lnk.rd import P…)

3000 random streams OK
kinds seen  grant=24599 pull=11895 over=65889 late=4863 drop=4666
… +4 lines (click to expand)
All three sample streams run, the hand-checked edge stream matches, and 3000 random streams pass every invariant with all five row kinds exercised.

## What was wrong

Three faults in the policy layer, all in how permit was handed back and judged:

- **The link never recovered thrown-away rows.** The link's "finished" total counted only drawn rows, so every dropped or late row held link permit forever. In strand the three drops pinned the link at 117 of 120 and feed 3's twelve-row batches were refused to the end.
- **Lost rows were booked to the wrong level and wiped on reopen.** They were credited to the torn-down feed, which is gone, and then erased by `tear.opened`. They belong to the link, whose totals never restart.
- **Admission ignored the three-tick lag and had no `late` path.** Batches were judged against the standing ceiling rather than the one the producer had learned, and rows landing in a teardown gap were refused instead of being charged to the link, thrown away and written down as `late`.

## What I changed

- `pol/rtn.py` now credits the link with drawn plus thrown-away rows, keeps a per-level publication history, and answers what a producer has learned at a given tick. A ceiling published at tick p is usable from tick p+3.
- `pol/tear.py` accumulates thrown-away rows as one link-wide total, clears only the feed's publication history on reopen, and reports whether a teardown is still in flight.
- `pol/adm.py` judges live feeds against learned ceilings at both levels, returns `late` inside the gap when the link alone would accept, and `over` otherwise.
- `pol/emit.py` keeps the grant and pull rules and records each published ceiling so the lag can be applied.

Nothing under `/app/lnk/` was touched. Its files still carry their original timestamps.

## Verified behaviour

Strand now ends with the link granted to 357 and feed 3 to 160, with every batch from tick 16 onward accepted. Lull and handover are unchanged. My edge stream confirmed the paths the samples never reach:

- Rows landing in the teardown's own tick and the two after it are `late`. The third tick after is `over`.
- A reopened feed starts fresh at 40 with the window known at once.
- A batch three ticks after a grant is accepted while one two ticks after is refused.
- The small-grant rule fires when the producer has under five rows left and the raise is under twenty.
- Draws and teardowns on gone or unknown feeds are silent.

The fuzz confirmed that every grant is strictly above the standing ceiling, pulls apply only to feeds and only downward, and every row charged to the link is either drawn, parked or thrown away.