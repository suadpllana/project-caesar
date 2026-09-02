# The vote map a company's meeting sees, under the determination reached so far.
#
# Everything on the list is one voter. The list is a single set of hands that moves
# together, so the meeting cannot tell its members apart, and the seats it takes are the
# seats one holder of that size takes -- never the sum of the seats its members would
# take standing apart, which is a smaller number whenever the board is shared out by
# running averages.
#
# The collapse is keyed on the party that actually casts the vote, not on the party the
# register records as holding the shares. A nominee votes what its principal tells it to
# vote, so a nominee on the list holding for an outsider brings nothing, and an outsider
# holding for a party on the list brings everything.
#
# The same resolution is what silences a company's own stock. The site drops a holding
# recorded against the company whose meeting it is, which covers the plain case and
# leaves this one: shares standing in some other name but held for the company are the
# company's shares, and a company does not help decide its own affairs. Skipping them has
# to happen after the principal is resolved rather than before, and it matters most where
# the company is on the list, because folding its own stock into the list's hand is
# exactly the vote the rule exists to remove.
BLOC = "+"


def hands(st, cid, on):
    out = {}
    for who, w in st.stakes(cid):
        v = st.voter(who)
        if v == cid:
            continue
        k = BLOC if v in on else v
        out[k] = out.get(k, 0) + w
    return out
