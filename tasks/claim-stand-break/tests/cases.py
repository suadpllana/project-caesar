"""The enumerated programs: one per graded decision, and both sides of every fence.

Each name says what its program pins down. The nonce population is what stops a submission
fitting the shipped examples; these are what make a failure name the rule it broke.
"""

PROGS = {

# --- what a read is answered from -------------------------------------------------------

"read-base": """
open 1
put 1 5 10
seal 1
open 2
get 2 5
open 3
put 3 7 20
seal 3
get 2 7
seal 2
look 0 9
""",

"read-cover": """
open 1
put 1 4 10
seal 1
open 2
put 2 4 11
get 2 4
put 2 4 12
get 2 4
seal 2
look 0 9
""",

"read-del": """
open 1
put 1 4 10
put 1 6 30
seal 1
open 2
del 2 4
get 2 4
get 2 6
seal 2
look 0 9
""",

"span-order": """
open 1
put 1 8 80
put 1 2 20
put 1 5 50
seal 1
open 2
span 2 0 9 2
span 2 0 9 9
span 2 3 9 1
seal 2
look 0 9
""",

"span-short": """
open 1
put 1 2 20
put 1 5 50
seal 1
open 2
span 2 0 9 4
span 2 6 9 2
seal 2
look 0 9
""",

"span-mine": """
open 1
put 1 5 50
seal 1
open 2
put 2 3 30
span 2 0 9 3
seal 2
look 0 9
""",

"span-gone": """
open 1
put 1 2 20
put 1 4 40
put 1 6 60
seal 1
open 2
del 2 4
span 2 0 9 2
seal 2
look 0 9
""",

# --- when a claim stops standing ---------------------------------------------------------

"same-value": """
open 1
put 1 3 30
put 1 7 70
seal 1
open 2
span 2 0 9 4
open 3
put 3 3 30
seal 3
seal 2
look 0 9
""",

"same-claim": """
open 1
put 1 3 30
seal 1
open 2
put 2 3 31
open 3
put 3 3 30
seal 3
seal 2
look 0 9
""",

"win-past": """
open 1
put 1 2 20
put 1 4 40
put 1 8 80
seal 1
open 2
span 2 0 9 2
open 3
put 3 6 60
seal 3
seal 2
look 0 9
""",

"win-in": """
open 1
put 1 2 20
put 1 4 40
put 1 8 80
seal 1
open 2
span 2 0 9 2
open 3
put 3 3 30
seal 3
seal 2
look 0 9
""",

"short-gap": """
open 1
put 1 2 20
put 1 8 80
seal 1
open 2
span 2 0 9 5
open 3
put 3 5 50
seal 3
seal 2
look 0 9
""",

"over-after": """
open 1
put 1 3 30
seal 1
open 2
get 2 3
put 2 3 30
open 3
put 3 3 31
seal 3
seal 2
look 0 9
""",

"off-cover": """
open 1
put 1 3 30
seal 1
open 2
put 2 3 35
mark 2 m
put 2 3 36
span 2 0 9 3
back 2 m
seal 2
look 0 9
""",

"off-claim": """
open 1
put 1 3 30
seal 1
open 2
get 2 7
mark 2 m
put 2 3 35
back 2 m
open 3
put 3 3 31
seal 3
seal 2
look 0 9
""",

"off-pos": """
open 1
put 1 3 30
seal 1
open 2
put 2 3 35
mark 2 m
put 2 3 36
put 2 5 50
back 2 m
get 2 3
get 2 5
seal 2
look 0 9
""",

"off-twice": """
open 1
put 1 3 30
seal 1
open 2
mark 2 m
put 2 3 35
back 2 m
put 2 3 36
back 2 m
get 2 3
seal 2
look 0 9
""",

"off-keep": """
open 1
put 1 3 30
put 1 5 50
seal 1
open 2
mark 2 m
get 2 5
put 2 3 35
back 2 m
open 3
put 3 5 51
seal 3
seal 2
look 0 9
""",

"back-again": """
open 1
put 1 3 30
seal 1
open 2
get 2 3
open 3
put 3 3 31
seal 3
open 4
put 4 3 30
seal 4
get 2 3
seal 2
look 0 9
""",

"late-read": """
open 1
put 1 3 30
seal 1
open 2
open 3
put 3 3 31
seal 3
get 2 3
span 2 0 9 2
seal 2
look 0 9
""",

"late-put": """
open 1
put 1 3 30
seal 1
open 2
open 3
put 3 3 31
seal 3
put 2 3 32
seal 2
look 0 9
""",

"low-index": """
open 1
put 1 3 30
put 1 5 50
seal 1
open 2
span 2 0 9 4
get 2 3
get 2 5
open 3
put 3 3 31
seal 3
seal 2
look 0 9
""",

"one-dead": """
open 1
put 1 3 30
put 1 5 50
seal 1
open 2
get 2 3
get 2 5
open 3
put 3 3 31
seal 3
open 4
put 4 5 51
seal 4
seal 2
look 0 9
""",

"dead-order": """
open 1
put 1 3 30
seal 1
open 7
get 7 3
open 2
get 2 3
open 5
get 5 3
open 9
put 9 3 31
seal 9
seal 5
seal 2
seal 7
look 0 9
""",

"dead-read": """
open 1
put 1 3 30
put 1 5 50
seal 1
open 2
get 2 3
open 3
put 3 3 31
seal 3
get 2 3
get 2 5
put 2 8 80
seal 2
look 0 9
""",

"dead-none": """
open 1
put 1 3 30
seal 1
open 2
get 2 3
put 2 6 60
open 3
put 3 3 31
seal 3
seal 2
look 0 9
""",

"drop-none": """
open 1
put 1 3 30
seal 1
open 2
put 2 6 60
del 2 3
drop 2
open 3
get 3 6
seal 3
look 0 9
""",

"apply-last": """
open 1
put 1 3 30
seal 1
open 2
put 2 3 31
mark 2 m
put 2 3 32
put 2 6 60
back 2 m
put 2 3 33
del 2 5
seal 2
look 0 9
""",

"look-rows": """
look 0 9
open 1
put 1 3 30
put 1 5 50
seal 1
look 0 2
look 3 5
look 0 9
""",

"calm": """
open 1
put 1 2 20
put 1 4 40
seal 1
open 2
span 2 0 3 1
get 2 2
open 3
put 3 8 80
seal 3
span 2 0 3 1
put 2 6 60
seal 2
look 0 9
""",
}

ORDER = sorted(PROGS)


def prog(name):
    return [line for line in PROGS[name].strip().splitlines()]
