from hb import book, tell

FLOOR = 4


def check(st, job, node, mode):
    box = node[:node.find(":")]
    got, wet = book.tally(st, job, box)
    if got < FLOOR:
        return None
    return "w" if mode == "w" or wet else "r"


def settle(st, job, box, trig):
    for node in book.slots(st, job, box):
        while book.modes(st, job, node):
            book.sub(st, job, node)
            tell.free(st, job, node)
    node, mode = trig
    book.add(st, job, node, mode)
    tell.grant(st, job, node, mode)
    return {box}
