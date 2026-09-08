"""The enumerated scenarios: one per graded decision, plus the cases that must stay quiet.

Grouped by the decision each one pins. The `quiet` group is the other side of the fence -
a round that must emit nothing, and a one-sided change that must emit exactly one operation
- so an engine cannot pass by turning conservative and rewriting everything every round.
"""

CASES = {

    # --- which nodes the record keeps -------------------------------------------------
    "gone-vs-write": """d 1 /a
f 2 /a/n p1
L rm /a/n
R ed /a/n p2
sync""",

    "gone-vs-name": """d 1 /a
f 2 /a/n p1
L rm /a/n
R mv /a/n /a/m
sync""",

    "gone-vs-place": """d 1 /a
d 2 /b
f 3 /a/n p1
L rm /a/n
R mv /a/n /b/n
sync""",

    "gone-vs-quiet": """d 1 /a
f 2 /a/n p1
f 3 /a/m p2
L rm /a/n
R ed /a/m p3
sync""",

    "gone-both": """d 1 /a
f 2 /a/n p1
L rm /a/n
R rm /a/n
sync""",

    "folder-held-by-child": """d 1 /a
f 2 /a/n p1
L rm /a/n
L rm /a
R ed /a/n p2
sync""",

    "folder-held-two-deep": """d 1 /a
d 2 /a/b
f 3 /a/b/n p1
L rm /a/b/n
L rm /a/b
L rm /a
R ed /a/b/n p2
sync""",

    "folder-not-held-by-mover": """d 1 /a
f 2 /a/n p1
L rm /a/n
L rm /a
R mv /a/n /n
sync""",

    "folder-not-held-by-arrival": """d 1 /a
d 2 /k
f 3 /k/n p1
L rm /a
R mv /k/n /a/n
sync""",

    "walk-up-two": """d 1 /a
d 2 /a/b
d 3 /k
f 4 /k/n p1
L rm /a/b
L rm /a
R mv /k/n /a/b/n
sync""",

    "new-in-dead-folder": """d 1 /a
d 2 /k
L rm /a
R mkf /a/n p1
sync""",

    # --- folder and name, settled apart -----------------------------------------------
    "axes-apart": """d 1 /a
d 2 /b
f 3 /a/n k1
L mv /a/n /a/m
R mv /a/n /b/n
sync""",

    "both-moved": """d 1 /a
d 2 /b
d 3 /c
f 4 /a/n k1
L mv /a/n /b/n
R mv /a/n /c/n
sync""",

    "both-renamed": """d 1 /a
f 2 /a/n k1
L mv /a/n /a/p
R mv /a/n /a/q
sync""",

    "both-moved-and-renamed": """d 1 /a
d 2 /b
d 3 /c
f 4 /a/n k1
L mv /a/n /b/p
R mv /a/n /c/q
sync""",

    "one-side-moved": """d 1 /a
d 2 /b
f 3 /a/n k1
L mv /a/n /b/n
sync""",

    "name-contested-folder-not": """d 1 /a
d 2 /b
f 3 /a/n k1
L mv /a/n /b/p
R mv /a/n /b/q
sync""",

    # --- folders that end up inside each other ----------------------------------------
    "ring-two": """d 1 /a
d 2 /b
L mv /a /b/a
R mv /b /a/b
sync""",

    "ring-three": """d 1 /a
d 2 /b
d 3 /c
L mv /a /b/a
L mv /c /b/a/c
R mv /b /c/b
sync""",

    "ring-not-formed": """d 1 /a
d 2 /b
L mv /a /b/a
sync""",

    # --- contested names ---------------------------------------------------------------
    "two-new-one-name": """d 1 /a
L mkf /a/n p1
R mkf /a/n p2
sync""",

    "holder-keeps-when-gone": """d 1 /a
d 2 /a/d
f 3 /a/n p1
L rm /a/d
L ed /a/n p2
R rm /a/n
R mkf /a/d/n p3
sync""",

    "holder-keeps": """d 1 /a
d 2 /a/d
f 3 /a/n p1
L rm /a/d
R mkf /a/d/n p2
sync""",

    "mark-before-extension": """f 1 /notes.txt p1
L ed /notes.txt p2
R ed /notes.txt p3
sync""",

    "mark-without-extension": """f 1 /ab p1
L ed /ab p2
R ed /ab p3
sync""",

    "mark-leading-dot": """f 1 /.cfg p1
L ed /.cfg p2
R ed /.cfg p3
sync""",

    "mark-two-dots": """f 1 /x.y.z p1
L ed /x.y.z p2
R ed /x.y.z p3
sync""",

    "mark-skips-taken": """d 1 /a
d 2 /a/d
f 3 /a/ab p1
f 4 /a/ab~1 p2
L rm /a/d
R mkf /a/d/ab p3
sync""",

    "two-second-nodes": """d 1 /a
f 2 /a/x p0
f 3 /a/y q0
L mv /a/x /a/w
L ed /a/w p1
L ed /a/y q1
R mv /a/y /a/w
R ed /a/x p2
R ed /a/w q2
sync""",

    "case-contested": """d 1 /a
f 2 /a/gh p1
L mkf /a/GH p2
sync""",

    "case-mark-free": """d 1 /a
f 2 /a/gh p1
f 3 /a/GH~1 p2
L mkf /a/GH p3
sync""",

    "case-rename-on-side": """d 1 /a
f 2 /a/gh p1
L mv /a/gh /a/GH
sync""",

    # --- what a node holds --------------------------------------------------------------
    "both-wrote-same": """f 1 /n p1
L ed /n p2
R ed /n p2
sync""",

    "both-wrote-apart": """f 1 /n.txt p1
L ed /n.txt p2
R ed /n.txt p3
sync""",

    "one-wrote": """f 1 /n p1
L ed /n p2
sync""",

    "wrote-and-moved": """d 1 /a
f 2 /n p1
L ed /n p2
R mv /n /a/n
sync""",

    "second-node-in-contest": """d 1 /a
f 2 /a/ab p0
f 3 /a/ab~1 q0
L ed /a/ab p1
R ed /a/ab p2
sync""",

    "second-node-marked-once": """d 1 /a
f 2 /a/ab p1
f 3 /a/xy p2
L ed /a/ab p3
R ed /a/ab p4
L ed /a/xy p5
R ed /a/xy p6
sync""",

    # --- numbering ----------------------------------------------------------------------
    "server-numbered-first": """d 1 /a
d 2 /d
L rm /d
L mkf /w l1
R mkf /d/w r1
R mkf /w r2
sync""",

    "new-nodes-in-path-order": """d 1 /a
d 2 /d
L rm /d
R mkf /n p2
R mkf /d/n p1
sync""",

    # --- the operations, and their order ------------------------------------------------
    "sibling-swap": """f 1 /a p1
f 2 /b p2
L mv /a /hold
L mv /b /a
L mv /hold /b
sync""",

    "folder-swap": """d 1 /u
d 2 /v
f 3 /u/n p1
L mv /u /hold
L mv /v /u
L mv /hold /v
sync""",

    "destination-is-a-node": """d 1 /u
d 2 /v
f 3 /w p1
L mv /u /hold
L mv /v /u
L mv /hold /v
L mv /w /u/w
sync""",

    "name-freed-by-removal": """d 1 /a
f 2 /a/n p1
L rm /a/n
L mkf /a/n p2
sync""",

    "parents-before-children": """d 1 /a
L mkd /a/b
L mkd /a/b/c
L mkf /a/b/c/n p1
sync""",

    "moved-out-then-removed": """d 1 /a
d 2 /b
f 3 /a/n p1
L mv /a/n /b/n
L rm /a
R ed /a/n p2
sync""",

    "written-after-placed": """f 1 /a p1
f 2 /b p2
L mv /a /hold
L mv /b /a
L mv /hold /b
L ed /a p3
sync""",

    # --- quiet: what must not happen ----------------------------------------------------
    "quiet-round": """d 1 /a
f 2 /a/n p1
sync""",

    "quiet-after-work": """d 1 /a
f 2 /a/n p1
L ed /a/n p2
sync
sync""",

    "one-change-one-operation": """d 1 /a
f 2 /a/n p1
f 3 /a/m p2
R ed /a/m p3
sync""",

    "same-change-both-sides": """d 1 /a
d 2 /b
f 3 /a/n p1
L mv /a/n /b/n
R mv /a/n /b/n
sync""",

    # --- rounds carry the record forward -------------------------------------------------
    "second-node-lives-on": """f 1 /n.txt p1
L ed /n.txt p2
R ed /n.txt p3
sync
L ed /n~1.txt p4
sync""",

    "new-node-not-made-twice": """d 1 /a
L mkf /a/n p1
sync
R ed /a/n p2
sync""",

    "record-carries-the-mark": """f 1 /ab p1
L ed /ab p2
R ed /ab p3
sync
R mv /ab~1 /cd
sync""",
}

ORDER = sorted(CASES)


def text(name):
    return CASES[name]
