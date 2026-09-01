"""The scenario set.

Each entry is a set of task programs plus the reading of the rule it is aimed at. `aim` is
quoted back in the verifier's failure messages, so a submission that fails one case is told
which distinction it got wrong rather than only which tick moved.

A program is a list of steps: run for n ticks, take a mutex with a timeout (-1 waits for
ever), release a mutex, or sleep. Priorities are integers and larger is more urgent.

Two of these exist to fail an implementation that does too much rather than too little, which
is the half a defensive rewrite gets wrong: a task blocking on a holder that already outranks
it must not move anything, and neither must one blocking at exactly the holder's priority.

This file is readable by the run. Knowing which programs execute does not produce the
schedule they end on.
"""

import hashlib
import random


def T(tid, base, start, prog):
    return {"id": tid, "base": base, "start": start, "prog": prog}


def run(n):
    return ["run", n]


def lock(m, d=-1):
    return ["lock", m, d]


def rel(m):
    return ["unlock", m]


def nap(n):
    return ["sleep", n]


SCENARIOS = [
    {
        "name": "one-mutex-one-waiter",
        "aim": "the shape every write up of this covers, and the one the shipped policy gets "
               "right: a single holder, a single waiter, raise on block and put back on "
               "release. It has to keep working",
        "tasks": [
            T(1, 9, 4, [lock(1), run(2), rel(1), run(1)]),
            T(2, 5, 2, [run(8)]),
            T(3, 1, 0, [lock(1), run(6), rel(1), run(1)]),
        ],
    },
    {
        "name": "release-with-queue-behind",
        "aim": "a holder of two mutexes releases one of them while a task is still waiting "
               "on the other: what it goes back to is what the remaining waiter is worth, "
               "never its own priority",
        "tasks": [
            T(1, 9, 7, [lock(1), run(2), rel(1), run(1)]),
            T(2, 5, 5, [lock(2), run(2), rel(2), run(1)]),
            T(3, 4, 3, [run(14)]),
            T(4, 1, 0, [lock(1), lock(2), run(8), rel(1), run(4), rel(2), run(1)]),
        ],
    },
    {
        "name": "chain-of-three",
        "aim": "the task holding the processor is two links away: an urgent task blocks on a "
               "holder that is itself blocked, and the urgency has to travel the whole chain "
               "or it stops at the first link",
        "tasks": [
            T(1, 9, 9, [lock(1), run(2), rel(1), run(1)]),
            T(2, 6, 4, [lock(1), run(2), lock(2), run(2), rel(2), rel(1), run(1)]),
            T(3, 4, 5, [run(16)]),
            T(4, 1, 0, [lock(2), run(10), rel(2), run(2)]),
        ],
    },
    {
        "name": "chain-unwinds",
        "aim": "the same chain coming apart: as each link releases, the priority has to fall "
               "back down the chain and not stay where the peak left it",
        "tasks": [
            T(1, 9, 9, [lock(1), run(1), rel(1), run(1)]),
            T(2, 6, 3, [lock(1), run(1), lock(2), run(2), rel(2), run(2), rel(1), run(1)]),
            T(3, 5, 12, [run(8)]),
            T(4, 1, 0, [lock(2), run(9), rel(2), run(4)]),
        ],
    },
    {
        "name": "waiter-gives-up",
        "aim": "a waiter that times out stops being a reason for anybody to be urgent, so the "
               "holder has to come back down at the moment the wait ends rather than at the "
               "moment the mutex is released",
        "tasks": [
            T(1, 9, 4, [lock(1, 3), run(2), rel(1), run(2)]),
            T(2, 4, 5, [run(10)]),
            T(3, 1, 0, [lock(1), run(12), rel(1), run(1)]),
        ],
    },
    {
        "name": "one-waiter-left",
        "aim": "two tasks waiting on one mutex and the more urgent one gives up: the holder "
               "comes down to what the one still waiting is worth, which is neither where it "
               "started nor where it was",
        "tasks": [
            T(1, 9, 4, [lock(1, 4), run(2), rel(1), run(1)]),
            T(2, 6, 3, [lock(1), run(2), rel(1), run(1)]),
            T(3, 5, 6, [run(10)]),
            T(4, 1, 0, [lock(1), run(12), rel(1), run(1)]),
        ],
    },
    {
        "name": "handed-on-with-a-queue",
        "aim": "a mutex passed to the next waiter while a third task is still queued behind "
               "it: the new holder inherits from the moment it takes the mutex, not from the "
               "next time somebody blocks",
        "tasks": [
            T(1, 9, 5, [lock(1), run(2), rel(1), run(1)]),
            T(2, 2, 4, [lock(1), run(5), rel(1), run(1)]),
            T(3, 6, 12, [run(8)]),
            T(4, 1, 0, [lock(1), run(6), rel(1), run(2)]),
        ],
    },
    {
        "name": "holder-already-urgent",
        "aim": "a task blocks on a holder that already outranks it: nothing moves, and a "
               "policy that raises anyway hands the holder a priority it never earned",
        "tasks": [
            T(1, 8, 0, [lock(1), run(6), rel(1), run(2)]),
            T(2, 3, 2, [lock(1), run(2), rel(1), run(1)]),
            T(3, 5, 3, [run(6)]),
        ],
    },
    {
        "name": "equal-priorities",
        "aim": "a waiter at exactly the holder's priority: still nothing to move, and the "
               "queue order decides who runs rather than any change of priority",
        "tasks": [
            T(1, 5, 0, [lock(1), run(6), rel(1), run(2)]),
            T(2, 5, 2, [lock(1), run(3), rel(1), run(1)]),
            T(3, 4, 1, [run(5)]),
        ],
    },
    {
        "name": "carries-its-boost-onward",
        "aim": "a task that has been raised then blocks on a second mutex: what travels to "
               "the next holder is what it is worth now, not what it started as",
        "tasks": [
            T(1, 9, 6, [lock(1), run(2), rel(1), run(1)]),
            T(2, 2, 0, [lock(1), run(4), lock(2), run(3), rel(2), rel(1), run(1)]),
            T(3, 5, 8, [run(10)]),
            T(4, 1, 1, [lock(2), run(9), rel(2), run(1)]),
        ],
    },
    {
        "name": "releases-the-quiet-one-first",
        "aim": "a holder of two mutexes releases the one nobody is waiting on: that changes "
               "nothing at all, and a policy that recomputes from scratch has to arrive back "
               "where it was",
        "tasks": [
            T(1, 9, 6, [lock(2), run(2), rel(2), run(1)]),
            T(2, 4, 4, [run(12)]),
            T(3, 1, 0, [lock(1), lock(2), run(6), rel(1), run(3), rel(2), run(1)]),
        ],
    },
    {
        "name": "raised-then-sleeps",
        "aim": "a raised holder that goes to sleep still holds the mutex, so it is still the "
               "reason the urgent task is waiting and it has to wake up still raised",
        "tasks": [
            T(1, 9, 5, [lock(1), run(2), rel(1), run(1)]),
            T(2, 4, 6, [run(10)]),
            T(3, 1, 0, [lock(1), run(4), nap(4), run(3), rel(1), run(1)]),
        ],
    },
    {
        "name": "two-chains-one-task",
        "aim": "a holder with a queue on each of two mutexes: it is worth the more urgent of "
               "the two, and losing one of them leaves it worth the other",
        "tasks": [
            T(1, 9, 8, [lock(1), run(2), rel(1), run(1)]),
            T(2, 7, 6, [lock(2), run(2), rel(2), run(1)]),
            T(3, 5, 10, [run(12)]),
            T(4, 1, 0, [lock(1), lock(2), run(9), rel(1), run(4), rel(2), run(2)]),
        ],
    },
    {
        "name": "everything-at-once",
        "aim": "a chain, a second mutex, a timeout and a handover in one run, which is where "
               "a policy that handles each of them alone stops agreeing with itself",
        "tasks": [
            T(1, 9, 11, [lock(1, 6), run(2), rel(1), run(2)]),
            T(2, 7, 8, [lock(2), lock(1), run(3), rel(1), rel(2), run(1)]),
            T(3, 6, 5, [lock(1), run(2), rel(1), run(2)]),
            T(4, 4, 14, [run(10)]),
            T(5, 1, 0, [lock(2), run(4), lock(3), run(6), rel(3), rel(2), run(2)]),
            T(6, 2, 1, [lock(3), run(5), rel(3), run(2)]),
        ],
    },
]


def by_name(name):
    for s in SCENARIOS:
        if s["name"] == name:
            return s
    raise KeyError(name)


def batch(seed, n):
    """Task sets built from a seed, so there is nothing to recognise and nothing to store.

    Every set is small and shallow on purpose: the shapes that separate a correct policy from
    the textbook one are chains, second mutexes and abandoned waits, none of which need size.
    """
    rng = random.Random(seed)
    out = []
    for k in range(n):
        nt = rng.randint(3, 5)
        nm = rng.randint(1, 3)
        bases = rng.sample(range(1, 12), nt)
        tasks = []
        for i in range(nt):
            prog = []
            held = []
            for _ in range(rng.randint(1, 4)):
                pick = rng.random()
                if pick < 0.42 and len(held) < 2:
                    m = rng.randint(1, nm)
                    if m not in held:
                        d = -1 if rng.random() < 0.7 else rng.randint(1, 6)
                        prog.append(["lock", m, d])
                        held.append(m)
                        prog.append(["run", rng.randint(1, 4)])
                elif pick < 0.62 and held:
                    prog.append(["unlock", held.pop(0)])
                    prog.append(["run", rng.randint(1, 3)])
                elif pick < 0.72:
                    prog.append(["sleep", rng.randint(1, 3)])
                else:
                    prog.append(["run", rng.randint(1, 5)])
            for m in held:
                prog.append(["unlock", m])
            prog.append(["run", rng.randint(1, 3)])
            tasks.append({"id": i + 1, "base": bases[i],
                          "start": rng.choice([0, 0, 1, 2, 3, 5]), "prog": prog})
        out.append({"name": "drawn-%03d" % k, "tasks": tasks,
                    "aim": "a task set drawn at verification time, so no answer to it can have "
                           "been prepared in advance"})
    return out


def seed_from(env):
    raw = env or "0"
    return int(hashlib.sha256(raw.encode("utf-8")).hexdigest()[:12], 16)


