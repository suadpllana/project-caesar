Agent trajectory

permit-strand-relay__pALSU4U

6 steps · 4 tool calls
Live

[brief omitted: the agent's own words only, per CLAUDE.md]

I'll start by reading the machine under `/app/lnk/`, the four policy files, and the driver.

Bash(find . -type f | sort && echo ---- && cat relay.py && echo ---- && for f in lnk/*.py; do echo "=== $f"; cat $f…)

./cases/handover.json
./cases/lull.json
./cases/strand.json
… +258 lines (click to expand)
Bash(for f in pol/*.py; do echo "=== $f"; cat $f; done; echo; for c in cases/*.json; do echo "=== $c"; head -c 1500…)

=== pol/adm.py
from lnk.book import LINK
… +538 lines (click to expand)
The machine is clear now. The link never learns that dropped or late rows have left, and there's no three-tick lag anywhere. Writing the four policy files.

Bash(cat > pol/rtn.py <<'EOF' from lnk.book import LINK def fin(st): return st.setdefault("fin", {}) def freed(st, …)

== cases/handover.json
["grant", 3, -1, 140]
["grant", 3, 0, 60]
… +100 lines (click to expand)
The three sample streams now behave. Next I'll check the teardown gap, reopen, and lag with a synthetic stream, and time a wide stream.

Bash(cat > /tmp/gap.json <<'EOF' {"ticks": 20, "feeds": [0, 1], "ev": [ [0,"a",0,10], [1,"x",0,0], [1,"a",0,10], [2…)

["drop", 1, 0, 10]
["late", 1, 0, 10]
["grant", 1, -1, 140]
… +54 lines (click to expand)
All four files are rewritten and the relay now hands permit back correctly.

**What was wrong**

- Dropped and late rows never freed link permit. Only drawn rows counted as finished at the link, so after the three teardowns the link sat at its opening figure of 120 with 117 rows already charged, and every batch from feed 3 was refused.
- No lag existed. Admission read the figure the machine had just published, not the one the producer had learned, and nothing tracked in-flight ceilings.
- The publish pass walked every open feed each tick, which would not survive a wide stream.

**What the four files now do**

- `pol/rtn.py` keeps one finished-rows tally per level. A draw frees rows at the feed and the link and marks the feed for review at tick end.
- `pol/tear.py` credits dropped and late rows to the link only. Reopening wipes the feed's tally and its learned ceiling so the new run starts from the window, and schedules its idle check.
- `pol/emit.py` computes ceilings as finished rows plus window or floor, applies the threshold and small-grant rules against the standing figure, and records each publication with its arrival tick three ticks later. It only reviews the link, feeds touched this tick, and feeds whose seven-tick idle deadline falls on this tick.
- `pol/adm.py` refuses against what the producer has learned at both levels. Inside the three-tick teardown gap an arrival is late unless it would carry the link past its learned figure, in which case it is an over. After the gap everything is an over.

**Results** on the strand stream: the link is granted 159, 198 and 237 as the three feeds drop, feed 3 lands its first batch at tick 16, and grants alternate with draws from then on. Nothing is left parked, since every batch is drawn. The handover and lull streams also run cleanly. A synthetic stream confirmed late, over, reopen and lag behavior tick by tick, and a generated wide stream of nine thousand feeds over one hundred twenty thousand ticks finishes in about 1.3 seconds.

One judgment call to flag: a feed that has accepted nothing since the stream began is pulled to the floor at tick 7, as the idle rule reads literally. The strand output already showed that line before my change and I kept it.