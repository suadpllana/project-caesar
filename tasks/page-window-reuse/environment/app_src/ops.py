from kv import pool, store, live, turn


def tokens(spec):
    if spec == "-":
        return []
    out = []
    for part in spec.split(","):
        cnt, _, val = part.partition(":")
        out.extend([int(val)] * int(cnt))
    return out


def new(kv, name, prompt, out):
    rq = store.Rq(name, kv.tick(), prompt, out)
    kv.rq[name] = rq
    kv.wait.append(name)


def ex(kv, f):
    op = f[0]
    if op == "pool":
        kv.n = int(f[1])
        kv.w = int(f[2])
        kv.a = int(f[3])
        kv.s = int(f[4])
        kv.b = int(f[5])
        pool.start(kv)
    elif op == "ask":
        new(kv, f[1], tokens(f[2]), tokens(f[3]))
    elif op == "bulk":
        base = f[1]
        pre = tokens(f[3])
        tail = int(f[4])
        made = int(f[5])
        for i in range(int(f[2])):
            new(kv, base + str(i), pre + [1000 + i] * tail, [2000 + i] * made)
    elif op == "step":
        turn.step(kv)
    elif op == "stop":
        turn.kill(kv, f[1])
    elif op == "at":
        rq = kv.rq.get(f[1])
        i = int(f[2])
        pid = live.holds(kv, rq, i) if rq is not None else 0
        kv.say("at", f[1], i, pid if pid else "none")
