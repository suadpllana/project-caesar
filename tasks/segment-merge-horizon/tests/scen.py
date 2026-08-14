"""The scenario set.

Each entry is an operation stream against the store plus the reading of the rule it is
aimed at. `aim` is quoted back in the verifier's failure messages, so a submission that
fails one case is told which distinction it got wrong rather than only which number moved.

The stream is deliberately small - a few segments, a handful of keys, at most a couple of
merge jobs - because the difficulty is in what a job may discard, never in how much of it
there is. Every scenario runs in milliseconds.

This file is readable by the run. Knowing which operation sequences execute does not
produce the values they end on, and it certainly does not produce the amount of work the
cheapest correct merge spends reaching them.
"""

PUT = 0
DEL = 1
ADD = 2


def P(k, v):
    return {"op": "put", "k": k, "v": v}


def D(k):
    return {"op": "del", "k": k}


def A(k, d):
    return {"op": "add", "k": k, "d": d}


def U(i):
    return {"op": "unpin", "i": i}


F = {"op": "flush"}
M = {"op": "merge"}
N = {"op": "pin"}


SCENARIOS = [
    {
        "name": "set-only-stack",
        "aim": "the survivor rule on its own: with one read point only the newest set for "
               "a key can be seen, and everything under it is unreachable and must never "
               "be pulled",
        "ops": [P(1, 10), P(2, 5), F,
                P(1, 20), P(3, 7), F,
                P(1, 30), P(2, 9), F,
                M],
    },
    {
        "name": "adjust-over-set",
        "aim": "an adjust is not an answer: the newest record a read point can see carries "
               "a difference, so the set beneath it is still load bearing and the chain has "
               "to be resolved before anything is emitted",
        "ops": [P(1, 100), P(2, 4), F,
                A(1, 5), P(2, 6), F,
                A(1, 2), P(3, 9), F,
                M],
    },
    {
        "name": "adjust-runs-off",
        "aim": "a chain that leaves the job stays open: the base is in a segment this job "
               "does not own, so the outcome has to go out as a difference and cannot be "
               "collapsed into a set",
        "ops": [P(1, 50), F,
                A(1, 3), F,
                A(1, 4), P(2, 1), F,
                A(1, 6), F,
                M],
    },
    {
        "name": "open-outcomes-stack",
        "aim": "two open outcomes in one key: the upper record is applied on top of the "
               "lower one in the output, so it carries the difference between them and not "
               "its own total",
        "ops": [P(1, 50), P(2, 3), F,
                A(1, 2), F,
                A(1, 4), N, F,
                A(1, 3), N, F,
                A(1, 5), F,
                M],
    },
    {
        "name": "absent-bottom-drops",
        "aim": "an absent outcome at the bottom of a key can go, but only once the rest of "
               "the store has been asked and has nothing for that key",
        "ops": [P(1, 3), P(2, 8), F,
                D(1), P(3, 2), F,
                P(2, 9), F,
                M],
    },
    {
        "name": "absent-bottom-holds",
        "aim": "the same shape with a value outside the job: dropping the absence here "
               "uncovers a set this job never read and the key comes back from the dead",
        "ops": [P(1, 42), F,
                P(2, 1), F,
                D(1), F,
                P(3, 7), F,
                M],
    },
    {
        "name": "equal-outcomes-collapse",
        "aim": "two read points that resolve the same way need one record between them, "
               "and the lower of the two is the one that serves both",
        "ops": [P(1, 5), N, F,
                P(2, 2), N, F,
                P(1, 5), F,
                M],
    },
    {
        "name": "zero-difference-drops",
        "aim": "an open outcome whose difference is zero changes nothing and can go with "
               "no point read at all, which is the one drop that costs nothing to find",
        "ops": [P(1, 10), P(2, 6), F,
                A(1, 5), F,
                A(1, -5), N, F,
                A(1, 2), F,
                M],
    },
    {
        "name": "adjust-over-nothing",
        "aim": "a chain of adjusts standing on an empty key: the sum is the answer and the "
               "key is present, so an open outcome of zero is a record that has to be "
               "written and not a difference that changes nothing",
        "ops": [P(2, 1), F,
                A(1, -3), F,
                A(1, 3), N, F,
                A(1, 6), F,
                M],
    },
    {
        "name": "deep-below-floor",
        "aim": "four generations of the same keys with a single read point: only the newest "
               "record of each is reachable and the depth under it is pure cost",
        "ops": [P(1, 1), P(2, 1), F,
                P(1, 2), P(2, 2), F,
                P(1, 3), P(2, 3), F,
                P(1, 4), P(2, 4), F,
                M],
    },
    {
        "name": "read-point-on-sequence",
        "aim": "a read point landing exactly on a record's sequence sees that record, and "
               "a key whose only record in the job sits above a read point contributes "
               "nothing to it",
        "ops": [P(1, 10), F,
                P(1, 20), N, F,
                A(2, 3), F,
                P(1, 30), F,
                M],
    },
    {
        "name": "read-point-under-key",
        "aim": "a read point below every record a key has in the job: that point is served "
               "by the rest of the store and the job owes it nothing",
        "ops": [P(1, 7), N, F,
                P(2, 1), F,
                P(1, 8), F,
                P(3, 4), F,
                M],
    },
    {
        "name": "adjust-over-delete",
        "aim": "adjusts standing on a delete resolve to the adjusts themselves, so the "
               "outcome is a value and not an absence, and the delete under them is spent",
        "ops": [P(1, 9), F,
                D(1), F,
                A(1, 5), N, F,
                A(1, 2), F,
                M],
    },
    {
        "name": "job-feeds-job",
        "aim": "the output of one job is the input of the next, so a record this job "
               "synthesises has to be a legal record for the one after it",
        "ops": [P(1, 10), P(2, 2), F,
                A(1, 3), F,
                A(1, 4), F,
                M,
                A(1, 5), F,
                A(1, 6), P(2, 8), F,
                M],
    },
    {
        "name": "wide-mixed",
        "aim": "everything at once across eight keys, two read points and two jobs, with a "
               "pin released between them so the second job sees a shallower requirement "
               "than the first",
        "ops": [P(1, 5), P(2, 6), P(3, 7), P(4, 8), F,
                A(1, 2), D(2), P(5, 1), N, F,
                A(1, 3), P(3, 70), D(4), P(6, 2), F,
                P(7, 9), A(5, 4), N, F,
                M,
                A(1, 1), D(3), P(8, 4), F,
                A(5, -4), P(6, 5), F,
                U(0),
                M],
    },
]


def by_name(name):
    for s in SCENARIOS:
        if s["name"] == name:
            return s
    raise KeyError(name)
