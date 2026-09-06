import collections


def cycle(h):
    idx = {}
    for k, v in h.pr:
        idx.setdefault(k, []).append(v)

    col = {}

    def paint(seed, shade):
        q = collections.deque(seed)
        while q:
            i = q.popleft()
            if i not in h.ob or col.get(i):
                continue
            col[i] = shade
            for v in h.ob[i].fl.values():
                if v is not None and not col.get(v):
                    q.append(v)
            for v in idx.get(i, ()):
                if not col.get(v):
                    q.append(v)

    paint([v for f in h.fr for v in f.values() if v is not None], 1)

    due = [i for i in sorted(h.ob)
           if col.get(i) != 1 and h.ob[i].fz is not None
           and i not in h.rn and i not in h.qu]

    paint(list(h.qu) + due, 2)

    cl = [n for n in sorted(h.wk) if not h.wk[n].c and col.get(h.wk[n].t) != 1]
    rl = [i for i in sorted(h.ob) if not col.get(i)]
    return cl, due, rl
