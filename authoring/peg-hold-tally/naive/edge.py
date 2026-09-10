def shed(a, p, t):
    a.t = t
    fresh = []
    for b in a.pset.pop(p, ()):
        a.pc[b] -= 1
        if a.pc[b] == 0 and a.vc[b] == 0 and b not in a.stop:
            a.stop[b] = t
            fresh.append(b)
    fresh.sort()
    a.q.extend(fresh)
