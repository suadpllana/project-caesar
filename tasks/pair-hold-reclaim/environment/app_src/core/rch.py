def reach(st, seeds):
    live = set()
    stack = []
    for i in seeds:
        if st.has(i) and i not in live:
            live.add(i)
            stack.append(i)
    while stack:
        i = stack.pop()
        for j in st.outs(i):
            if j not in live:
                live.add(j)
                stack.append(j)
    for k, v in st.prs():
        if k in live and v not in live:
            live.add(v)
            stack.append(v)
    for a, b, v in st.bos():
        if a in live and b in live and v not in live:
            live.add(v)
            stack.append(v)
    while stack:
        i = stack.pop()
        for j in st.outs(i):
            if j not in live:
                live.add(j)
                stack.append(j)
    return live
