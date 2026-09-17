"""Whether a request is covered already, and which jobs stand in its way."""
from hb import hold, line
from hb.store import boxof


def clash(one, two):
    return one == "w" or two == "w"


def cover(st, job, node, mode):
    for held in (node, boxof(node)):
        text = hold.letters(st, job, held)
        if text and (mode == "r" or "w" in text):
            return True
    return False


def blockers(st, job, node, mode, seq=None):
    out = set()
    box = boxof(node)
    for other in hold.holders(st, node):
        if other != job and any(clash(mode, m) for m in hold.letters(st, other, node)):
            out.add(other)
    if box == node:
        for other, tal in hold.slotters(st, box).items():
            if other != job and (mode == "w" or tal[1] > 0):
                out.add(other)
    else:
        for other in hold.holders(st, box):
            if other != job and any(clash(mode, m) for m in hold.letters(st, other, box)):
                out.add(other)
    for ask in line.ahead(st, node, seq):
        if ask["job"] != job and clash(mode, ask["mode"]):
            out.add(ask["job"])
    return out
