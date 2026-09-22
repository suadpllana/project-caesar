def runs(items, lo, hi):
    gaps = []
    at = lo
    for st in items:
        if st.hi < lo or st.lo > hi:
            continue
        if st.lo > at:
            gaps.append((at, st.lo - 1))
        if st.hi + 1 > at:
            at = st.hi + 1
        if at > hi:
            break
    if at <= hi:
        gaps.append((at, hi))
    return gaps
