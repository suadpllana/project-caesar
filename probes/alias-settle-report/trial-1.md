I'll start by reading the harness code and the three report sets.

Bash(find . -type f | sort && echo ---- && cat run_bind.py && for f in bind/*.py; do echo "==== $f"; cat "$f"; done)

./bind/__init__.py
./bind/bk.py
./bind/card.py
… +239 lines (click to expand)
Bash(for f in sets/*.txt; do echo "==== $f"; cat "$f"; echo "---- output"; python3 run_bind.py "$f"; done)

==== sets/barred.txt
watch 5
run r0 5
… +132 lines (click to expand)
Thinking… (click to expand)
Bash(cat > bind/rch.py <<'EOF' def _barred(bk, cells, x, y): """True if some standing difference lies between cell …)

==== sets/barred.txt
["ps", 1, "r0", 5, 70]
["br", 2, "m1", 2, 5]
… +58 lines (click to expand)
Thinking… (click to expand)
Bash(cat > /tmp/fuzz.py <<'EOF' import random, sys, itertools sys.path.insert(0, '/app') from bind.rd import Spec f…)

ok 300

[stdout]
… +2 lines (click to expand)
Bash(python3 /tmp/fuzz.py 2 400 && python3 /tmp/fuzz.py 3 400 && python3 -m pyflakes bind/*.py 2>/dev/null; python3…)

ok 400
ok 400
syntax ok
… +6 lines (click to expand)
The fix is in place and verified. I changed two files, `bind/rch.py` and `bind/hold.py`, and left `card.py` and `seq.py` as shipped.

**What was wrong.** The old reachability in `rch.span` looked only one tag hop out from the cell, ignored standing differences entirely, and could not follow a chain of overlapping tag pools. The old `hold.firm` only compared the smallest key and never asked whether any open run could still post ahead of the post the item carried. That is why plain filed key 4 on tick 1 while r0 still had key 4 unsent, and chain filed key 5 on tick 1 while m0 and m1 together could still bring key 2 in.

**The rule now.**
- `rch.span` grows a blob from the cell one cell at a time. A cell may join if some open tag pool touches both it and the blob, and no bar stands between it and any cell already in the blob. Every blob reachable this way is explored, and the union of members is the span. Shut tags contribute nothing. A tag whose pool lies inside one cell adds nothing.
- `hold.firm` files a watched key once its item carries a post, no reachable cell holds a smaller key or an earlier post, and no open run has an unsent key inside the item or any reachable cell that would sort ahead of the post it carries.

**Results on the three sets.**

| Set | Filing row now |
|---|---|
| plain | key 9 at tick 2, key 4 at tick 5 as `[4, 4, 12]` |
| chain | key 5 at tick 4 as `[5, 2, 70]` |
| barred | key 5 at tick 2 as `[5, 5, 70]`, right after the bar makes key 2 unreachable |

**Verification.** I fuzzed the rule with 1100 random sets of overlapping run and tag pools, random bars and ties, and multiple open runs. For each set the check confirmed that no filed line was moved by any later event, and that at every earlier tick where the key was held there existed a legal continuation of up to four events that would have changed the line. All passed.

One assumption worth stating: a line is treated as movable when an earlier post could still enter the item, even if that post's score might happen to equal the current one. The check is on which post the item would carry, not on coincidental score equality.