from model.arch import D, V, L, M


def dot(a, b):
    s = 0
    for i in range(len(a)):
        s += a[i] * b[i]
    return s % M


def matvec(h, W):
    c = len(W[0])
    out = [0] * c
    for i in range(len(h)):
        hi = h[i]
        if hi:
            row = W[i]
            for j in range(c):
                out[j] += hi * row[j]
    for j in range(c):
        out[j] %= M
    return out


class Backend:
    def __init__(self):
        self.n_pos = 0

    def proj(self, w, h, i):
        k = tuple(matvec(h, w["l" + str(i) + ".wk"]))
        v = tuple(matvec(h, w["l" + str(i) + ".wv"]))
        return (k, v)

    def forward(self, w, tok, ctx):
        self.n_pos += 1
        h = list(w["emb"][tok])
        new = []
        for i in range(L):
            kv = self.proj(w, h, i)
            new.append(kv)
            q = matvec(h, w["l" + str(i) + ".wq"])
            acc = [0] * D
            for pair in ctx[i]:
                s = dot(q, pair[0])
                pv = pair[1]
                for j in range(D):
                    acc[j] += s * pv[j]
            s = dot(q, kv[0])
            for j in range(D):
                acc[j] = (acc[j] + s * kv[1][j]) % M
            o = matvec(acc, w["l" + str(i) + ".wo"])
            for j in range(D):
                h[j] = (h[j] + o[j]) % M
            m1 = matvec(h, w["l" + str(i) + ".w1"])
            for j in range(D):
                m1[j] = (m1[j] * m1[j]) % M
            m2 = matvec(m1, w["l" + str(i) + ".w2"])
            for j in range(D):
                h[j] = (h[j] + m2[j]) % M
        g = w["gsc"][0]
        for j in range(D):
            h[j] = (h[j] * g[j]) % M
        return new, matvec(h, w["head"])


def pick(logits, salt, step):
    best = -1
    out = 0
    for j in range(V):
        s = (logits[j] + salt * (j + 1) + step * 2654435761) % M
        if s > best:
            best = s
            out = j
    return out
