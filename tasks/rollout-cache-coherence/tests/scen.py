"""The scenario set the verifier drives the rebuilt engine through.

Every scenario is built to fail one specific wrong reading of the invalidation rule
while a second scenario fails the opposite overreaction, so neither "invalidate on every
push" nor "never invalidate" can pass the set.  The map from scenario to the mistake it
catches is in test_outputs.py, next to the assertions.

Prompts overlap on purpose: P3 shares its first block with P1, so cross-request reuse is
partial rather than all-or-nothing, and a block-granularity error shows up as a counter
difference rather than only as wrong tokens.

Only one scenario runs the page pool dry. That is deliberate. Once eviction and preemption
start firing, the totals depend on which block a least-recently-used sweep happens to pick
when several are equally old, and two faithful implementations of the same policy disagree
there. The verifier grades work counters only where nothing is evicted and nothing is
preempted; `pressure` is graded on the tokens and the rewinds, which eviction order cannot
move. See test_outputs.py.
"""

P1 = [5, 9, 14, 3, 21, 7, 2, 11, 33, 41, 6, 19, 28, 8, 52, 17]
P2 = [12, 44, 5, 9, 14, 3, 21, 7, 30, 26]
P3 = [5, 9, 14, 3, 60, 13, 44, 22, 9, 5, 17, 38]

BASE_SEEDS = {
    "emb": 3300, "l0.wq": 3317, "l0.wk": 3334, "l0.wv": 3351, "l0.wo": 3368,
    "l0.w1": 3385, "l0.w2": 3402, "l1.wq": 3419, "l1.wk": 3436, "l1.wv": 3453,
    "l1.wo": 3470, "l1.w1": 3487, "l1.w2": 3504, "l2.wq": 3521, "l2.wk": 3538,
    "l2.wv": 3555, "l2.wo": 3572, "l2.w1": 3589, "l2.w2": 3606, "l3.wk": 3623,
    "l3.wv": 3640, "l3.wo": 3657, "l3.w1": 3674, "l3.w2": 3691, "gsc": 3708,
    "head": 3725,
}


def add(rid, prompt, adapter=None, max_new=6):
    return {"op": "add", "rid": rid, "prompt": list(prompt), "adapter": adapter,
            "max_new": max_new}


def step(n=1):
    return {"op": "step", "n": n}


def sync(ups):
    return {"op": "sync", "ups": [list(u) for u in ups]}


def sleep(level):
    return {"op": "sleep", "level": level}


WAKE = {"op": "wake"}
DRAIN = {"op": "drain"}


SCENARIOS = [
    {
        "name": "group",
        "over": {"pages": 160},
        "ops": [
            add("g0", P1), add("g1", P1), add("g2", P1), add("g3", P3),
            DRAIN,
        ],
    },
    {
        "name": "neutral-base",
        "over": {"pages": 160},
        "ops": [
            add("n0", P1, max_new=8), add("n1", P1, max_new=8),
            step(4),
            sync([[None, "l3.wo", 4101], [None, "gsc", 4102], [None, "head", 4103]]),
            add("n2", P1, max_new=5), add("n3", P3, max_new=5),
            DRAIN,
        ],
    },
    {
        "name": "relevant-base",
        "over": {"pages": 160},
        "ops": [
            add("r0", P1, max_new=8), add("r1", P1, max_new=8),
            step(4),
            sync([[None, "l1.wk", 4201]]),
            add("r2", P1, max_new=5), add("r3", P3, max_new=5),
            DRAIN,
        ],
    },
    {
        "name": "tied-push",
        "over": {"pages": 160},
        "ops": [
            add("t0", P1, max_new=8), add("t1", P1, max_new=8),
            step(4),
            sync([[None, "l3.wq", 4301]]),
            add("t2", P1, max_new=5), add("t3", P3, max_new=5),
            DRAIN,
        ],
    },
    {
        "name": "adapter-share",
        "over": {"pages": 160},
        "ops": [
            add("s0", P1, None, 6),
            step(2),
            add("s1", P1, "a1", 6), add("s2", P1, "a2", 6), add("s3", P1, "b1", 6),
            DRAIN,
        ],
    },
    {
        "name": "adapter-push",
        "over": {"pages": 160},
        "ops": [
            add("p0", P1, None, 8), add("p1", P1, "a1", 8), add("p2", P1, "b1", 8),
            step(4),
            sync([["b1", "l2.wk", 4501]]),
            add("p3", P1, None, 4), add("p4", P1, "b1", 4),
            DRAIN,
        ],
    },
    {
        "name": "adapter-neutral-push",
        "over": {"pages": 160},
        "ops": [
            add("q0", P1, None, 8), add("q1", P1, "a1", 8),
            step(4),
            sync([["a1", "head", 4601]]),
            add("q2", P1, "a1", 4),
            DRAIN,
        ],
    },
    {
        "name": "replayed-push",
        "over": {"pages": 160},
        "ops": [
            add("z0", P1, max_new=8), add("z1", P1, "b1", 8),
            step(4),
            sync([[None, "l0.wk", BASE_SEEDS["l0.wk"]], [None, "emb", BASE_SEEDS["emb"]]]),
            add("z2", P1, max_new=5),
            DRAIN,
        ],
    },
    {
        "name": "offload-cycle",
        "over": {"pages": 160},
        "ops": [
            add("o0", P1, max_new=8), add("o1", P3, max_new=8),
            step(3),
            sleep(1), WAKE,
            step(3),
            add("o2", P1, max_new=4),
            sleep(2), WAKE,
            add("o3", P1, max_new=4),
            DRAIN,
        ],
    },
    {
        "name": "pressure",
        "over": {"pages": 10, "max_batch": 3},
        "ops": [
            add("x0", P1, max_new=6), add("x1", P3, max_new=6), add("x2", P2, max_new=6),
            add("x3", P1, "a1", 6), add("x4", P2, "b1", 6),
            step(5),
            sync([[None, "l2.wv", 4901]]),
            DRAIN,
        ],
    },
    {
        "name": "mixed",
        "over": {"pages": 40, "max_batch": 3},
        "ops": [
            add("m0", P1, None, 9), add("m1", P1, "a1", 9), add("m2", P3, "b1", 9),
            step(3),
            sync([[None, "l3.w1", 5001], [None, "l3.w2", 5002]]),
            step(2),
            sync([["a1", "l3.wq", 5003]]),
            add("m3", P1, "a2", 5),
            step(2),
            sleep(1), WAKE,
            sync([[None, "l0.wv", 5004]]),
            add("m4", P3, None, 5),
            step(4),
            sleep(2), WAKE,
            sync([[None, "gsc", BASE_SEEDS["gsc"]]]),
            DRAIN,
        ],
    },
]


def by_name(name):
    for s in SCENARIOS:
        if s["name"] == name:
            return s
    raise KeyError(name)
