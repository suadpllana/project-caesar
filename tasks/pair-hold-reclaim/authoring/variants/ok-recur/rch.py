import sys


def reach(st, seeds):
    sys.setrecursionlimit(10000)
    live = set()

    def walk(i):
        if not st.has(i) or i in live:
            return
        live.add(i)
        for j in st.outs(i):
            walk(j)

    for i in seeds:
        walk(i)
    while True:
        grew = False
        for k, v in st.prs():
            if k in live and v not in live:
                walk(v)
                grew = True
        for a, b, v in st.bos():
            if a in live and b in live and v not in live:
                walk(v)
                grew = True
        if not grew:
            return live
