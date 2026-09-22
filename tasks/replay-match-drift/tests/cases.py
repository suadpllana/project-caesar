"""Enumerated run files: one per graded decision, plus the must-still-work side of each fence.

Every rule in the brief has a program here whose trace changes when that rule is read the
other way, so a failure names the rule rather than the program. The generated population
covers combinations; these pin the rules.
"""

CASES = {
    # --- a command is counted among the commands of its own kind ----------------------
    "kind-count": [
        "b call ax", "b nap ti", "b call bo", "b fin",
        "e go call ax", "e ok call ax 3",
        "e go call bo", "e ok call bo 4",
        "e go timer ti", "e ok timer ti 9",
    ],
    "kind-count-same": [
        "b call ax", "b call bo", "b call cy", "b fin",
        "e go call ax", "e ok call ax 1",
        "e go call bo", "e ok call bo 2",
        "e go call cy", "e ok call cy 3",
    ],
    "kind-count-three": [
        "b spawn ax", "b call bo", "b nap ti", "b spawn cy", "b fin",
        "e go call bo", "e ok call bo 5",
        "e go child ax", "e ok child ax 6",
        "e go timer ti", "e ok timer ti 7",
        "e go child cy", "e ok child cy 8",
    ],

    # --- a slot naming something else stops the run where it happens -------------------
    "name-check": [
        "b call ax", "b call bo", "b call cy", "b fin",
        "e go call ax", "e ok call ax 1",
        "e go call zz", "e ok call zz 2",
        "e go call cy", "e ok call cy 3",
    ],
    "name-check-kind": [
        "b call ax", "b nap ti", "b fin",
        "e go call ax", "e ok call ax 1",
        "e go timer zz", "e ok timer zz 2",
    ],

    # --- an answer is paired on kind and name together ---------------------------------
    "pair-name": [
        "b call ax", "b call bo", "b fin",
        "e go call ax", "e go call bo",
        "e ok call bo 7", "e ok call ax 5",
    ],
    "pair-dup": [
        "b fire ax", "b fire ax", "b fire bo", "b join", "b join", "b join", "b fin",
        "e go call ax", "e go call ax", "e go call bo",
        "e ok call bo 9", "e ok call ax 1", "e ok call ax 2",
    ],
    "pair-kind-name": [
        "b call ax", "b nap ax", "b fin",
        "e go call ax", "e go timer ax",
        "e ok timer ax 9", "e ok call ax 5",
    ],
    "pair-order": [
        "b call ax", "b call bo", "b fin",
        "e go call ax", "e ok call ax 5",
        "e go call bo", "e ok call bo 7",
    ],

    # --- the boundary: one crossing for the whole run, printed once ---------------------
    "edge-once": [
        "b call ax", "b call bo", "b call cy", "b call de", "b fin",
        "e go call ax", "e ok call ax 1",
        "r 21", "r 22", "r 23",
    ],
    "edge-global": [
        "b call ax", "b nap ti", "b fin",
        "e go timer ti", "e ok timer ti 8",
        "r 30",
    ],
    "edge-none": [
        "b call ax", "b call bo", "b fin",
        "e go call ax", "e ok call ax 4",
        "e go call bo", "e ok call bo 6",
    ],
    "edge-empty": [
        "b call ax", "b nap ti", "b fin",
        "r 11", "r 12",
    ],
    "edge-feed-out": [
        "b call ax", "b call bo", "b call cy", "b fin",
        "r 40",
    ],

    # --- what the log has left when the body is done ------------------------------------
    "left-earliest": [
        "b call ax", "b fin",
        "e go call ax", "e ok call ax 2",
        "e go timer ti", "e go child cy",
    ],
    "left-not-sig": [
        "b call ax", "b fin",
        "e go call ax", "e ok call ax 2", "e sig pay 30",
    ],
    "left-not-ok": [
        "b call ax", "b fin",
        "e go call ax", "e ok call ax 2", "e ok call bo 8", "e ch road 4",
    ],
    "left-skip-hold": [
        "b call ax", "b call bo", "b fin",
        "e go call ax", "e ok call ax 2",
        "e go call bo",
        "e go timer ti",
    ],
    "left-after-live": [
        "b call ax", "b call bo", "b fin",
        "e go call ax", "e ok call ax 2",
        "e go timer ti", "e ok timer ti 3",
        "r 50",
    ],

    # --- taking a result: issued earliest against answered earliest ----------------------
    "join-first": [
        "b fire ax", "b fire bo", "b join", "b join", "b fin",
        "e go call ax", "e go call bo",
        "e ok call bo 7", "e ok call ax 5",
    ],
    "race-answered": [
        "b fire ax", "b fire bo", "b race", "b race", "b fin",
        "e go call ax", "e go call bo",
        "e ok call bo 7", "e ok call ax 5",
    ],
    "race-live-after": [
        "b fire bo", "b open ax", "b race", "b race", "b fin",
        "e go call bo", "e ok call bo 7",
        "r 60",
    ],
    "feed-order": [
        "b open ax", "b open bo", "b join", "b join", "b fin",
        "r 61", "r 62",
    ],
    "race-none": [
        "b fire ax", "b fire bo", "b race", "b fin",
        "e go call ax", "e go call bo",
    ],
    "hold-cmd": [
        "b call ax", "b call bo", "b fin",
        "e go call ax", "e ok call ax 2",
        "e go call bo",
    ],
    "hold-none": [
        "b call ax", "b join", "b fin",
        "e go call ax", "e ok call ax 2",
    ],

    # --- signals, per tag, on either side of the boundary --------------------------------
    "sig-tag": [
        "b wait pay", "b wait ship", "b wait pay", "b fin",
        "e sig ship 40", "e sig pay 11", "e sig pay 12",
    ],
    "sig-hold": [
        "b wait pay", "b wait ship", "b fin",
        "e sig pay 11",
    ],
    "sig-after-live": [
        "b call ax", "b wait pay", "b fin",
        "e sig pay 33",
        "r 70",
    ],

    # --- markers ---------------------------------------------------------------------------
    "ver-recorded": [
        "b mark road 3", "b fin",
        "e ch road 1",
    ],
    "ver-replay-zero": [
        "b mark road 3", "b call ax", "b fin",
        "e go call ax", "e ok call ax 5",
    ],
    "ver-live-cur": [
        "b call ax", "b mark road 3", "b fin",
        "r 80",
    ],
    "ver-empty-zero": [
        "b mark road 3", "b fin",
    ],
    "ver-per-key": [
        "b mark road 5", "b mark turn 5", "b mark road 5", "b fin",
        "e ch turn 7", "e ch road 1", "e ch road 2",
    ],
    "ver-branch": [
        "b mark road 2", "b jz slow", "b call fast", "b jmp out",
        "b lab slow", "b call slow", "b lab out", "b fin",
        "e go call slow", "e ok call slow 6",
    ],

    # --- the step ceiling ---------------------------------------------------------------------
    "over-steps": [
        "b set 1", "b lab spin", "b add 1", "b jmp spin", "b fin",
    ],

    # --- an everyday program that an overconservative engine breaks ----------------------------
    "parse-blank": [
        "b call ax", "", "b fin", "",
        "e go call ax", "", "e ok call ax 6",
    ],

    # --- an everyday program that an overconservative engine breaks ----------------------------
    "plain-ordinary": [
        "b call ax", "b nap ti", "b wait pay", "b fire bo", "b spawn cy", "b join",
        "b add 2", "b fin",
        "e go call ax", "e ok call ax 4",
        "e go timer ti", "e ok timer ti 0",
        "e sig pay 21",
        "e go call bo",
        "e go child cy", "e ok child cy 9",
        "e ok call bo 12",
    ],
}

ORDER = sorted(CASES)


def prog(name):
    return list(CASES[name])
