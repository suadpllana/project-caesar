# What a round moves.
#
# The house settles a round in one motion, so money a party is owed inside the
# round is money it can pay with. That makes the question "which obligations
# move" a joint one rather than a sequence: a party with nothing in hand can
# still discharge its head when the party behind it discharges too, and a ring
# of parties who owe each other and hold nothing clears itself.
#
# A party takes obligations from the front of its line and never one before the
# one in front of it, so all a round decides for a party is how far down its
# line it gets. The whole answer is one depth per party, capped by what the
# round is allowed to reach.
#
# Write out(d) for what a party pays at depth d and in(d) for what reaches it.
# A depth vector stands up when, for every party,
#
#     hold + in(d) - out(d) >= 0
#
# and the round has to leave nothing on the table, so the answer is the largest
# such vector. There is exactly one. If two vectors both stand up, so does the
# one taking the larger depth for each party: for any party the larger vector
# pays what one of the two paid, and it receives at least what that one
# received, because raising anybody's depth never lowers what anybody gets. So
# the vectors that stand up are closed under taking the larger of two, the set
# is finite and not empty, and it has a single top element.
#
# Start at the cap and come down. Each step gives every party everything the
# current vector sends it and asks how far down its own line that carries it.
# That answer is never above where the party already was, so the vector only
# falls, and it stops. Where it stops every party is paying exactly as far as
# its money reaches, which is the requirement; and nothing that stands up was
# cut away, because a step only ever drops an obligation the party could not
# fund even with everything the current vector hands it.


def draw(b, cap):
    who = b.who()
    ln = {n: b.line(n) for n in who}
    d = {n: cap[n] for n in who}
    while True:
        inc = {n: 0 for n in who}
        for n in who:
            for o in ln[n][: d[n]]:
                inc[o.pe] += o.am
        nd = {}
        for n in who:
            av = b.hold(n) + inc[n]
            s = 0
            k = 0
            for o in ln[n][: d[n]]:
                if s + o.am > av:
                    break
                s += o.am
                k += 1
            nd[n] = k
        if nd == d:
            return d
        d = nd
