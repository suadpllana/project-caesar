Agent trajectory

permit-strand-relay__PRc9fjY

6 steps · 4 tool calls
Live

[brief omitted: the agent's own words only, per CLAUDE.md]

I'll start by reading the machine under `/app/lnk/`, the four policy files, and the driver.

Bash(find . -type f | sort && echo ---- && cat relay.py && echo ---- && for f in lnk/*.py; do echo "=== $f"; cat $f…)

./cases/handover.json
./cases/lull.json
./cases/strand.json
… +258 lines (click to expand)
Bash(for f in pol/*.py; do echo "=== $f"; cat $f; done; echo ----; for f in cases/*.json; do echo "=== $f"; head -c…)

=== pol/adm.py
from lnk.book import LINK
… +466 lines (click to expand)
Thinking… (click to expand)
Bash(cat > pol/rtn.py <<'EOF' from collections import deque from lnk.book import IDLE, LAG, LINK, WINF, WINL def st…)

from collections import deque

from lnk.book import IDLE, LAG, LINK, WINF, WINL
… +140 lines (click to expand)
Thinking… (click to expand)
Bash(grep -c '"x"\|"o"' cases/*.json; python3 - <<'EOF' import json, random, subprocess, time # gap / reopen case e…)

cases/strand.json:3
cases/handover.json:0
cases/lull.json:0
… +42 lines (click to expand)
All four policy files are rewritten and the relay now holds and hands back rows correctly.

**What was wrong**

- Admission checked arrivals against the figure just published, not the one the producer had learned three ticks later, and treated any torn-down feed as an immediate `over`, so the teardown gap never produced `late`.
- The link ceiling counted only drawn rows. Dropped and late rows never returned their link permit, so after the three teardowns in `strand` the link stayed pinned.
- Reopening cleared per-feed tallies but nothing tracked which figures a fresh run should forget.
- `emit.plan` scanned every open feed every tick, which would not survive a nine-thousand-feed stream.

**What the four files do now**

- `pol/rtn.py` keeps a per-level history of published figures and answers what a producer has learned at a given tick, defaulting to the window until something has aged in. It also holds the shed total for the link and a dirty set plus an idle-due schedule.
- `pol/adm.py` refuses on either level against the learned figures, returns `late` for arrivals inside the three-tick gap after a teardown when the link allows them, and `over` otherwise.
- `pol/tear.py` adds dropped and late rows to the link's finished total, and on reopen forgets the old run's published figures and reschedules its idle check.
- `pol/emit.py` evaluates the link every tick and only the feeds that changed or fell due for idleness, applying the threshold rule, the small-grant rule against the standing figure, and the idle pull.

**Results**

`strand` now grants the link back after each drop and feed 3 lands every batch, with nothing parked at the end. `lull` and `handover` publish grants and idle pulls in line with the rules. A synthetic stream with arrivals inside the gap, a reopen in the same tick as a teardown, and an oversized batch behaved as specified. A synthetic wide stream of nine thousand feeds over a hundred and ten thousand ticks ran in about 1.2 seconds. Nothing under `/app/lnk/` was touched.