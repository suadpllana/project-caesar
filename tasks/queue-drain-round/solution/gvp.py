# What a round gives up on.
#
# Everything the round was allowed to reach and did not move is past its day,
# and the house does not carry it forward. Giving up on one is not a tidy-up at
# the end though: an obligation sits at a place in its payer's line, and taking
# it out is what lets the round reach the ones behind it. Those may well be
# affordable, and the round is required to leave nothing on the table.
#
# So this hands back one, and the round asks again. The oldest goes first, which
# is the order the house wrote the obligations down in.


def give(b, cap, plan):
    out = []
    for n in b.who():
        q = b.line(n)
        for k in range(plan.get(n, 0), cap[n]):
            out.append(q[k])
    if not out:
        return []
    out.sort(key=lambda o: o.sq)
    return [out[0].i]
