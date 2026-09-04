I'll start by reading the whole tree to understand the interfaces and the current behavior.

Bash(find . -type f | grep -v __pycache__ | sort && echo ---- && cat rev/store.py scr/pin.py scr/grp.py note/board.…)

./note/board.py
./note/rule.py
./rev/store.py
… +222 lines (click to expand)
Bash(for f in streams/*.txt; do echo "== $f"; cat -A $f | head -40; echo "-- out"; python run_review.py $f; done)

== streams/guard.txt
rev |    log(job)|    if not job:|        return None|    return out|    for row in job:$
note 0 2$
… +48 lines (click to expand)
Thinking… (click to expand)
Bash(cat > note/rule.py <<'EOF' from scr import grp, pin def kept(before, after): """Map each surviving line of ``b…)

== streams/guard.txt
retire 0
== streams/repeat.txt
… +14 lines (click to expand)
Bash(python - <<'EOF' from scr import pin, grp from rev.store import Store from note.board import Board b="a|b|a|b|…)

[('K', 0, 0), ('K', 1, 1), ('K', 2, 2), ('K', 3, 3), ('K', 4, 4), ('D', 5, None)]
[('D', 0, None), ('K', 1, 0), ('K', 2, 1), ('K', 3, 2), ('K', 4, 3)]
[{1, 2, 3}]
… +8 lines (click to expand)
Both files are rewritten and the three sample streams now behave as the rules describe.

**What was wrong**

- The board jumped straight from each note's opening revision to the head, so a line deleted in one revision and retyped in a later one was treated as surviving. That is why the guard stream kept note 0 alive on line 3.
- `rule.kept` used its own longest-common-subsequence match instead of the settled script from `scr.pin`, so on repetitive files it could pick a different alignment than the change script.
- Raises were only checked against the last revision, and any note surviving to head was compared against a line set derived from that ad hoc LCS.

**What I changed**

- `note/rule.py`: `kept` now reads the K ops from `pin.reading` over `pin.script`, so a line survives exactly when the one change script keeps it. `raised` asks `grp.spans` whether the note's landed line sits inside a change group.
- `note/board.py`: `build` walks revisions in order. For each revision it carries every live note through the script (retiring those whose line is dropped), raises those inside a change, then lets notes opened at that revision join, absorbing into an existing owner of the same line. Retired and absorbed notes are gone for good. Within a revision the log is retires, then raises, then absorbs, each in ascending note order. Opens with an out-of-range line are ignored.

**Results**

```
guard.txt   -> retire 0
repeat.txt  -> note 0 1
rework.txt  -> retire 0 / retire 1
```

A synthetic check with a raise, same-revision collisions, and a later note landing on an already held line produced the expected `absorb`, `raise`, `absorb` sequence in the right order. No other files were touched and all signatures are unchanged.