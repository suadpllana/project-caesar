from hb import hold, say

FLOOR = 4


def check(st, job, node, mode):
    box = node[:node.find(":")]
    got, wet = hold.tally(st, job, box)
    if got < FLOOR:
        return None
    return "w" if mode == "w" or wet else "r"


def settle(st, job, box, trig):
    for node in hold.slots(st, job, box):
        while hold.modes(st, job, node):
            hold.sub(st, job, node)
            say.free(st, job, node)
    node, mode = trig
    hold.add(st, job, node, mode)
    say.grant(st, job, node, mode)
    return {box}
