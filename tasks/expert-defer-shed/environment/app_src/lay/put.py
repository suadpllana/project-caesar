from lay import back, buf, cap, gate, tally, trim


def _ids(mbs):
    base = 0
    out = []
    for mb in mbs:
        out.append(list(range(base, base + len(mb))))
        base += len(mb)
    return out


def step(cfg, mbs, out):
    weights = []
    for mb in mbs:
        weights.extend(mb)
    n = len(weights)
    order = [gate.rank(s) for s in weights]

    wanted = 0
    for token in range(n):
        wanted += len(gate.want(order[token], weights[token], cfg.w))
    c = cap.slots(cfg, wanted)
    z = cap.budget(cfg, c)
    out.line("cap %d %d" % (c, z))

    st = back.Track(n)
    bufs = buf.Bufs(cfg.ex, c)

    for group in _ids(mbs):
        for token in group + st.take():
            wl = gate.want(order[token], weights[token], cfg.w)
            st.wl[token] = wl
            held = []
            for e in wl:
                if bufs.room(e):
                    held.append((e, bufs.fill(e, token)))
            st.place[token] = held
            if not held and wl:
                st.defer(token, out)

    trim.shed(cfg, weights, bufs, st, z)
    tally.report(cfg, weights, bufs, st, out, n)
