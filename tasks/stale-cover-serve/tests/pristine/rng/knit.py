def rows(items, lo, hi, at):
    out = []
    for st in items:
        if st.hi < lo or st.lo > hi:
            continue
        for k, v in st.rows:
            if lo <= k <= hi:
                out.append((k, v))
    return out
