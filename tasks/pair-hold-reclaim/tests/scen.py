"""The enumerated streams.

One per rule, named for the reading it exists to fail, plus the must-still-work side of
every fence. These are hand-written and small enough to read; the generated set in
gen.py is what stops a submission fitted to them from carrying.

Coverage on paper is not coverage. Every reading in authoring/readings.py was run
against this set, and where the set could not separate one, a shrunk counterexample was
added here under the name of the reading it separates.
"""

CASES = {

"links-only": """
new 1
new 2
new 3
bind a 1
edge 1 2
watch w1 firm 3
pass
show w1
""",

"one-key-holds": """
new 1
new 2
new 3
bind a 1
edge 1 2
pair 2 3
watch w3 firm 3
pass
show w3
""",

"one-key-drops": """
new 1
new 2
new 3
bind a 1
pair 2 3
watch w3 firm 3
pass
show w3
""",

"entry-chain": """
new 1
new 2
new 3
new 4
bind a 1
pair 1 2
edge 2 3
pair 3 4
watch w4 firm 4
pass
show w4
""",

"entry-chain-back": """
new 1
new 2
new 3
new 4
new 5
bind a 1
pair 3 4
pair 1 2
edge 2 3
edge 4 5
watch w4 firm 4
watch w5 firm 5
pass
show w4
show w5
""",

"self-holding": """
new 1
new 2
new 3
bind a 1
pair 2 3
edge 3 2
watch w2 firm 2
pass
show w2
""",

"two-key-both": """
new 1
new 2
new 3
bind a 1
bind b 2
both 1 2 3
watch w3 firm 3
pass
show w3
""",

"two-key-one": """
new 1
new 2
new 3
bind a 1
both 1 2 3
watch w3 firm 3
pass
show w3
""",

"two-key-late": """
new 1
new 2
new 3
new 4
new 5
bind a 1
pair 1 2
both 2 1 3
edge 3 4
both 4 1 5
watch w5 firm 5
pass
show w5
""",

"clean-runs": """
new 1
new 2
bind a 1
arm 2 none
watch w2 firm 2
pass
show w2
""",

"clean-puts-back": """
new 1
new 2
new 3
bind a 1
edge 2 3
arm 2 bind b 2
watch p2 plain 2
watch f2 firm 2
watch f3 firm 3
pass
show p2
show f2
show f3
""",

"clean-cuts-loose": """
new 1
new 2
new 3
bind a 1
bind h 3
edge 1 2
arm 2 unbind h
watch p3 plain 3
watch f3 firm 3
unbind a
pass
show p3
show f3
""",

"clean-wakes-clean": """
new 1
new 2
new 3
bind a 1
bind h 3
edge 1 2
arm 2 unbind h
arm 3 none
unbind a
pass
""",

"clean-cascade": """
new 1
new 2
new 3
new 4
bind a 1
bind g 3
bind h 4
edge 1 2
arm 2 unbind g
arm 3 unbind h
arm 4 none
unbind a
pass
""",

"clean-once": """
new 1
new 2
bind a 1
arm 2 bind b 2
pass
unbind b
pass
""",

"order-by-reach": """
new 1
new 2
new 3
bind a 1
edge 3 2
arm 2 none
arm 3 none
pass
""",

"order-two-key": """
new 1
new 2
new 3
bind h 1
both 3 1 2
arm 2 none
arm 3 none
pass
""",

"order-entry": """
new 1
new 2
new 3
bind a 1
pair 3 2
arm 2 none
arm 3 none
pass
""",

"cycle-puts-back": """
new 1
new 2
new 3
bind a 1
edge 2 3
edge 3 2
arm 2 bind b 3
arm 3 none
pass
""",

"order-cycle": """
new 1
new 2
new 3
bind a 1
edge 2 3
edge 3 2
arm 2 none
arm 3 none
pass
""",

"order-chain": """
new 1
new 2
new 3
new 4
bind a 1
edge 4 3
edge 3 2
arm 2 none
arm 3 none
arm 4 none
pass
""",

"clean-adds-entry": """
new 1
new 2
new 3
bind a 1
arm 2 pair 1 3
watch f3 firm 3
pass
show f3
""",

"plain-empties": """
new 1
new 2
bind a 1
watch p2 plain 2
watch f2 firm 2
pass
show p2
show f2
""",

"watch-order": """
new 1
new 2
bind a 1
watch p2 plain 2
watch q2 plain 2
watch f2 firm 2
pass
""",

"plain-late-round": """
new 1
new 2
new 3
bind a 1
bind h 3
edge 1 2
arm 2 unbind h
arm 3 none
watch p3 plain 3
unbind a
pass
""",

"watch-never-refills": """
new 1
new 2
bind a 1
watch p2 plain 2
arm 2 bind b 2
pass
show p2
""",

"release-order": """
new 1
new 2
new 3
new 4
new 5
bind a 3
pass
""",

"entries-dropped": """
new 1
new 2
new 3
new 4
bind a 1
pair 2 3
both 2 3 4
pass
""",

"look-mid-pass": """
new 1
new 2
new 3
bind a 1
watch p3 plain 3
watch f3 firm 3
arm 2 look p3
arm 3 none
pass
show f3
""",

"nothing-doomed": """
new 1
new 2
new 3
bind a 1
edge 1 2
edge 2 3
watch f3 firm 3
arm 3 none
pass
show f3
""",

"held-through-clean": """
new 1
new 2
new 3
bind a 1
edge 1 3
arm 2 none
watch f3 firm 3
pass
show f3
""",
}


def cases():
    return [(k, v.lstrip("\n")) for k, v in sorted(CASES.items())]
