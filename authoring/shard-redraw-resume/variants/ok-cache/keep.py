"""The checkpoint as an immutable record of the epoch's ledger and counters."""

import collections

from rig import say

Point = collections.namedtuple("Point", "epoch seen fed done sc gt")


def checkpoint(run, st):
    if run.ckpt > 0 and st["done"] % run.ckpt == 0:
        st["saved"] = Point(st["epoch"], tuple(sorted(st["seen"].items())),
                            st["fed"], st["done"], st["sc"], st["gt"])
        say.save(run, st["done"], st["epoch"], st["fed"])


def restore(run, st):
    back = st["saved"] or Point(0, (), 0, 0, run.scale, 0)
    st["epoch"], st["seen"], st["fed"] = back.epoch, dict(back.seen), back.fed
    st["done"], st["sc"], st["gt"] = back.done, back.sc, back.gt
    say.kill(run, st["epoch"], st["fed"])
