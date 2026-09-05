Agent trajectory

permit-strand-relay__UTZ3mpu

8 steps · 6 tool calls

[brief omitted: the agent's own words only, per CLAUDE.md]

I'll start by reading the machine under `/app/lnk/`, the four policy files, and the driver.

Bash(find . -type f | sort && echo ---- && cat relay.py && echo ---- && for f in lnk/*.py; do echo "=== $f"; cat $f…)

./cases/handover.json
./cases/lull.json
./cases/strand.json
… +258 lines (click to expand)
Bash(for f in pol/*.py; do echo "=== $f"; cat $f; done; echo ----; for c in cases/*.json; do echo "=== $c"; cat $c;…)

=== pol/adm.py
from lnk.book import LINK
… +538 lines (click to expand)
Thinking… (click to expand)
Bash(cat > pol/adm.py <<'EOF' from lnk.book import IDLE, LAG, LINK, WINF, WINL def _window(level): return WINL if l…)

== cases/handover.json
["grant", 3, -1, 140]
["grant", 3, 0, 60]
… +100 lines (click to expand)
Thinking… (click to expand)
Bash(python3 - <<'EOF' import json, random random.seed(1) # wide stream: 10500 feeds, 160000 ticks, each feed activ…)

118 ["grant",
      3 ["late",
  67500 ["over",
… +70 lines (click to expand)
Wide stream ran in under three seconds, so timing is safe. Let me hand-check a stretch of the random stream around a teardown, late arrivals, and a reopen.

Bash(python3 - <<'EOF' import json ev=json.load(open('/tmp/rnd.json'))['ev'] for e in ev: if e[0] <= 12: print(e) E…)

[3, 'x', 1, 0]
[5, 'a', 3, 7]
[5, 'a', 3, 15]
… +72 lines (click to expand)
Bash(python3 - <<'EOF' import json ev=json.load(open('/tmp/rnd.json'))['ev'] for e in ev: if 12 < e[0] <= 15 and e[…)

[15, 'a', 0, 14]

[stdout]
… +2 lines (click to expand)
All checks pass. The traced stretch of the random stream matches the rules line by line: a teardown with parked rows drops them, arrivals in the three‑tick gap are late, an arrival on the tick after the gap is over, the small‑grant rule fires when the standing ceiling leaves fewer than five rows, and a batch that would push a feed past its learned ceiling is refused.

**What was wrong**

- **Link permit was never handed back for rows we threw away.** Only drawn rows counted as finished at the link level. Once three feeds were torn down with rows parked, the link stayed charged for them forever and every later batch was refused.
- **Admission ignored the lag.** The verdict compared against the figure just published rather than the one the producer had actually learned. The teardown gap and late handling were missing too.
- **Feed ceilings were built from a private tally** rather than the book's own drawn counts, and the tally was not reset cleanly across reopens.
- **Every publish scanned every feed**, which would not have survived the wide graded streams.

**What I changed, in the four policy files only**

- `pol/adm.py` keeps a per‑level schedule of published figures and the one currently in force, three ticks after publication, defaulting to the window. A down feed inside its gap yields late, subject to the link check, and over afterwards. Refused rows are tallied per feed so the small‑grant test uses what the producer believes it has sent, while the link test uses our own count.
- `pol/rtn.py` derives finished rows from the book: drawn rows for a feed, drawn plus thrown‑away rows for the link.
- `pol/tear.py` accumulates dropped and late rows into a link total, and on reopen forgets the old run's schedule and refusal tally.
- `pol/emit.py` only examines the link and the feeds that changed this tick or are due an idle check, so cost tracks activity rather than feed count. It publishes a grant when the raise clears the threshold or the small‑grant rule applies, and a pull only for the idle floor.

**Verification**

- `strand.json` now grants link permit on each drop and the fourth feed lands every batch, with nothing left parked.
- `handover.json` and `lull.json` produce grants and idle pulls consistent with the ground rules.
- A synthetic wide stream with over ten thousand feeds and one hundred sixty thousand ticks finishes in about three seconds.

Nothing under `/app/lnk/`, `/app/relay.py`, or `/app/cases/` was touched.