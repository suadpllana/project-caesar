Agent trajectory

permit-strand-relay__w64rYoN

7 steps · 5 tool calls

[brief omitted: the agent's own words only, per CLAUDE.md]

I'll start by reading the machine under `/app/lnk/`, the four policy files, and the driver.

Bash(find . -type f | grep -v __pycache__ | sort && echo ---- && cat relay.py && echo ---- && for f in lnk/*.py; do…)

./cases/handover.json
./cases/lull.json
./cases/strand.json
… +258 lines (click to expand)
Bash(for f in pol/*.py; do echo "=== $f"; cat $f; done; echo; for c in cases/*.json; do echo "=== $c"; head -c 600 …)

=== pol/adm.py
from lnk.book import LINK
… +467 lines (click to expand)
Thinking… (click to expand)
Bash(cat > pol/rtn.py <<'EOF' """Return of permit: what each level has finished with, and learned ceilings. Shared …)

== strand
["pull", 7, 3, 12]
["drop", 11, 0, 39]
… +100 lines (click to expand)
Thinking… (click to expand)
Bash(python3 - <<'EOF' import json, random random.seed(1) ev=[]; F=10500; T=160000 for fd in range(F): s=random.ran…)

3 ["drop",
     59 ["grant",
      3 ["late",
… +64 lines (click to expand)
Thinking… (click to expand)
Bash(python3 -c " import json;d=json.load(open('/tmp/fz3.json')) for e in d['ev']: if e[0]<=42: print(e) " | head -…)

[0, 'x', 0, 0]
[0, 'o', 0, 0]
[3, 't', 0, 0]
… +104 lines (click to expand)
The trace confirms it: at tick 9 the feed was torn down and reopened, so the pull to 30 is 18 drawn plus the floor of 12 on a fresh run, and the surrounding refusals match the lag rule exactly.

## Recap

All four policy files under `/app/pol/` are rewritten. Nothing under `/app/lnk/` was touched.

**What was wrong**
- The link's ceiling only counted drawn rows. Dropped and late rows were charged to the link but never returned, so after the three teardowns in strand the link stayed pinned and every later batch was refused.
- Admission checked the figure the machine had just stored, not the figure the producer had actually learned three ticks later.
- Publishing scanned every open feed every tick, which would not fit a wide stream of ten thousand feeds in the time budget.

**What the new code does**
- `rtn.py` holds the shared state: learned ceilings with a pending list per level that matures after the lag, the rows each producer believes it has sent, and the link's count of rows thrown away. A feed's finished count is its drawn rows. The link's is drawn plus dropped plus late.
- `adm.py` charges against learned figures only. A torn-down feed gets `late` inside its three-tick gap when the link allows it, `over` otherwise, and `over` after the gap.
- `tear.py` records shed rows against the link, resets a reopened feed to a fresh run that knows the feed window at once, and computes the idle floor.
- `emit.py` grants on a raise of twenty or more, or when the standing figure would leave fewer than five rows usable while the new one would not. It pulls an idle feed to drawn plus twelve. Only the link, feeds touched this tick, and feeds whose idle deadline falls on this tick are examined.

**Verification**
- Strand now grants the link back its permit after each drop and accepts every one of feed 3's batches.
- Handover and lull produce the expected grants and idle pulls, checked by hand against the rules.
- Thirty random small streams with teardowns and reopens landing beside arrivals ran without error, and one was traced by hand.
- A synthetic stream of 10,500 feeds over 160,000 ticks runs in about 2.7 seconds.