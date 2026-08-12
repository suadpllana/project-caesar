"""The scenario set the verifier drives the loop through.

Each entry is one rollout worker's op list. They are aimed, one at a time, at the
readings of the rule a solver is likely to settle on: a reply that survives the render
whole, a reply whose tail is swallowed by what follows it, a reply whose own prompt
moves underneath it, a turn made untrainable by text appended two turns later, a tool
result with no resume point anywhere in it, one dense with them, retries that throw work
away, and two episodes sharing one loop.

The texts are drawn from the character set the tokenizer was built over. Which of them
carry resume points and which do not is deliberate and is what separates the cases.
"""

SCENARIOS = [
    {
        "name": "one-turn",
        "ops": [
            {"op": "begin", "ep": "e0", "salt": 4409},
            {"op": "user", "ep": "e0", "text": "check the stale queue for #q4821"},
            {"op": "turn", "ep": "e0", "cap": 24},
            {"op": "end", "ep": "e0"},
        ],
    },
    {
        "name": "append",
        "ops": [
            {"op": "begin", "ep": "e0", "salt": 7717},
            {"op": "user", "ep": "e0", "text": "check the stale queue for #q4821"},
            {"op": "turn", "ep": "e0", "cap": 24},
            {"op": "tool", "ep": "e0", "text": "status=ok items=12 @w/ingest/queue"},
            {"op": "turn", "ep": "e0", "cap": 24},
            {"op": "end", "ep": "e0"},
        ],
    },
    {
        "name": "two-tools",
        "ops": [
            {"op": "begin", "ep": "e0", "salt": 1228},
            {"op": "user", "ep": "e0", "text": "trace the late shard for #q3307"},
            {"op": "turn", "ep": "e0", "cap": 24},
            {"op": "tool", "ep": "e0", "text": "status=late lag=284 @w/router/shard"},
            {"op": "tool", "ep": "e0", "text": "depth=19 held=4 @w/router/lease"},
            {"op": "turn", "ep": "e0", "cap": 24},
            {"op": "end", "ep": "e0"},
        ],
    },
    {
        "name": "short-reply",
        "ops": [
            {"op": "begin", "ep": "e0", "salt": 5051},
            {"op": "user", "ep": "e0", "text": "count the warm buffer for #q7712"},
            {"op": "turn", "ep": "e0", "cap": 2},
            {"op": "tool", "ep": "e0", "text": "items=6 @w/keeper/buffer"},
            {"op": "turn", "ep": "e0", "cap": 3},
            {"op": "end", "ep": "e0"},
        ],
    },
    {
        "name": "truncated",
        "ops": [
            {"op": "begin", "ep": "e0", "salt": 9931},
            {"op": "user", "ep": "e0", "text": "drain the paused stream for #q2264"},
            {"op": "turn", "ep": "e0", "cap": 5},
            {"op": "tool", "ep": "e0", "text": "status=drained sent=88 @w/shipper/stream"},
            {"op": "turn", "ep": "e0", "cap": 5},
            {"op": "end", "ep": "e0"},
        ],
    },
    {
        "name": "no-anchor",
        "ops": [
            {"op": "begin", "ep": "e0", "salt": 6173},
            {"op": "user", "ep": "e0", "text": "list the mixed worker for #q5519"},
            {"op": "turn", "ep": "e0", "cap": 24},
            {"op": "tool", "ep": "e0", "text": "status=warn lag=155 rate=12 sent=51"},
            {"op": "turn", "ep": "e0", "cap": 24},
            {"op": "tool", "ep": "e0", "text": "status=warn items=25 gap=11 held=15"},
            {"op": "turn", "ep": "e0", "cap": 24},
            {"op": "end", "ep": "e0"},
        ],
    },
    {
        "name": "anchor-dense",
        "ops": [
            {"op": "begin", "ep": "e0", "salt": 2857},
            {"op": "user", "ep": "e0", "text": "audit the pinned record for #q8043"},
            {"op": "turn", "ep": "e0", "cap": 24},
            {"op": "tool", "ep": "e0",
             "text": "#q8043 status=ok @w/reducer/record\n#q8044 status=ok @w/reducer/offset"},
            {"op": "turn", "ep": "e0", "cap": 24},
            {"op": "tool", "ep": "e0",
             "text": "#q8045 depth=3 @w/reducer/quota\n#q8046 depth=7 @w/reducer/cursor"},
            {"op": "turn", "ep": "e0", "cap": 24},
            {"op": "end", "ep": "e0"},
        ],
    },
    {
        "name": "back-reach",
        "ops": [
            {"op": "begin", "ep": "e0", "salt": 761627},
            {"op": "user", "ep": "e0", "text": "trace the late shard for #q3307"},
            {"op": "turn", "ep": "e0", "cap": 3},
            {"op": "tool", "ep": "e0", "text": "ok"},
            {"op": "turn", "ep": "e0", "cap": 24},
            {"op": "tool", "ep": "e0", "text": "status=warn lag=155 rate=12 sent=51"},
            {"op": "turn", "ep": "e0", "cap": 24},
            {"op": "tool", "ep": "e0", "text": "status=empty age=2 @w/planner/digest"},
            {"op": "turn", "ep": "e0", "cap": 24},
            {"op": "end", "ep": "e0"},
        ],
    },
    {
        "name": "retry",
        "ops": [
            {"op": "begin", "ep": "e0", "salt": 3391},
            {"op": "user", "ep": "e0", "text": "replay the dropped batch for #q1187"},
            {"op": "turn", "ep": "e0", "cap": 24},
            {"op": "retry", "ep": "e0", "text": "call failed, handle is not a segment"},
            {"op": "turn", "ep": "e0", "cap": 24},
            {"op": "end", "ep": "e0"},
        ],
    },
    {
        "name": "retry-late",
        "ops": [
            {"op": "begin", "ep": "e0", "salt": 8123},
            {"op": "user", "ep": "e0", "text": "widen the narrow window for #q6605"},
            {"op": "turn", "ep": "e0", "cap": 24},
            {"op": "tool", "ep": "e0", "text": "status=held age=41 @w/walker/window"},
            {"op": "turn", "ep": "e0", "cap": 24},
            {"op": "retry", "ep": "e0", "text": "quota rejected the second call"},
            {"op": "turn", "ep": "e0", "cap": 24},
            {"op": "tool", "ep": "e0", "text": "status=ok acked=9 @w/walker/lease"},
            {"op": "turn", "ep": "e0", "cap": 24},
            {"op": "end", "ep": "e0"},
        ],
    },
    {
        "name": "interleave",
        "ops": [
            {"op": "begin", "ep": "e0", "salt": 4703},
            {"op": "begin", "ep": "e1", "salt": 6449},
            {"op": "user", "ep": "e0", "text": "show the split cursor for #q9902"},
            {"op": "user", "ep": "e1", "text": "reset the idle digest for #q4416"},
            {"op": "turn", "ep": "e0", "cap": 24},
            {"op": "turn", "ep": "e1", "cap": 24},
            {"op": "tool", "ep": "e0", "text": "status=ok items=31 @w/planner/cursor"},
            {"op": "tool", "ep": "e1", "text": "status=empty age=2 @w/planner/digest"},
            {"op": "turn", "ep": "e1", "cap": 24},
            {"op": "turn", "ep": "e0", "cap": 24},
            {"op": "end", "ep": "e1"},
            {"op": "end", "ep": "e0"},
        ],
    },
    {
        "name": "long",
        "ops": [
            {"op": "begin", "ep": "e0", "salt": 1523},
            {"op": "user", "ep": "e0", "text": "inspect the merged offset for #q3728"},
            {"op": "turn", "ep": "e0", "cap": 24},
            {"op": "tool", "ep": "e0", "text": "status=ok depth=17 @w/ingest/offset"},
            {"op": "turn", "ep": "e0", "cap": 6},
            {"op": "tool", "ep": "e0", "text": "status=warn lag=25 rate=11 sent=52"},
            {"op": "turn", "ep": "e0", "cap": 24},
            {"op": "retry", "ep": "e0", "text": "the reducer refused a wide window"},
            {"op": "turn", "ep": "e0", "cap": 24},
            {"op": "tool", "ep": "e0", "text": "#q3729 status=ok @w/reducer/segment"},
            {"op": "turn", "ep": "e0", "cap": 24},
            {"op": "end", "ep": "e0"},
        ],
    },
]

BY_NAME = {s["name"]: s for s in SCENARIOS}


def by_name(name):
    return BY_NAME[name]
