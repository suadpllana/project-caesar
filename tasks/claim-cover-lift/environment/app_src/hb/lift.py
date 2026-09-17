from hb import book, tell

FLOOR = 4


def check(st, job, node, mode):
    box = node[:node.find(":")]
    kept = book.kept(st, job, box)
    if len(kept) < FLOOR:
        return None
    wet = mode == "w" or any(book.mode(st, job, one) == "w" for one in kept)
    return "w" if wet else "r"


def settle(st, job, box, trig):
    for node in book.kept(st, job, box):
        book.sub(st, job, node)
        tell.free(st, job, node)
    node, mode = trig
    book.add(st, job, node, mode)
    tell.grant(st, job, node, mode)
    return {box}
