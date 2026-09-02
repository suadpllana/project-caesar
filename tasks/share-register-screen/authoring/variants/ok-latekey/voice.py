BLOC = "~~"


def hands(st, cid, on):
    out = {}
    for who, w in st.stakes(cid):
        v = st.voter(who)
        if v == cid:
            continue
        k = BLOC if v in on else v
        out[k] = out.get(k, 0) + w
    return out
