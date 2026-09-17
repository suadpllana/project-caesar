"""A slot request that becomes a request for the box."""
from hb import book, tell

FLOOR = 4


def check(st, job, node, mode):
    box = node.split(":")[0]
    held = book.slots(st, job, box)
    if len(held) < FLOOR:
        return None
    wet = mode == "w" or any("w" in book.letters(st, job, one) for one in held)
    return "w" if wet else "r"


def settle(st, job, box, trig):
    for node in book.slots(st, job, box):
        while book.letters(st, job, node):
            book.sub(st, job, node)
            tell.free(st, job, node)
    book.put(st, job, trig[0], trig[1])
    tell.grant(st, job, trig[0], trig[1])
    return {box}
