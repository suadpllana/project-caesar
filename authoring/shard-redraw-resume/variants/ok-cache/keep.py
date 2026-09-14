"""The checkpoint as an immutable record, and what a return puts back."""

import collections

from rig import say

Point = collections.namedtuple("Point", "epoch seen done sc gt")


def checkpoint(run, st):
    if run.ckpt > 0 and st["done"] % run.ckpt == 0:
        st["saved"] = Point(st["epoch"], st["seen"], st["done"], st["sc"], st["gt"])
        say.save(run, st["done"], st["epoch"], st["seen"])


def restore(run, st):
    back = st["saved"] or Point(0, 0, 0, run.scale, 0)
    st["epoch"], st["seen"], st["done"] = back.epoch, back.seen, back.done
    st["sc"], st["gt"] = back.sc, back.gt
    say.kill(run, st["epoch"], st["seen"])
