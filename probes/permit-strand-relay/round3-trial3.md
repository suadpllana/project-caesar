Agent trajectory

permit-strand-relay__xfnHs9w

6 steps · 4 tool calls

[brief omitted: the agent's own words only, per CLAUDE.md]

I'll start by reading the machine, the policy files, and the cases.

Bash(find . -type f | sort && echo ---- && cat relay.py && echo ---- && for f in lnk/*.py; do echo "=== $f"; cat $f…)

./cases/handover.json
./cases/lull.json
./cases/strand.json
… +258 lines (click to expand)
Bash(for f in pol/*.py; do echo "=== $f"; cat $f; done; echo ----; for f in cases/*.json; do echo "=== $f"; cat $f;…)

=== pol/adm.py
from lnk.book import LINK
… +538 lines (click to expand)
Thinking… (click to expand)
Bash(cat > pol/rtn.py <<'EOF' """Rows finished with, and what each producer has learned so far.""" from lnk.book im…)

== cases/handover.json
["grant", 3, -1, 140]
["grant", 3, 0, 60]
… +100 lines (click to expand)
The three cases now behave sensibly and I've hand-checked the lull trace. Next: a timing test on a synthetic wide stream, plus a teardown/reopen edge stream.

Bash(python3 - <<'EOF' import json, random random.seed(1) F=10000; T=160000 ev=[] for fd in range(F): s=random.rand…)

119767
      6 ["drop",
     72 ["grant",
… +46 lines (click to expand)
All done. The relay now takes rows again, and the wide-stream timing is well inside budget.

**What was wrong**

- **Link permit never came back.** Dropped and late rows were tracked per feed, but the link's finished count ignored them. After the three teardowns in the strand case, the link sat at 117 of 120 sent forever, so feed 3 could never land a batch.
- **Admission used the wrong figure.** It checked against the value just published, not the one the producer had actually learned three ticks later.
- **Refusals were invisible to the small-grant test.** A turned-away batch counts as sent from the producer's side, and the test ignored that.
- **Every feed was scanned every tick.** On a wide stream that is billions of checks.

**What I changed, in the four policy files only**

- `pol/rtn.py` now holds a per-level schedule of published figures with their effective ticks, so admission asks what the producer knows at this tick. It also tracks the producer's own view of rows sent, refusals included, and marks feeds that need a publish decision.
- `pol/adm.py` refuses on either level against the learned ceiling. Inside the three-tick teardown gap it returns late unless the link would be exceeded. It also schedules the idle check seven ticks after each acceptance.
- `pol/tear.py` accumulates lost rows for the link, and on reopen forgets everything the old run learned so the new run starts from the feed window.
- `pol/emit.py` computes the link ceiling as the window plus drawn plus lost rows, and the feed ceiling as drawn rows plus the window or the idle floor. It only visits the link plus feeds touched this tick or crossing the idle threshold.

**Results**

- Strand: the three drops each release link permit as a grant, and feed 3 lands every batch from tick 16 on. No overs remain.
- Handover and lull produce the expected alternating grants and idle pulls. I traced lull by hand against the rules and it matches.
- A synthetic edge stream with same-tick arrival plus teardown, reopen and re-teardown, double teardowns and double reopens behaves as specified.
- A synthetic wide stream of ten thousand feeds over 160,000 ticks runs in about three seconds.

Nothing under `/app/lnk/` was touched.