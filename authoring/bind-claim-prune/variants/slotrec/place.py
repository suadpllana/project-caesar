def run(st):
    out = {}
    for nm, s in st.names.slot.items():
        if not s.spare or s.firm or s.soft:
            continue
        best = None
        for size, order, who in s.spare:
            if best is None or size > best[0] or (size == best[0] and order < best[1]):
                best = (size, order, who)
        out[nm] = (best[2], best[0])
    return out
