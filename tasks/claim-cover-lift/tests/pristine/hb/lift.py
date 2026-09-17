from hb import hold, say

FLOOR = 4


def check(st, job, node, mode):
    box = node[:node.find(":")]
    kept = hold.kept(st, job, box)
    if len(kept) < FLOOR:
        return None
    wet = mode == "w" or any(hold.mode(st, job, one) == "w" for one in kept)
    return "w" if wet else "r"


def settle(st, job, box, trig):
    for node in hold.kept(st, job, box):
        hold.sub(st, job, node)
        say.free(st, job, node)
    node, mode = trig
    hold.add(st, job, node, mode)
    say.grant(st, job, node, mode)
    return {box}
