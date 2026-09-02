def give(b, cap, plan):
    out = []
    for n in b.who():
        q = b.line(n)
        for k in range(plan.get(n, 0), cap[n]):
            out.append(q[k].i)
    out.sort(key=lambda i: b.look(i).sq)
    return out
