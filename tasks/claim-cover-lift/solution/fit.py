from hb import hold, line
from hb.store import boxof


def clash(one, two):
    return one == "w" or two == "w"


def cover(st, job, node, mode):
    for held in (node, boxof(node)):
        got = hold.modes(st, job, held)
        if got and (mode == "r" or "w" in got):
            return True
    return False


def blockers(st, job, node, mode, seq=None):
    out = set()
    for other, got in hold.at(st, node).items():
        if other != job and any(clash(mode, m) for m in got):
            out.add(other)
    box = boxof(node)
    if box != node:
        for other, got in hold.at(st, box).items():
            if other != job and any(clash(mode, m) for m in got):
                out.add(other)
    else:
        for other, sum_ in hold.under(st, box).items():
            if other != job and (mode == "w" or sum_[1] > 0):
                out.add(other)
    for req in line.ahead(st, node, seq):
        if req["job"] != job and clash(mode, req["mode"]):
            out.add(req["job"])
    return out
