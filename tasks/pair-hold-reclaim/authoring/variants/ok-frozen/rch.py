"""What is still in reach, computed as a least fixed point.

Three kinds of edge lead out of a cell and only the first behaves like an edge.

A link is unconditional: if the cell holding it is in reach, so is the cell it points at,
and a plain worklist closure settles that in one traversal.

An entry is conditional. A one-key entry puts its value in reach for as long as its key
is in reach; a two-key entry does so only while both of its keys are. Neither is an edge
the closure can walk, because the question they ask -- is the key in reach? -- is
answered by the very set being built. Sweeping the tables once, adding the values whose
keys are already marked, is not enough: a value that has just been marked can lead to
another entry's key, which puts that entry's value in reach, which can lead to a third,
and a two-key entry can sit unfired through several sweeps waiting for its second key.
The set has only settled when a full sweep of both tables adds nothing, so the sweeps and
the closure alternate until neither moves.

Taking the least fixed point is also what gets the self-holding case right. An entry
whose key is reachable only from its own value is never fired at all: nothing outside
puts the key in reach, so the value is never added on its account, so the key never
becomes reachable. A reading that treats an entry as an ordinary edge keeps that group
alive forever.
"""


def reach(st, seeds):
    live = set()
    stack = []
    for i in seeds:
        if st.has(i) and i not in live:
            live.add(i)
            stack.append(i)
    prs = st.prs()
    bos = st.bos()
    while True:
        while stack:
            i = stack.pop()
            for j in st.outs(i):
                if j not in live:
                    live.add(j)
                    stack.append(j)
        grew = False
        for k, v in prs:
            if k in live and v not in live:
                live.add(v)
                stack.append(v)
                grew = True
        for a, b, v in bos:
            if a in live and b in live and v not in live:
                live.add(v)
                stack.append(v)
                grew = True
        if not grew:
            return live
