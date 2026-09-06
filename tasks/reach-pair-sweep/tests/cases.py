"""Hand programs, one per graded decision, plus the ordinary side of each fence.

The first six name a decision and separate a specific wrong reading of it. The rest are the
must-still-work side: a collector that keeps everything, or clears everything, or re-queues on
every pass, fails these even though it passes some of the six.
"""

CASES = {
    # a pair's value joins once its key is reached, and that can cascade; listed back to front
    # so one sweep of the table settles only the first link
    "chain": ["new 1", "new 2", "new 3",
              "pair 2 3", "pair 1 2",
              "slot a 1", "collect"],

    # object 1 is kept only to run its finalizer, and its closure reaches the key of a pair
    "hold-pair": ["new 1 fin", "new 2", "new 3",
                  "set 1 x 2", "pair 2 3", "collect"],

    # a weak reference to an object kept only for its finalizer clears anyway
    "weak-on-held": ["new 1 fin", "weak w 1", "collect"],

    # 2 is reachable only from 1, and both are finalizable: the queue is settled before keeping
    "queue-first": ["new 1 fin", "new 2 fin", "set 1 x 2", "collect"],

    # stored back by its own finalizer, dropped again, and never finalized a second time
    "comes-back": ["new 1 fin s", "collect", "runfin", "collect", "slot s -", "collect"],

    # the same, watched: the reference does not clear twice
    "stays-clear": ["new 1 fin s", "weak w 1", "collect", "runfin", "collect",
                    "slot s -", "collect"],

    # ---- the must-still-work side -------------------------------------------------

    # everything is reachable; a collector that releases anything here is wrong
    "all-live": ["new 1", "new 2", "new 3", "set 1 x 2", "set 2 y 3",
                 "slot a 1", "collect", "collect"],

    # an ordinary drop still releases
    "plain-drop": ["new 1", "new 2", "slot a 1", "collect", "slot a -", "collect"],

    # a weak reference to a reachable object must not clear
    "weak-live": ["new 1", "weak w 1", "slot a 1", "collect", "collect"],

    # a pair whose key is unreachable keeps nothing alive
    "dead-key": ["new 1", "new 2", "pair 1 2", "collect"],

    # frames nest, and closing one drops what only it held
    "frames": ["new 1", "new 2", "slot a 1", "push", "slot b 2", "collect",
               "pop", "collect"],

    # a finalizer that stores nothing: queued, run, then released
    "quiet-fin": ["new 1 fin", "collect", "runfin", "collect"],

    # repeated collections must not queue the same finalizer twice
    "no-requeue": ["new 1 fin", "collect", "collect", "collect"],

    # an object held for a finalizer keeps its whole field closure, not just itself
    "hold-closure": ["new 1 fin", "new 2", "new 3", "set 1 x 2", "set 2 y 3", "collect"],

    # a value pulled in by a pair is itself a key of the next pair, two links deep, live side
    "chain-live": ["new 1", "new 2", "new 3", "new 4",
                   "pair 3 4", "pair 2 3", "pair 1 2", "slot a 1", "collect"],

    # nothing at all is rooted: everything without a finalizer goes at once
    "empty-roots": ["new 1", "new 2", "set 1 x 2", "collect"],
}

ORDER = sorted(CASES)


def ops(name):
    return [tuple(ln.split()) for ln in CASES[name]]
