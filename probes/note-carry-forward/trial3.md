
I'll read the whole tree first.

Bash(find . -type f | sort && echo ---- && for f in rev/store.py scr/pin.py scr/grp.py note/board.py note/rule.py r…)

./note/board.py
./note/rule.py
./rev/store.py
… +178 lines (click to expand)
Bash(for f in streams/*.txt; do echo "=== $f"; cat -n $f; echo "--- out"; python3 run_review.py $f; done)

=== streams/guard.txt
     1	rev |    log(job)|    if not job:|        return None|    return out|    for row in job:
     2	note 0 2
… +48 lines (click to expand)
Thinking… (click to expand)
Bash(cat > note/rule.py <<'EOF' from scr import pin, grp def kept(before, after): """Map before-index -> after-inde…)

=== streams/guard.txt
retire 0
=== streams/repeat.txt
… +14 lines (click to expand)
Results look right for guard and rework. Let me verify repeat against the pinned script directly, and stress-test with random streams to make sure the board never crashes and obeys the rules.

Bash(python3 - <<'EOF' from scr.pin import script, reading from scr.grp import spans from rev.store import Store fr…)

Exit code 1
[('K', 0, 0), ('K', 1, 1), ('K', 2, 2), ('K', 3, 3), ('K', 4, 4), ('D', 5, None)] []
[('D', 0, None), ('K', 1, 0), ('K', 2, 1), ('K', 3, 2), ('K', 4, 3)] []
… +5 lines (click to expand)
The repeat trace confirms the board's answer. The assertion failure is a bug in my test, which counted raise entries as endings. I'll fix the invariant check.

Bash(python3 - <<'EOF' from rev.store import Store from note.board import Board import random random.seed(1) for t …)

ok

[stdout]
… +2 lines (click to expand)
Done. Both files are rewritten and the three streams now answer correctly.

**What was wrong**

- `note/board.py` diffed each note's opening revision straight against head with a longest-common-subsequence match, so it ignored the pinned change script, skipped the intermediate revisions, and could resurrect a note once a look-alike line appeared. That is why the guard stream reported the note alive on the newly typed guard.
- Raising was computed by "line not in the LCS", not by the change hunks that `scr/grp.spans` reads out of the script.
- The log was built globally rather than per revision, so ordering and absorbing of partway-opened notes were wrong.

**What the board does now**

- Walks the store revision by revision. `rule.kept` maps kept lines through the pinned script from `scr/pin.reading`, so a note survives only while that script keeps its line, and a retired note is never revisited.
- `rule.raised` reports a line as raised when it sits inside one of the hunks from `scr/grp.spans`.
- Per revision the log emits retirements, then raises, then absorbs, each in ascending note id. Notes opened at that revision join after carrying and settle against what is already there. The lower id owns the line.

**Results**

```
guard.txt   -> retire 0
repeat.txt  -> note 0 1
rework.txt  -> retire 0 / retire 1
```

I traced the repeat stream against the pinned script by hand and it matches. A random stress run over two thousand generated streams confirmed every note ends exactly once, held lines are unique, and absorbers are always older than the absorbed. No other file was touched.