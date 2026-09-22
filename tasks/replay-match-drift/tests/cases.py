"""Enumerated run files: one per graded decision, plus the must-still-work side of each fence.

Every rule in the brief has a program here whose trace changes when that rule is read the
other way, so a failure names the rule rather than the program. The generated population
covers combinations; these pin the rules.
"""

CASES = {
    # --- a command is counted among the commands of its own kind ----------------------
    "count-kind": [
        "b call ax", "b nap ti", "b call bo", "b end",
        "e go call ax", "e ok call ax 3",
        "e go call bo", "e ok call bo 4",
        "e go timer ti", "e ok timer ti 9",
    ],
    "count-same": [
        "b call ax", "b call bo", "b end",
        "e go call ax", "e ok call ax 1",
        "e go call bo", "e ok call bo 2",
    ],
    "count-three": [
        "b spawn ax", "b call bo", "b nap ti", "b spawn cy", "b end",
        "e go call bo", "e ok call bo 5",
        "e go child ax", "e ok child ax 6",
        "e go timer ti", "e ok timer ti 7",
        "e go child cy", "e ok child cy 8",
    ],

    # --- a recorded command under another name stops the run where it happens ----------
    "name-drift": [
        "b call ax", "b call bo", "b call cy", "b end",
        "e go call ax", "e ok call ax 1",
        "e go call zz", "e ok call zz 2",
        "e go call cy", "e ok call cy 3",
    ],
    "name-drift-kind": [
        "b call ax", "b nap ti", "b end",
        "e go call ax", "e ok call ax 1",
        "e go timer zz", "e ok timer zz 2",
    ],

    # --- an answer is paired on kind and name together ---------------------------------
    "pair-swap": [
        "b call ax", "b call bo", "b end",
        "e go call ax", "e go call bo",
        "e ok call bo 7", "e ok call ax 5",
    ],
    "pair-dup": [
        "b fire ax", "b fire ax", "b fire bo", "b take", "b take", "b take", "b end",
        "e go call ax", "e go call ax", "e go call bo",
        "e ok call bo 9", "e ok call ax 1", "e ok call ax 2",
    ],
    "pair-cross": [
        "b call ax", "b nap ax", "b end",
        "e go call ax", "e go timer ax",
        "e ok timer ax 9", "e ok call ax 5",
    ],
    "pair-order": [
        "b call ax", "b call bo", "b end",
        "e go call ax", "e ok call ax 5",
        "e go call bo", "e ok call bo 7",
    ],

    # --- which branch runs next --------------------------------------------------------
    "sched-mark": [
        "b fork side", "b call ax", "b end",
        "b lab side", "b call bo", "b end",
        "e go call ax", "e go call bo",
        "e ok call bo 7", "e ok call ax 5",
    ],
    "sched-ready-first": [
        "b fork side", "b call ax", "b end",
        "b lab side", "b call bo", "b end",
        "e go call ax", "e ok call ax 1",
        "e go call bo", "e ok call bo 2",
    ],
    "sched-id": [
        "b fork one", "b fork two", "b call ax", "b end",
        "b lab one", "b call bo", "b end",
        "b lab two", "b call cy", "b end",
        "e go call ax", "e go call bo", "e go call cy",
        "e ok call cy 3", "e ok call bo 2", "e ok call ax 1",
    ],
    "sched-chain": [
        "b fork side", "b call ax", "b call bo", "b end",
        "b lab side", "b call cy", "b end",
        "e go call ax", "e go call cy",
        "e ok call cy 30", "e ok call ax 10",
        "e go call bo", "e ok call bo 20",
    ],

    # --- what a take reaches for ---------------------------------------------------------
    "take-first": [
        "b fire ax", "b fire bo", "b take", "b take", "b end",
        "e go call ax", "e go call bo",
        "e ok call bo 7", "e ok call ax 5",
    ],
    "take-none": [
        "b take", "b add 4", "b call ax", "b end",
        "e go call ax", "e ok call ax 6",
    ],

    # --- signals, claimed per tag as a branch goes down -----------------------------------
    "sig-claim": [
        "b fork one", "b fork two", "b fork three", "b call ax", "b end",
        "b lab one", "b wait pay", "b end",
        "b lab two", "b wait pay", "b end",
        "b lab three", "b call bo", "b end",
        "e go call ax", "e sig pay 11", "e go call bo",
        "e ok call bo 6", "e sig pay 12", "e ok call ax 9",
    ],
    "sig-tags": [
        "b wait pay", "b wait ship", "b wait pay", "b end",
        "e sig ship 40", "e sig pay 11", "e sig pay 12",
    ],
    "sig-live": [
        "b call ax", "b wait pay", "b end",
        "e sig pay 33",
        "r 70",
    ],

    # --- the live side ---------------------------------------------------------------------
    "edge-standstill": [
        "b call ax", "b call bo", "b call cy", "b end",
        "e go call ax", "e ok call ax 1",
        "r 21", "r 22",
    ],
    "edge-none": [
        "b call ax", "b call bo", "b end",
        "e go call ax", "e ok call ax 4",
        "e go call bo", "e ok call bo 6",
    ],
    "edge-empty": [
        "b call ax", "b nap ti", "b end",
        "r 11", "r 12",
    ],
    "edge-release-id": [
        "b fork one", "b fork two", "b call ax", "b end",
        "b lab one", "b call bo", "b end",
        "b lab two", "b call cy", "b end",
        "r 51", "r 52", "r 53",
    ],
    "edge-no-wait": [
        "b fork side", "b call ax", "b call bo", "b end",
        "b lab side", "b call cy", "b end",
        "r 71", "r 72", "r 73",
    ],
    "edge-feed-out": [
        "b call ax", "b call bo", "b end",
        "r 40",
    ],
    "edge-after-live-go": [
        "b fork side", "b call ax", "b call bo", "b end",
        "b lab side", "b nap ti", "b end",
        "e go call ax",
        "e go call bo", "e ok call bo 9",
        "e go timer ti", "e ok timer ti 7",
        "r 50", "r 51",
    ],
    "edge-no-match-after": [
        "b fork side", "b call ax", "b end",
        "b lab side", "b nap ti", "b end",
        "e go timer ti", "e ok timer ti 7",
        "r 31",
    ],

    # --- what the history has left over -------------------------------------------------
    "left-earliest": [
        "b call ax", "b end",
        "e go call ax", "e ok call ax 2",
        "e go timer ti", "e go child cy",
    ],
    "left-not-ok": [
        "b call ax", "b end",
        "e go call ax", "e ok call ax 2", "e ok call bo 8",
        "e sig pay 30", "e ch road 4",
    ],
    "left-unissued": [
        "b fork side", "b call ax", "b end",
        "b lab side", "b call bo", "b end",
        "e go call ax", "e ok call ax 2",
        "e go timer ti",
        "r 50",
    ],
    "left-after-live": [
        "b fork side", "b call ax", "b call bo", "b end",
        "b lab side", "b nap ti", "b end",
        "e go call ax", "e ok call ax 2",
        "e go timer ti", "e go child cy",
        "r 50",
    ],
    "stop-mid": [
        "b fork side", "b call ax", "b end",
        "b lab side", "b call bo", "b end",
        "e go call ax", "e go call bo",
        "e ok call ax 5", "e ok call bo 7",
    ],

    # --- markers ----------------------------------------------------------------------------
    "ver-recorded": [
        "b mark road 3", "b end",
        "e ch road 1",
    ],
    "ver-replay-zero": [
        "b mark road 3", "b call ax", "b end",
        "e go call ax", "e ok call ax 5",
    ],
    "ver-live-cur": [
        "b call ax", "b mark road 3", "b end",
        "r 80",
    ],
    "ver-empty-zero": [
        "b mark road 3", "b end",
    ],
    "ver-per-key": [
        "b mark road 5", "b mark turn 5", "b mark road 5", "b end",
        "e ch turn 7", "e ch road 1", "e ch road 2",
    ],
    "ver-branch": [
        "b mark road 2", "b jz slow", "b call fast", "b jmp out",
        "b lab slow", "b call slow", "b lab out", "b end",
        "e go call slow", "e ok call slow 6",
    ],

    # --- the step ceiling, the grammar, and an everyday program ------------------------------
    "over-steps": [
        "b set 1", "b lab spin", "b add 1", "b jmp spin", "b end",
    ],
    "parse-blank": [
        "b call ax", "", "b end", "",
        "e go call ax", "", "e ok call ax 6",
    ],
    "plain-ordinary": [
        "b fork side", "b call ax", "b wait pay", "b fire bo", "b take", "b add 2", "b end",
        "b lab side", "b nap ti", "b spawn cy", "b end",
        "e go call ax", "e go timer ti",
        "e ok timer ti 3", "e go child cy", "e ok child cy 9",
        "e sig pay 21", "e ok call ax 4", "e go call bo", "e ok call bo 12",
    ],
}

ORDER = sorted(CASES)


def prog(name):
    return list(CASES[name])
