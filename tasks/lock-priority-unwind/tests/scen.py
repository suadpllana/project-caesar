"""The scenario set.

Each entry is a set of task programs plus the reading of the rule it is aimed at. `aim` is
quoted back in the verifier's failure messages, so a submission that fails one case is told
which distinction it got wrong rather than only which tick moved.

A program is a list of steps: run for n ticks, take a mutex with a timeout (-1 waits for
ever), release a mutex, or sleep. Priorities are integers and larger is more urgent.

Two of these exist to fail an implementation that does too much rather than too little, which
is the half a defensive rewrite gets wrong: a task blocking on a holder that already outranks
it must not move anything, and neither must one blocking at exactly the holder's priority.

Five of them turn on a mutex that has been let go and not yet taken. That is a state the engine
spends real ticks in, and a policy that reads holders sees nobody there at all.

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
        "aim": "a mutex let go with a third task still queued behind the one at the head: "
               "what the queue is waiting for from that moment is the task at the head of it, "
               "which is holding nothing at all",
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
    {
        "name": "claim-with-a-queue-behind",
        "aim": "a mutex let go with two tasks queued on it. The one at the head is the only "
               "task that can take it and it has not taken it yet, so from the release onward "
               "it is what the task behind it is waiting for and it is worth what that task "
               "is worth",
        "tasks": [
            T(1, 9, 4, [lock(1), run(2), rel(1), run(1)]),
            T(2, 2, 2, [lock(1), run(4), rel(1), run(1)]),
            T(3, 5, 6, [run(12)]),
            T(4, 1, 0, [lock(1), run(8), rel(1), run(2)]),
        ],
    },
    {
        "name": "blocks-while-it-is-between-owners",
        "aim": "a task joins the queue on a mutex that is between owners: the task it has "
               "just queued behind is the one to raise, and there is no holder to raise",
        "tasks": [
            T(1, 8, 9, [lock(1), run(2), rel(1), run(1)]),
            T(2, 2, 3, [lock(1), run(5), rel(1), run(1)]),
            T(3, 4, 7, [run(14)]),
            T(4, 1, 0, [lock(1), run(7), rel(1), run(2)]),
        ],
    },
    {
        "name": "chain-through-a-claim",
        "aim": "the middle of the chain is a mutex between owners, so a walk that follows "
               "holders stops there and the urgency never reaches the task at the head of "
               "the queue, which is the one that has to run",
        "tasks": [
            T(1, 9, 7, [lock(2), run(2), rel(2), run(1)]),
            T(2, 2, 2, [lock(1), run(4), rel(1), run(1)]),
            T(3, 3, 4, [lock(2), run(1), lock(1), run(3), rel(1), rel(2), run(1)]),
            T(4, 5, 9, [run(12)]),
            T(5, 1, 0, [lock(1), run(8), rel(1), run(2)]),
        ],
    },
    {
        "name": "gives-up-behind-a-claim",
        "aim": "the task queued behind the head gives up: what has to come down is the task "
               "at the head of the queue, which holds nothing, and it has to come down at the "
               "moment the wait ends",
        "tasks": [
            T(1, 9, 5, [lock(1, 6), run(2), rel(1), run(1)]),
            T(2, 2, 3, [lock(1), run(5), rel(1), run(1)]),
            T(3, 4, 7, [run(14)]),
            T(4, 1, 0, [lock(1), run(6), rel(1), run(2)]),
        ],
    },
    {
        "name": "claimant-holds-as-well",
        "aim": "the task at the head of one queue is the holder of another mutex with a queue "
               "of its own: it is worth the more urgent of the two, so the two cases are one "
               "quantity rather than two rules",
        "tasks": [
            T(1, 9, 8, [lock(1), run(2), rel(1), run(1)]),
            T(2, 2, 3, [lock(2), run(2), lock(1), run(3), rel(1), rel(2), run(1)]),
            T(3, 7, 11, [lock(2), run(2), rel(2), run(1)]),
            T(4, 5, 13, [run(10)]),
            T(5, 1, 0, [lock(1), run(7), rel(1), run(2)]),
        ],
    },
    {
        "name": "comes-down-while-it-is-still-waiting",
        "aim": "the task queued behind the head gives up while the mutex is still between "
               "owners, so what has to come down is a task that holds nothing and is not "
               "waiting for anybody either",
        "tasks": [
            T(1, 8, 2, [lock(1, 6), run(2), rel(1), run(1)]),
            T(2, 2, 1, [lock(1), run(4), rel(1), run(1)]),
            T(3, 4, 6, [run(8)]),
            T(4, 11, 4, [run(8)]),
            T(5, 1, 0, [lock(1), run(3), rel(1), run(2)]),
        ],
    },
    {
        "name": "chain-forms-after-the-claim",
        "aim": "the chain is built while a mutex is already between owners: a task queued "
               "behind the head is itself the holder of something, and when somebody blocks on "
               "that the rise has to travel through a mutex that has no holder to travel "
               "through",
        "tasks": [
            T(1, 1, 0, [lock(1), run(3), rel(1), run(2)]),
            T(2, 2, 1, [lock(1), run(4), rel(1), run(1)]),
            T(3, 3, 2, [lock(2), run(1), lock(1), run(3), rel(1), rel(2), run(1)]),
            T(4, 10, 5, [run(8)]),
            T(5, 11, 7, [lock(2), run(2), rel(2), run(1)]),
            T(6, 6, 8, [run(12)]),
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

    Every set is small and shallow on purpose: what separates a correct policy from the
    textbook one is queues, chains, second mutexes and abandoned waits, and none of those need
    size. Mutexes are kept few and critical sections long so that the sets contend - a task set
    where nothing ever queues behind anything grades nothing.
    """
    rng = random.Random(seed)
    out = []
    for k in range(n):
        nt = rng.randint(4, 6)
        nm = rng.randint(1, 2)
        bases = rng.sample(range(1, 12), nt)
        tasks = []
        for i in range(nt):
            prog = []
            held = []
            m0 = rng.randint(1, nm)
            prog.append(["lock", m0, -1 if rng.random() < 0.75 else rng.randint(2, 9)])
            held.append(m0)
            prog.append(["run", rng.randint(3, 8)])
            for _ in range(rng.randint(1, 3)):
                pick = rng.random()
                if pick < 0.58 and len(held) < 2:
                    m = rng.randint(1, nm)
                    if m not in held:
                        d = -1 if rng.random() < 0.75 else rng.randint(2, 9)
                        prog.append(["lock", m, d])
                        held.append(m)
                        prog.append(["run", rng.randint(2, 6)])
                elif pick < 0.78 and held:
                    prog.append(["unlock", held.pop(0)])
                    prog.append(["run", rng.randint(1, 4)])
                elif pick < 0.85:
                    prog.append(["sleep", rng.randint(1, 3)])
                else:
                    prog.append(["run", rng.randint(1, 4)])
            for m in held:
                prog.append(["unlock", m])
            prog.append(["run", rng.randint(1, 3)])
            tasks.append({"id": i + 1, "base": bases[i],
                          "start": rng.choice([0, 0, 0, 1, 1, 2, 2, 3, 4, 5]), "prog": prog})
        out.append({"name": "drawn-%03d" % k, "tasks": tasks,
                    "aim": "a task set drawn at verification time, so no answer to it can have "
                           "been prepared in advance"})
    return out


def seed_from(env):
    raw = env or "0"
    return int(hashlib.sha256(raw.encode("utf-8")).hexdigest()[:12], 16)


