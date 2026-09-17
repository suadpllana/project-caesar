from hb import book, line
from hb.desk import boxof


def clash(one, two):
    return one == "w" or two == "w"


def cover(st, job, node, mode):
    for held in (node, boxof(node)):
        got = book.modes(st, job, held)
        if got and (mode == "r" or "w" in got):
            return True
    return False


def blockers(st, job, node, mode, seq=None):
    out = set()
    for other, got in book.at(st, node).items():
        if other != job and any(clash(mode, m) for m in got):
            out.add(other)
    box = boxof(node)
    if box != node:
        for other, got in book.at(st, box).items():
            if other != job and any(clash(mode, m) for m in got):
                out.add(other)
    else:
        for kid in book.kids(st, box):
            for other, got in book.at(st, kid).items():
                if other != job and any(clash(mode, m) for m in got):
                    out.add(other)
    for req in line.ahead(st, node, seq):
        if req["job"] != job and clash(mode, req["mode"]):
            out.add(req["job"])
    return out
