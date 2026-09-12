def run(st):
    """Names nothing gives, that some unit spared.

    Size is the largest spared, and the unit is the first in load order that spared it at that
    size, which is why the load order of every unit is carried rather than the declaration
    order. A give of either strength cancels the whole name, however late it arrived.
    """
    out = {}
    for nm, row in st.names.spare.items():
        if st.names.firm.get(nm) or st.names.soft.get(nm):
            continue
        best = None
        for size, order, who in row:
            if best is None:
                best = (size, order, who)
        out[nm] = (best[2], best[0])
    return out
