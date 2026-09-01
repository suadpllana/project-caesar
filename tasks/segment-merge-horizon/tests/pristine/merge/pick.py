def choose(st, tier):
    n = len(st.segs)
    if n < 2:
        return []
    w = tier if tier <= n else n
    if w < 2:
        return []
    return list(range(0, w))
