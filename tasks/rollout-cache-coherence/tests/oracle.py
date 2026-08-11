"""A sealed, self-contained generator used to prove the ground-truth token streams.

It shares no code with the tree the agent works in: the arithmetic, the parameter
construction and the sampling rule are written out again here, and generation recomputes
the whole context for every token with no cache, no blocks and no scheduler.  What it can
prove is therefore exactly the property that matters: that each expected token stream in
gt.json is what this model emits for that prompt under one single parameter state, which
is what "the sample came from one policy, with the cache making no difference to the
result" means.

Parameter snapshots are rebuilt here from the scenario op list, so the expected streams
are anchored to the scenario definition rather than to anything the engine reported.
"""

D = 8
V = 64
L = 4
M = 2147483647
EOS = 0
MODS = ("wq", "wk", "wv", "wo", "w1", "w2")
TIES = {"l3.wq": "l1.wq"}


def pids():
    out = ["emb"]
    for i in range(L):
        for m in MODS:
            out.append("l%d.%s" % (i, m))
    return out + ["gsc", "head"]


def store_of(p):
    return TIES.get(p, p)


def dims(p):
    if p == "emb":
        return (V, D)
    if p == "gsc":
        return (1, D)
    if p == "head":
        return (D, V)
    return (D, D)


def mix64(x):
    x &= 0xFFFFFFFFFFFFFFFF
    x = ((x ^ (x >> 33)) * 0xFF51AFD7ED558CCD) & 0xFFFFFFFFFFFFFFFF
    x = ((x ^ (x >> 33)) * 0xC4CEB9FE1A85EC53) & 0xFFFFFFFFFFFFFFFF
    return x ^ (x >> 33)


def tag(text, salt=0):
    h = mix64(salt ^ 0x243F6A8885A308D3)
    for ch in str(text):
        h = mix64(h ^ ord(ch))
    return h


def mat(pid, seed):
    r, c = dims(pid)
    s = mix64(tag(pid) ^ mix64(seed))
    rows = []
    for _ in range(r):
        row = []
        for _ in range(c):
            s = mix64(s + 0x9E3779B97F4A7C15)
            row.append(s % M)
        rows.append(tuple(row))
    return tuple(rows)


def weights(seeds, deltas):
    w = {}
    for p in pids():
        b = mat(store_of(p), seeds[store_of(p)])
        if p in deltas:
            d = mat(p, deltas[p])
            b = tuple(tuple((b[i][j] + d[i][j]) % M for j in range(len(b[0])))
                      for i in range(len(b)))
        w[p] = b
    return w


def matvec(h, W):
    c = len(W[0])
    out = [0] * c
    for i in range(len(h)):
        if h[i]:
            row = W[i]
            for j in range(c):
                out[j] += h[i] * row[j]
    return [x % M for x in out]


def dot(a, b):
    s = 0
    for i in range(len(a)):
        s += a[i] * b[i]
    return s % M


def run_prefix(w, toks):
    """Recompute every position from scratch and return the logits of the last one."""
    ctx = [[] for _ in range(L)]
    logits = None
    for t in toks:
        h = list(w["emb"][t])
        for i in range(L):
            k = tuple(matvec(h, w["l%d.wk" % i]))
            v = tuple(matvec(h, w["l%d.wv" % i]))
            q = matvec(h, w["l%d.wq" % i])
            acc = [0] * D
            for (kk, vv) in ctx[i]:
                s = dot(q, kk)
                for j in range(D):
                    acc[j] += s * vv[j]
            s = dot(q, k)
            for j in range(D):
                acc[j] = (acc[j] + s * v[j]) % M
            ctx[i].append((k, v))
            o = matvec(acc, w["l%d.wo" % i])
            for j in range(D):
                h[j] = (h[j] + o[j]) % M
            m1 = matvec(h, w["l%d.w1" % i])
            for j in range(D):
                m1[j] = (m1[j] * m1[j]) % M
            m2 = matvec(m1, w["l%d.w2" % i])
            for j in range(D):
                h[j] = (h[j] + m2[j]) % M
        g = w["gsc"][0]
        for j in range(D):
            h[j] = (h[j] * g[j]) % M
        logits = matvec(h, w["head"])
    return logits


def sample(logits, salt, step):
    best = -1
    out = 0
    for j in range(V):
        s = (logits[j] + salt * (j + 1) + step * 2654435761) % M
        if s > best:
            best = s
            out = j
    return out


def generate(seeds, deltas, rid, prompt, max_new):
    w = weights(seeds, deltas)
    salt = tag(rid, 7717) % M
    toks = list(prompt)
    gen = []
    for step in range(max_new):
        nt = sample(run_prefix(w, toks), salt, step)
        gen.append(nt)
        toks.append(nt)
        if nt == EOS:
            break
    return gen


def snapshots(base_seeds, base_adapters, ops):
    """Parameter states as the op list walks: one entry before any op, one after each sync."""
    seeds = dict(base_seeds)
    ad = {k: dict(v) for k, v in base_adapters.items()}
    out = [(dict(seeds), {k: dict(v) for k, v in ad.items()})]
    for op in ops:
        if op["op"] != "sync":
            continue
        for who, pid, sd in op["ups"]:
            if who is None:
                seeds[store_of(pid)] = sd
            else:
                ad.setdefault(who, {})[pid] = sd
        out.append((dict(seeds), {k: dict(v) for k, v in ad.items()}))
    return out
