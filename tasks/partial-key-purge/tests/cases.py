"""Hand scripts: one per graded decision or wrong reading, plus a deep simple chain.

Each is small enough to check by hand; `chain-1500` is the fence for a cascade that
recurses once per row. Answers are frozen in seal/gt.json. The merge cases fence a row with two
cascade references that is itself referenced, the depth cases fence the fifteen-round limit
from both sides, and every audit line carries the refusal the delete would print.
"""

CASES = {
    "audit-diamond": """table rev d n bd bn
table note k d n
key rev_k rev d n
key note_k note k
ref rev_base rev bd bn -> rev_k simple cascade
ref note_on note d n -> rev_k partial cascade
row rev 1 a 1 - -
row rev 2 a 2 a 1
row rev 3 a 3 a 1
row note 1 1 a -
audit
""",
    "audit-loop": """table rev d n bd bn
table note k d n
key rev_k rev d n
key note_k note k
ref rev_base rev bd bn -> rev_k partial cascade
ref note_on note d n -> rev_k partial cascade
row rev 1 x 2 - -
row rev 2 a 1 - 2
row rev 3 a 2 a 1
row rev 4 y 1 x 2
row note 1 1 a -
row note 2 2 y 1
audit
""",
    "cascade-tree": """table doc d
table rev d n bd bn
key doc_k doc d
key rev_k rev d n
ref rev_doc rev d -> doc_k simple noaction
ref rev_base rev bd bn -> rev_k simple cascade
row doc 1 a
row rev 1 a 1 - -
row rev 2 a 2 a 1
row rev 3 a 3 a 2
row rev 4 a 4 a 2
row rev 5 a 5 - -
audit
delete rev 2
dump rev
audit
""",
    "clear-no-feedback": """table rev d n
table link k d n
key rev_k rev d n
key link_k link k
ref link_pin link d n -> rev_k partial setnull n
ref link_on link d n -> rev_k simple cascade
row rev 1 a 1
row rev 2 a 2
row link 1 1 a 1
row link 2 2 a 2
audit
delete rev 1
dump link
""",
    "fork-either": """table rev d n
table link k fd fn td tn
key rev_k rev d n
key link_k link k
ref link_from link fd fn -> rev_k simple cascade
ref link_to link td tn -> rev_k partial cascade
row rev 1 a 1
row rev 2 a 2
row rev 3 b 1
row link 1 1 a 1 b 1
row link 2 2 b 1 a -
audit
delete rev 1
dump link
delete rev 3
dump link
""",
    "full-broken-by-clear": """table rev d n
table cite k d n
key rev_k rev d n
key cite_k cite k
ref cite_on cite d n -> rev_k full setnull n
row rev 1 a 1
row rev 2 a 2
row cite 1 1 a 1
row cite 2 2 - -
audit
delete rev 1
delete rev 2
dump cite
""",
    "multi-delete": """table rev d n bd bn
key rev_k rev d n
ref rev_base rev bd bn -> rev_k simple cascade
row rev 1 a 1 - -
row rev 2 a 2 a 1
row rev 3 a 3 a 2
row rev 4 b 1 - -
delete rev 2 3
audit
delete rev 1 4
dump rev
""",
    "mutual-keep": """table rev d n bd bn
key rev_k rev d n
ref rev_base rev bd bn -> rev_k partial cascade
row rev 1 x 2 - -
row rev 2 a 1 - 2
row rev 3 a 2 a 1
row rev 4 a 3 a 2
audit
delete rev 1
dump rev
audit
delete rev 3
dump rev
""",
    "noaction-removed-anyway": """table rev d n bd bn
table link k d n e m
key rev_k rev d n
key link_k link k
ref rev_base rev bd bn -> rev_k partial cascade
ref link_in link d n -> rev_k partial cascade
ref link_see link e m -> rev_k simple noaction
row rev 1 a 1 - -
row rev 2 a 2 a 1
row rev 3 b 1 - -
row link 1 1 a 1 a 2
row link 2 2 b 1 a 2
audit
delete rev 3
delete rev 1
dump link
""",
    "order-decl": """table rev d n
table hold k d n
table watch k d n
key rev_k rev d n
key hold_k hold k
key watch_k watch k
ref watch_on watch d n -> rev_k simple noaction
ref hold_on hold d n -> rev_k simple restrict
row rev 1 a 1
row hold 3 3 a 1
row watch 7 7 a 1
delete rev 1
audit
""",
    "order-row": """table rev d n bd bn
table watch k d n
key rev_k rev d n
key watch_k watch k
ref rev_base rev bd bn -> rev_k simple cascade
ref watch_on watch d n -> rev_k simple noaction
row rev 1 a 1 - -
row rev 2 a 2 a 1
row watch 9 9 a 1
row watch 4 4 a 2
delete rev 1
audit
""",
    "partial-all-go": """table rev d n
table note k d n
key rev_k rev d n
key note_k note k
ref note_on note d n -> rev_k partial cascade
row rev 1 a 1
row rev 2 a 2
row rev 3 b 1
row note 1 1 a -
row note 2 2 - 1
row note 3 3 a 2
audit
delete rev 1
dump note
delete rev 2 3
dump note
""",
    "partial-self": """table rev d n bd bn
key rev_k rev d n
ref rev_base rev bd bn -> rev_k partial cascade
row rev 1 a 1 - -
row rev 2 a 2 a -
row rev 3 a 3 a 2
audit
delete rev 1
dump rev
delete rev 2
dump rev
""",
    "restrict-removed-anyway": """table rev d n bd bn
table hold k d n e m
key rev_k rev d n
key hold_k hold k
ref rev_base rev bd bn -> rev_k partial cascade
ref hold_in hold d n -> rev_k partial cascade
ref hold_on hold e m -> rev_k simple restrict
row rev 1 a 1 - -
row rev 2 a 2 a 1
row rev 3 b 1 - -
row hold 1 1 a 1 a 2
row hold 2 2 b 1 a 2
audit
delete rev 1
delete rev 3
dump hold
""",
    "restrict-broken-by-clear": """table rev d n
table tag k
table cite k d n
key rev_k rev d n
key tag_k tag k
key cite_k cite k
ref cite_on cite d n -> rev_k full restrict
ref cite_tag cite n -> tag_k simple setnull
row rev 1 a 1
row rev 2 a 2
row tag 1 1
row tag 2 2
row cite 1 1 a 1
row cite 2 2 a 2
audit
delete tag 1
delete rev 2
dump cite
""",
    "self-restrict": """table rev d n bd bn
key rev_k rev d n
ref rev_keep rev bd bn -> rev_k partial restrict
row rev 1 a 1 - -
row rev 2 a 2 a 2
row rev 3 b 1 a -
audit
delete rev 1
delete rev 2
audit
""",
    "setnull-all": """table rev d n
table pin k d n
key rev_k rev d n
key pin_k pin k
ref pin_on pin d n -> rev_k full setnull
row rev 1 a 1
row pin 1 1 a 1
audit
delete rev 1
dump pin
""",
    "setnull-already-null": """table rev d n bd bn
table pin k d n
key rev_k rev d n
key pin_k pin k
ref rev_base rev bd bn -> rev_k simple cascade
ref pin_on pin d n -> rev_k partial setnull n
row rev 1 a 1 - -
row rev 2 a 2 a 1
row rev 3 b 1 - -
row pin 1 1 a -
row pin 2 2 b 1
audit
delete rev 2
audit
""",
    "setnull-key-column": """table rev d n
table tag d n t
key rev_k rev d n
key tag_k tag d n t
ref tag_on tag d n -> rev_k simple setnull
row rev 1 a 1
row rev 2 a 2
row tag 1 a 1 x
audit
delete rev 1
delete rev 2
dump tag
""",
    "setnull-list": """table rev d n
table pin k d n
key rev_k rev d n
key pin_k pin k
ref pin_on pin d n -> rev_k partial setnull n
row rev 1 a 1
row rev 2 a 2
row pin 1 1 a 1
row pin 2 2 a -
audit
delete rev 1
dump pin
""",
    "setnull-rematch-fails": """table rev d n
table pin k d n
key rev_k rev d n
key pin_k pin k
ref pin_on pin d n -> rev_k partial setnull n
row rev 1 a 1
row rev 2 b 1
row pin 1 1 a 1
row pin 2 2 b 1
audit
delete rev 1
delete rev 2 1
dump pin
""",
    "simple-null-inert": """table rev d n
table pin k d n
key rev_k rev d n
key pin_k pin k
ref pin_on pin d n -> rev_k simple restrict
row rev 1 a 1
row rev 2 a 2
row pin 1 1 a -
row pin 2 2 a 2
delete rev 1
delete rev 2
dump pin
audit
""",
    "tiny": """table doc d
table rev d n bd bn
table note k d n
key doc_k doc d
key rev_k rev d n
key note_k note k
ref rev_doc rev d -> doc_k simple noaction
ref rev_base rev bd bn -> rev_k partial cascade
ref note_on note d n -> rev_k partial cascade
row doc 1 a
row rev 1 a 1 - -
row rev 2 a 2 a 1
row rev 3 a 3 a 1
row note 1 1 a 2
row note 2 2 a -
delete rev 2
dump note
delete rev 1
audit
""",
    "two-setnull": """table doc d
table rev d n
table pin k d n
key doc_k doc d
key rev_k rev d n
key pin_k pin k
ref pin_doc pin d -> doc_k simple setnull
ref pin_on pin d n -> rev_k partial setnull n
row doc 1 a
row doc 2 b
row rev 1 a 1
row rev 2 a 2
row rev 3 b 1
row pin 1 1 a 1
row pin 2 2 b -
audit
delete rev 1
dump pin
delete doc 2
dump pin
""",
    "audit-names": """table rev d n bd bn
table hold k d n
key rev_k rev d n
key hold_k hold k
ref hold_on hold d n -> rev_k partial restrict
ref rev_base rev bd bn -> rev_k partial cascade
row rev 1 a 1 - -
row rev 2 a 2 a 1
row rev 3 a 3 a 2
row rev 4 a 4 a 3
row rev 5 a 5 a 4
row hold 1 1 a 3
row hold 2 2 a 5
row hold 3 3 a -
audit
delete hold 3
audit
""",
    "depth-both-refs": """table rev d n bd bn md mn
key rev_k rev d n
ref rev_merge rev md mn -> rev_k partial cascade
ref rev_base rev bd bn -> rev_k partial cascade
row rev 1 a 1 - - - -
row rev 2 a 2 a 1 - -
row rev 3 a 3 a 2 - -
row rev 4 a 4 a 3 - -
row rev 5 a 5 a 4 - -
row rev 6 a 6 a 5 - -
row rev 7 a 7 a 6 - -
row rev 8 a 8 a 7 - -
row rev 9 a 9 a 8 - -
row rev 10 a 10 a 9 - -
row rev 11 a 11 a 10 - -
row rev 12 a 12 a 11 - -
row rev 13 a 13 a 12 - -
row rev 14 a 14 a 13 - -
row rev 15 a 15 a 14 - -
row rev 16 a 16 a 15 - -
row rev 17 b 1 a 1 - -
row rev 18 b 2 b 1 - -
row rev 19 b 3 b 2 - -
row rev 20 b 4 b 3 - -
row rev 21 b 5 b 4 - -
row rev 22 b 6 b 5 - -
row rev 23 b 7 b 6 - -
row rev 24 b 8 b 7 - -
row rev 25 b 9 b 8 - -
row rev 26 b 10 b 9 - -
row rev 27 b 11 b 10 - -
row rev 28 b 12 b 11 - -
row rev 29 b 13 b 12 - -
row rev 30 b 14 b 13 - -
row rev 31 b 15 b 14 - -
row rev 32 b 16 b 15 - -
row rev 33 b 17 b 16 - -
row rev 34 b 18 b 17 - -
row rev 35 b 19 b 18 - -
row rev 36 a 17 a 16 b 19
audit
delete rev 1
""",
    "depth-limit": """table rev d n bd bn
table note k d n
key rev_k rev d n
key note_k note k
ref note_on note d n -> rev_k partial cascade
ref rev_base rev bd bn -> rev_k partial cascade
row rev 1 a 1 - -
row rev 2 a 2 a 1
row rev 3 a 3 a 2
row rev 4 a 4 a 3
row rev 5 a 5 a 4
row rev 6 a 6 a 5
row rev 7 a 7 a 6
row rev 8 a 8 a 7
row rev 9 a 9 a 8
row rev 10 a 10 a 9
row rev 11 a 11 a 10
row rev 12 a 12 a 11
row rev 13 a 13 a 12
row rev 14 a 14 a 13
row rev 15 a 15 a 14
row rev 16 a 16 a 15
row note 1 1 a 16
row note 2 2 a 15
audit
delete rev 1
delete rev 2
dump rev
dump note
""",
    "depth-merge-shortcut": """table rev d n bd bn md mn
key rev_k rev d n
ref rev_base rev bd bn -> rev_k partial cascade
ref rev_merge rev md mn -> rev_k partial cascade
row rev 1 a 1 - - - -
row rev 2 a 2 a 1 - -
row rev 3 a 3 a 2 - -
row rev 4 a 4 a 3 - -
row rev 5 a 5 a 4 - -
row rev 6 a 6 a 5 - -
row rev 7 a 7 a 6 - -
row rev 8 a 8 a 7 - -
row rev 9 a 9 a 8 - -
row rev 10 a 10 a 9 x 1
row rev 11 a 11 a 10 - -
row rev 12 a 12 a 11 - -
row rev 13 a 13 a 12 - -
row rev 14 a 14 a 13 - -
row rev 15 a 15 a 14 - -
row rev 16 a 16 a 15 - -
row rev 17 a 17 a 16 - -
row rev 18 a 18 a 17 - -
row rev 19 a 19 a 18 - -
row rev 20 a 20 a 19 - -
row rev 21 x 1 a 1 - -
audit
delete rev 1
""",
    "merge-either": """table rev d n bd bn md mn
table note k d n
key rev_k rev d n
key note_k note k
ref rev_base rev bd bn -> rev_k partial cascade
ref rev_merge rev md mn -> rev_k partial cascade
ref note_on note d n -> rev_k partial cascade
row rev 1 a 1 - - - -
row rev 2 a 2 a 1 - -
row rev 3 a 3 a 1 - -
row rev 4 a 4 a 2 a 3
row rev 5 a 5 a 4 - -
row note 1 1 a 5
audit
delete rev 3
dump rev
audit
""",
    "merge-self": """table rev d n bd bn md mn
table note k d n
key rev_k rev d n
key note_k note k
ref rev_base rev bd bn -> rev_k partial cascade
ref rev_merge rev md mn -> rev_k partial cascade
ref note_on note d n -> rev_k partial cascade
row rev 1 a 1 - - - -
row rev 2 a 2 a 1 a 2
row rev 3 a 3 a 2 - -
row rev 4 b 1 - - b 1
row note 1 1 a 3
row note 2 2 b 1
audit
delete rev 1
dump rev
""",
    "merge-wild-side": """table rev d n bd bn md mn
key rev_k rev d n
ref rev_base rev bd bn -> rev_k partial cascade
ref rev_merge rev md mn -> rev_k partial cascade
row rev 1 a 1 - - - -
row rev 2 b 1 - - - -
row rev 3 b 2 b 1 - -
row rev 4 a 2 a 1 b -
row rev 5 a 3 a 2 - -
audit
delete rev 3
audit
""",
    "or-loop-broken": """table rev d n bd bn md mn
key rev_k rev d n
ref rev_base rev bd bn -> rev_k partial cascade
ref rev_merge rev md mn -> rev_k partial cascade
row rev 1 x 1 - - - -
row rev 2 a 1 a 2 x 1
row rev 3 a 2 a 1 - -
row rev 4 a 3 a 2 - -
row rev 5 b 1 b 2 - -
row rev 6 b 2 b 1 - -
audit
delete rev 1
dump rev
""",
}


def _chain(n):
    lines = ["table rev d n bd bn", "table note k d n", "key rev_k rev d n", "key note_k note k",
             "ref rev_base rev bd bn -> rev_k simple cascade",
             "ref note_on note d n -> rev_k simple cascade",
             "row rev 1 a 1 - -"]
    for i in range(2, n + 1):
        lines.append("row rev %d a %d a %d" % (i, i, i - 1))
    lines.append("row note 1 1 a %d" % n)
    lines += ["audit", "delete rev %d" % (n // 2), "dump note", "delete rev 1", "audit"]
    return "\n".join(lines) + "\n"


CASES["chain-1500"] = _chain(1500)
ORDER = sorted(CASES)
