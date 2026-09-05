Agent trajectory

permit-strand-relay__L95f6Dw

16 steps · 14 tool calls

[brief omitted: the agent's own words only, per CLAUDE.md]

I'll start by reading the machine under `/app/lnk/`, the four policy files, the driver, and the cases.

Bash(find . -type f | sort && echo "-----" && cat /app/relay.py && echo "----- book.py" && cat /app/lnk/book.py)

./cases/handover.json
./cases/lull.json
./cases/strand.json
… +196 lines (click to expand)
Bash(echo "----- mach.py" && cat /app/lnk/mach.py && echo "----- rd.py" && cat /app/lnk/rd.py && echo "----- adm.py…)

----- mach.py
from lnk.book import Book, LINK
from pol import adm, emit, tear
… +213 lines (click to expand)
Bash(for f in cases/*.json; do echo "===== $f"; cat $f; echo; done)

===== cases/handover.json
{
 "ev": [
… +794 lines (click to expand)
Bash(for f in strand handover lull; do echo "===== $f"; python3 relay.py cases/$f.json; done)

===== strand
["pull", 7, 3, 12]
["drop", 11, 0, 39]
… +92 lines (click to expand)
Thinking… (click to expand)
Bash(cat > /app/pol/rtn.py <<'EOF' """Handing permit back: what each level has finished with, and what the producer…)

===== strand
["pull", 7, 3, 12]
["drop", 11, 0, 39]
… +100 lines (click to expand)
Thinking… (click to expand)
Bash(mkdir -p /tmp/chk && cat > /tmp/chk/ref.py <<'EOF' """Independent reference model of the relay spec, written f…)

Exit code 1
python3: can't open file '/tmp/chk/relay.py': [Errno 2] No such file or directory
strand: DIFF
… +56 lines (click to expand)
Wrong working directory for the relay call. Fixing the path and rerunning the comparison.

Bash(cd /tmp/chk && for f in strand handover lull; do python3 ref.py /app/cases/$f.json > ref_$f.txt; (python3 rela…)

Exit code 1
python3: can't open file '/tmp/chk/relay.py': [Errno 2] No such file or directory
strand: DIFF
… +56 lines (click to expand)
Bash(cd /tmp/chk && for f in strand handover lull; do python3 ref.py /app/cases/$f.json > ref_$f.txt; (python3 rela…)

Exit code 1
python3: can't open file '/tmp/chk/relay.py': [Errno 2] No such file or directory
strand: DIFF
… +56 lines (click to expand)
I kept invoking the relay from the wrong directory. Running it from `/app` explicitly.

Bash(cd /tmp/chk && for f in strand handover lull; do python3 ref.py /app/cases/$f.json > ref_$f.txt; (python3 rela…)

Exit code 1
python3: can't open file '/tmp/chk/relay.py': [Errno 2] No such file or directory
strand: DIFF
… +56 lines (click to expand)
Bash(cd /tmp/chk && for f in strand handover lull; do python3 /tmp/chk/ref.py /app/cases/$f.json > /tmp/chk/ref_$f.…)

strand: match
handover: match
lull: match
… +10 lines (click to expand)
Thinking… (click to expand)
Bash(cat > /tmp/chk/fuzz.py <<'EOF' import json, random, subprocess, sys, os sys.path.insert(0, "/tmp/chk") sys.pat…)

ok 3000 streams; row kinds seen: {'over': 84678, 'grant': 31339, 'drop': 6481, 'pull': 10867, 'late': 8728, 'park': 4062}

[stdout]
… +2 lines (click to expand)
Thinking… (click to expand)
Bash(cd /tmp/chk && (python3 fuzz.py 7 4000 & python3 fuzz.py 42 4000 & python3 fuzz.py 99 4000 & wait))

ok 4000 streams; row kinds seen: {'over': 114784, 'grant': 42626, 'pull': 14476, 'late': 11810, 'drop': 8723, 'park': 5354}
ok 4000 streams; row kinds seen: {'grant': 42847, 'over': 117785, 'drop': 8831, 'late': 11667, 'park': 5384, 'pull': 14854}
ok 4000 streams; row kinds seen: {'late': 12001, 'grant': 42884, 'pull': 14480, 'over': 116521, 'park': 5278, 'drop': 8826}
… +10 lines (click to expand)
Bash(cat > /tmp/chk/gap.json <<'EOF' {"name": "gap", "ticks": 30, "feeds": [0, 1], "ev": [ [0, "a", 0, 25], [1, "a"…)

["grant", 2, -1, 150]
["grant", 2, 1, 70]
["drop", 4, 0, 25]
… +28 lines (click to expand)
Thinking… (click to expand)
Bash(find /app -name __pycache__ -type d -exec rm -rf {} + ; find /app -type f | sort; echo "---"; python3 /app/rel…)

/app/cases/handover.json
/app/cases/lull.json
/app/cases/strand.json
… +52 lines (click to expand)
The traceback there is only `head` closing the pipe early; the relay itself is fine. The tree now holds just the source files, and nothing under `/app/lnk/` was touched.

## What was wrong

The machine was sound. All four policy files were mishandling the hand-back:

- **`adm.py`** judged arrivals against the ceiling just published rather than the one the producer had learned, ignoring the three-tick lag. It also sent every arrival on a torn-down feed straight to `over`, so the `late` gap never existed.
- **`rtn.py`** credited the link only with drawn rows. Dropped and late rows kept holding link permit forever. That is why `strand` stuck at a link ceiling of 120 after 117 rows were dropped and refused every batch from feed 3.
- **`tear.py`** kept the thrown-away total per feed and wiped it on reopen, which would have broken the link's carry-over across a reopen.
- **`emit.py`** recorded nothing about when a figure went out, so the lag could not be honoured, and it pulled on any decrease rather than only for the idle fallback.

## What I changed

- **`rtn.py`** now holds the two hand-back rules. The link's finished-with total is drawn rows plus every dropped or late row. A feed's is its own drawn rows. It also keeps a per-level history of published figures and answers "what has the producer learned at this tick", falling back to the starting window when nothing is old enough.
- **`adm.py`** checks both levels against the learned figures. Inside the three-tick gap after a teardown it checks the link only and returns `late`, or `over` if the link would be carried past what was learned. Past the gap everything is `over`.
- **`tear.py`** adds thrown-away rows to one link-wide total that never resets, clears a reopened feed's publish history so its fresh run starts from the feed window, and exposes the idle test.
- **`emit.py`** grants on a threshold raise or the small-grant rule only, pulls only for the idle fallback, and records each published figure with its tick.

## Verification

`strand` now hands the link back 39 rows at each drop (159, 198, 237) and feed 3 lands every batch from tick 16 on. `handover` and `lull` are unchanged. I also wrote an independent model of the spec from the prose alone and compared it against the relay on the three shipped streams and 15,000 random streams with teardowns, reopens, same-tick combinations, tiny batches and unlisted feeds. All agreed, with every row kind exercised. A hand-built stream covering the gap and a same-tick reopen also traced correctly line by line.

One judgment call worth knowing: a reopened feed's producer is treated as knowing the feed window immediately, the same as at the start of the stream, since the spec gives a lag for teardown but not for reopening.