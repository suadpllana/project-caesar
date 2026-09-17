"""A slot request that becomes a request for the box."""
from hb import hold, say

FLOOR = 4


def check(st, job, node, mode):
    box = node.split(":")[0]
    held = hold.slots(st, job, box)
    if len(held) < FLOOR:
        return None
    wet = mode == "w" or any("w" in hold.letters(st, job, one) for one in held)
    return "w" if wet else "r"


def settle(st, job, box, trig):
    for node in hold.slots(st, job, box):
        while hold.letters(st, job, node):
            hold.sub(st, job, node)
            say.free(st, job, node)
    hold.put(st, job, trig[0], trig[1])
    say.grant(st, job, trig[0], trig[1])
    return {box}
