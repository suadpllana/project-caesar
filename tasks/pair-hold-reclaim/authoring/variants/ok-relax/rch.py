def reach(st, seeds):
    live = set(i for i in seeds if st.has(i))
    prs = st.prs()
    bos = st.bos()
    moving = True
    while moving:
        moving = False
        for i in sorted(live):
            for j in st.outs(i):
                if j not in live:
                    live.add(j)
                    moving = True
        for k, v in prs:
            if k in live and v not in live:
                live.add(v)
                moving = True
        for a, b, v in bos:
            if a in live and b in live and v not in live:
                live.add(v)
                moving = True
    return live
