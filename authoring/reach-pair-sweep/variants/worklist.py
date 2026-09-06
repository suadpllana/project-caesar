def cycle(h):
    byk = {}
    for k, v in h.pr:
        byk.setdefault(k, []).append(v)

    col = {}

    def paint(seed, c):
        stack = list(seed)
        while stack:
            i = stack.pop()
            if i not in h.ob or col.get(i):
                continue
            col[i] = c
            for v in h.ob[i].fl.values():
                if v is not None and v in h.ob and not col.get(v):
                    stack.append(v)
            for v in byk.get(i, ()):
                if v in h.ob and not col.get(v):
                    stack.append(v)

    start = []
    for f in h.fr:
        for v in f.values():
            if v is not None:
                start.append(v)
    paint(start, 1)

    qd = [i for i in sorted(h.ob)
          if col.get(i) != 1 and h.ob[i].fz is not None
          and i not in h.rn and i not in h.qu]

    paint(list(h.qu) + qd, 2)

    cl = [n for n, w in h.wk.items() if not w.c and col.get(w.t) != 1]
    rl = [i for i in sorted(h.ob) if not col.get(i)]
    return cl, qd, rl
