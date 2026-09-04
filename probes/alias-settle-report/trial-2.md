I'll start by reading the harness code and the three sets to understand the machine before touching the filing rule.

Bash(find . -type f | sort && echo ---- && cat run_bind.py && echo ---- && for f in bind/*.py; do echo "=== $f"; ca…)

./bind/__init__.py
./bind/bk.py
./bind/card.py
… +240 lines (click to expand)
Bash(for f in sets/*.txt; do echo "=== $f"; cat $f; echo "--- out"; python3 run_bind.py $f; done)

=== sets/barred.txt
watch 5
run r0 5
… +132 lines (click to expand)
Thinking… (click to expand)
Bash(cat > bind/rch.py <<'EOF' def _cell_of(bk, cells): where = {} for c, ks in cells.items(): for k in ks: where[k…)

=== sets/barred.txt
["ps", 1, "r0", 5, 70]
["br", 2, "m1", 2, 5]
… +58 lines (click to expand)
Thinking… (click to expand)
Bash(cat > /tmp/fuzz.py <<'EOF' import random, sys sys.path.insert(0, '/app') from bind.mc import Mach from bind.rd…)

bad 0 filed 7477 filed_on_last_tick 468
bad 0 filed 7497 filed_on_last_tick 453
… +4 lines (click to expand)
The filing rule is fixed. Only `bind/rch.py` and `bind/hold.py` changed; `card.py` and `seq.py` were already correct and are untouched.

**What was wrong.** The old rule looked one tag-hop out from the item, ignored standing differences, and never considered open runs at all. So key 4 in `plain.txt` filed while run r0 still held an unsent post for key 4 that sorts ahead of r1's, and key 5 in `chain.txt` filed while key 2 could still arrive through two chained matchers.

**The rule now.** A watched key files at the first tick where all of the following hold for its item:

- The item carries at least one post.
- No item reachable through open tags has a smaller key. Reachable means joined by a chain of open-tag pools where no standing difference sits between any two items on the chain, since such a weld can never happen. This is what makes `barred.txt` file at tick 2 rather than waiting.
- No post already sitting in a reachable item sorts ahead of the item's current first post.
- No open run has an unsent key in the item or a reachable item that would sort ahead of the current first post.

Each hold condition corresponds to a concrete legal continuation that would move the line, so nothing is held back once the line is safe. A shut tag contributes no edges, a tag wholly inside one item adds nothing, and sets without differences use the same path search with an empty bar set.

**Results on the shipped sets.**

| Set | Filing row |
|---|---|
| plain | key 9 at tick 2, key 4 at tick 5 with score 12 |
| chain | key 5 at tick 4 with representative 2 |
| barred | key 5 at tick 2 with representative 5 |

**Verification.** I fuzzed six thousand randomly generated legal sets with overlapping run and tag pools, bars between singleton and multi-key items, and interleaved shuts. Every filed line matched the line the key carried at the end of the set, with zero mismatches, and roughly ninety-four percent of keys filed before the final tick.