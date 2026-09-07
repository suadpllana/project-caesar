"""Hand programs, one per graded decision, plus the ordinary side of each fence.

An object promotes after surviving two collections, so `collect collect` is the shortest way to
move something into old space and is why several of these open that way.
"""

CASES = {
    # --- the pair table ------------------------------------------------------------

    # a pair's value joins once its key is reached, and the pull cascades; written back to
    # front so one sweep of the table settles only the first link
    "chain": ["new 1", "new 2", "new 3", "pair 2 3", "pair 1 2", "slot a 1", "collect"],

    # a pair whose key is unreachable keeps nothing alive
    "dead-key": ["new 1", "new 2", "pair 1 2", "collect"],

    # an old key is live for the whole of a minor collection, so its value is kept
    "old-key": ["new 1", "slot a 1", "collect", "collect",
                "new 2", "pair 1 2", "collect"],

    # --- the remembered set --------------------------------------------------------

    # 1 is promoted, then points into the nursery: 2 is live only through the remembered set
    "rset-root": ["new 1", "slot a 1", "collect", "collect",
                  "new 2", "set 1 x 2", "collect"],

    # the same, after the field is overwritten: the entry is stale and 2 is garbage
    "rset-stale": ["new 1", "slot a 1", "collect", "collect",
                   "new 2", "set 1 x 2", "set 1 x -", "collect"],

    # a nursery object reached only through an old field, two links deep
    "rset-deep": ["new 1", "slot a 1", "collect", "collect",
                  "new 2", "new 3", "set 2 y 3", "set 1 x 2", "collect"],

    # an object can promote with a field already pointing into the nursery; that edge must be
    # recorded at promotion, before the old object stops being traced by minor collections
    "rset-promote": ["new 1", "slot a 1", "collect", "new 2", "set 1 x 2",
                     "collect", "slot a -", "collect"],

    # --- finalizers ----------------------------------------------------------------

    # 2 is reachable only from 1, and both are finalizable: the queue is settled first
    "queue-first": ["new 1 fin", "new 2 fin", "set 1 x 2", "collect"],

    # an object held for a finalizer keeps its whole field closure
    "hold-closure": ["new 1 fin", "new 2", "new 3", "set 1 x 2", "set 2 y 3", "collect"],

    # held only for its finalizer, so its closure reaches a pair key
    "hold-pair": ["new 1 fin", "new 2", "new 3", "set 1 x 2", "pair 2 3", "collect"],

    # stored back by its own finalizer, dropped again, never finalized twice
    "comes-back": ["new 1 fin s", "collect", "runfin", "collect", "slot s -",
                   "collect", "collectfull"],

    # repeated collections must not queue the same finalizer twice
    "no-requeue": ["new 1 fin", "collect", "collect", "collect"],

    # --- promotion -----------------------------------------------------------------

    # an object kept only to run its finalizer does not age, so it cannot promote
    "held-no-age": ["new 1 fin", "new 2", "slot a 2", "collect", "collect", "collect"],

    # a pinned object survives and ages but stays where it is
    "pinned": ["new 1", "slot a 1", "pin 1", "collect", "collect", "collect"],

    # and promotes at the first collection it survives after the pin comes off
    "unpinned": ["new 1", "slot a 1", "pin 1", "collect", "collect",
                 "unpin 1", "collect"],

    # --- weak references -----------------------------------------------------------

    # a weak reference to an object held only for its finalizer clears anyway
    "weak-on-held": ["new 1 fin", "weak w 1", "collect"],

    # a minor collection says nothing about old space, so an old referent is left alone
    "weak-old": ["new 1", "slot a 1", "weak w 1", "collect", "collect",
                 "slot a -", "collect"],

    # and the full collection that does examine it clears it
    "weak-old-full": ["new 1", "slot a 1", "weak w 1", "collect", "collect",
                      "slot a -", "collectfull"],

    # a weak reference to a reachable object must not clear
    "weak-live": ["new 1", "weak w 1", "slot a 1", "collect", "collect"],

    # cleared, resurrected, dropped again: it does not clear twice
    "stays-clear": ["new 1 fin s", "weak w 1", "collect", "runfin", "collect",
                    "slot s -", "collect"],

    # --- roots and the ordinary side ------------------------------------------------

    # the global table and the handle stack are roots too
    "globals": ["new 1", "new 2", "glob g1 1", "hold 2", "collect", "collect"],

    # dropping a handle lets the object go
    "handle-drop": ["new 1", "hold 1", "collect", "drop", "collect"],

    # everything reachable stays, and nothing is released
    "all-live": ["new 1", "new 2", "new 3", "set 1 x 2", "set 2 y 3", "slot a 1",
                 "collect", "collect"],

    # an ordinary drop still releases
    "plain-drop": ["new 1", "new 2", "slot a 1", "collect", "slot a -", "collect"],

    # frames nest, and closing one drops what only it held
    "frames": ["new 1", "new 2", "slot a 1", "push", "slot b 2", "collect",
               "pop", "collect"],

    # a minor collection never releases an old object, however unreachable it looks
    "old-safe": ["new 1", "slot a 1", "collect", "collect", "slot a -",
                 "collect", "collect"],
}

ORDER = sorted(CASES)


def ops(name):
    return [tuple(ln.split()) for ln in CASES[name]]
