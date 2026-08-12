from tok.core import END, V, ask

D = 6
M = 1000003


def _mix(a, b):
    x = (a * 1103515245 + b * 12345 + 7) % 2147483647
    x = (x * 48271) % 2147483647
    return x


W = [[_mix(i * 31 + j, 17) % 97 + 1 for j in range(D)] for i in range(D)]
EM = [[_mix(t * 13 + j, t + 5) % 211 for j in range(D)] for t in range(V)]
HD = [[_mix(t * 7 + j, t * 3 + 11) % 173 for j in range(D)] for t in range(V)]

STOP_PULL = M // 60


class Net:
    def __init__(self):
        self.n_fwd = 0

    def start(self):
        return (1, 2, 3, 4, 5, 6)

    def step(self, h, t):
        self.n_fwd += 1
        rsp = ask({"op": "fwd", "h": [int(x) for x in h], "t": int(t)})
        if rsp is not None:
            return tuple(int(x) for x in rsp["h"])
        e = EM[t]
        out = []
        for i in range(D):
            s = e[i]
            row = W[i]
            for j in range(D):
                s += row[j] * h[j]
            out.append(s % M)
        return tuple(out)

    def pick(self, h, salt, k):
        rsp = ask({"op": "pick", "h": [int(x) for x in h], "salt": int(salt),
                   "k": int(k)})
        if rsp is not None:
            return int(rsp["t"])
        best = -1
        got = 0
        for t in range(V):
            r = HD[t]
            s = salt * (t + 1) + k * 2654435761
            for j in range(D):
                s += r[j] * h[j]
            s %= M
            if t == END:
                s += k * STOP_PULL
            if s > best:
                best = s
                got = t
        return got
