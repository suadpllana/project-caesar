from hb import book
from hb.desk import boxof


def clash(one, two):
    return one == "w" or two == "w"


def cover(st, job, node, mode):
    got = book.mode(st, job, node)
    return got is not None and (mode == "r" or got == "w")


def blockers(st, job, node, mode):
    out = set()
    for other, got in book.at(st, node).items():
        if other != job and clash(mode, got):
            out.add(other)
    box = boxof(node)
    if box != node:
        for other, got in book.at(st, box).items():
            if other != job and clash(mode, got):
                out.add(other)
    return out
