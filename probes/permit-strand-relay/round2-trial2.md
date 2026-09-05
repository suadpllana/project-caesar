Agent trajectory

permit-strand-relay__fB9x2KF

6 steps · 4 tool calls
Live

[brief omitted: the agent's own words only, per CLAUDE.md]

I'll start by reading the machine under `/app/lnk/`, the four policy files, and the driver, then trace how the current policy fails on the strand case.

Bash(find . -type f | sort && echo ---- && cat relay.py && echo ---- && for f in lnk/*.py; do echo "=== $f"; cat "$…)

./cases/handover.json
./cases/lull.json
./cases/strand.json
… +258 lines (click to expand)
Bash(for f in pol/*.py; do echo "=== $f"; cat "$f"; done; echo ----; for c in cases/*.json; do echo "=== $c"; cat "…)

=== pol/adm.py
from lnk.book import LINK
… +538 lines (click to expand)
Thinking… (click to expand)
Bash(cat > pol/rtn.py <<'EOF' """Shared policy state and the accounting of rows the relay has finished with. State …)

=== cases/handover.json
["grant", 3, -1, 140]
["grant", 3, 0, 60]
… +100 lines (click to expand)
Thinking… (click to expand)
Bash(cat > /tmp/gap.json <<'EOF' {"ticks": 20, "feeds": [0,1], "ev": [ [0,"a",0,30],[1,"a",0,12],[2,"x",0,0],[2,"a"…)

["over", 1, 0, 12]
["drop", 2, 0, 30]
["late", 2, 0, 10]
… +58 lines (click to expand)
All four policy files are rewritten and the relay now holds and releases rows correctly. Nothing under `/app/lnk/` was touched.

**What was wrong**

- **The link never got its permit back.** The link ceiling only counted drawn rows. Dropped and late rows were charged to the link and then forgotten, so after the three drops in strand the link sat at 120 with 117 sent, and nothing could land again.
- **No three-tick lag.** Admission read the published figure the instant it was published, instead of the figure the producer had actually learned.
- **Teardown gap ignored.** A torn-down feed went straight to `over`, with no `late` window and no link check inside it.
- **Reopen kept old figures.** The old run's published ceilings leaked into the fresh run.
- **Publishing scanned every feed every tick.** On a wide stream that would have been far too slow.

**What the new policy does**

- `pol/rtn.py` owns the shared state: a per-level history of published figures, the link's total of thrown-away rows, a dirty set of levels to examine at tick end, and a schedule of ticks at which a feed may have gone idle. It answers "what has this producer learned by tick T" by scanning the history back to the newest figure at least three ticks old, falling back to the window.
- `pol/adm.py` charges an arrival against the learned feed and link figures. A torn-down feed inside its three-tick gap gets `late` unless the link would overflow, and `over` afterwards.
- `pol/tear.py` adds dropped and late rows to the link's finished total and forgets a feed's history on teardown and reopen.
- `pol/emit.py` only visits dirty levels and feeds that just crossed the idle mark. It grants on a raise of twenty or more or under the five-row rule, and pulls an idle feed to its floor above what it has drained.

**Results**

- Strand now flows: the link grants 159, 198 and 237 alongside the three drops, feed 3 lands every batch, and it ends with nothing parked and no `over` at all.
- Handover and lull run cleanly with the expected grants and idle pulls.
- A hand-built case covering teardown with parked rows, late batches, link overflow inside the gap, reopen in the same tick as a teardown, and lagged refusals after a grant behaved exactly as the rules describe.
- A synthetic wide stream of 9000 feeds over 120000 ticks ran in about 1.4 seconds, well inside the ten-minute budget.

One judgment call to flag: I kept the existing idle convention, where a feed is pulled at the tick exactly seven after its last accept or reopen, since the description did not mark that behaviour as wrong.